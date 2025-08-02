"""
Schemachange templater for SQLFluff.

This templater integrates with the schemachange database change management tool,
allowing SQLFluff to lint SQL files that use schemachange's Jinja templating features.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Iterator, Tuple, Optional, Dict, Any, List, Union

from jinja2 import Environment, FileSystemLoader, Template, TemplateError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment

from sqlfluff.core.templaters.base import TemplatedFile, RawTemplater
from sqlfluff.core.templaters.jinja import JinjaTemplater
from sqlfluff.core.errors import SQLTemplaterError

logger = logging.getLogger(__name__)


class SchemachangeTemplater(RawTemplater):
    """
    A templater that processes schemachange Jinja templates.
    
    This templater is designed to work with schemachange's templating system,
    supporting:
    - Jinja2 templating with variables from schemachange-config.yml
    - Macro templates from modules folder
    - Environment variable substitution
    - Secret filtering and handling
    - Complex nested variable structures
    """
    
    name = "schemachange"
    sequential_fail_limit = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._environment = None
        self._config_vars = {}
        self._modules_path = None
        self._root_path = None
        
    def config_pairs(self):
        """Return configuration options for this templater."""
        return [
            ("schemachange_config", None),
            ("config_file_path", None),
            ("modules_folder", None),
            ("root_folder", None),
            ("vars", {}),
            ("apply_dbt_builtins", False),
            ("library_path", None),
            ("loader_search_path", None),
        ]

    def _load_schemachange_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load schemachange configuration from YAML file."""
        if config_path is None:
            # Look for schemachange-config.yml in current directory
            candidates = [
                "schemachange-config.yml",
                "schemachange-config.yaml",
                ".schemachange/config.yml",
                ".schemachange/config.yaml"
            ]
            
            for candidate in candidates:
                if os.path.exists(candidate):
                    config_path = candidate
                    break
            
            if config_path is None:
                logger.debug("No schemachange config file found")
                return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                # First pass: load raw YAML for env_var processing
                raw_content = f.read()
                
                # Create a basic Jinja environment for config file processing
                config_env = Environment()
                config_env.globals['env_var'] = self._env_var_function
                
                # Render the config file with environment variables
                rendered_content = config_env.from_string(raw_content).render()
                
                # Parse the rendered YAML
                config = yaml.safe_load(rendered_content)
                
                logger.debug(f"Loaded schemachange config from {config_path}")
                return config or {}
                
        except (FileNotFoundError, yaml.YAMLError, TemplateError) as e:
            logger.warning(f"Could not load schemachange config from {config_path}: {e}")
            return {}

    def _env_var_function(self, var_name: str, default: Optional[str] = None) -> str:
        """Custom function for accessing environment variables in config files."""
        value = os.environ.get(var_name)
        if value is None:
            if default is not None:
                return default
            else:
                raise ValueError(f"Environment variable '{var_name}' not found and no default provided")
        return value

    def _extract_variables(self, config: Dict[str, Any], cli_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and merge variables from config and CLI arguments."""
        # Start with config vars
        variables = config.get('vars', {}).copy()
        
        # Merge with CLI vars (CLI takes precedence)
        variables.update(cli_vars)
        
        return variables

    def _is_secret(self, key_path: List[str], value: Any) -> bool:
        """Determine if a variable should be treated as a secret."""
        # Check if any part of the key path contains 'secret'
        for key in key_path:
            if 'secret' in key.lower():
                return True
        
        # Check if the variable is under a 'secrets' key
        if len(key_path) > 1:
            for i, key in enumerate(key_path[:-1]):
                if key.lower() == 'secrets':
                    return True
        
        return False

    def _filter_secrets(self, variables: Dict[str, Any], path: List[str] = None) -> Dict[str, Any]:
        """Filter out secret values for logging purposes."""
        if path is None:
            path = []
            
        filtered = {}
        for key, value in variables.items():
            current_path = path + [key]
            
            if isinstance(value, dict):
                filtered[key] = self._filter_secrets(value, current_path)
            else:
                if self._is_secret(current_path, value):
                    filtered[key] = "***REDACTED***"
                else:
                    filtered[key] = value
        
        return filtered

    def _setup_jinja_environment(self, config: Dict[str, Any], variables: Dict[str, Any]) -> Environment:
        """Set up the Jinja2 environment with all necessary configurations."""
        # Determine search paths
        search_paths = []
        
        # Add modules folder if specified
        modules_folder = config.get('modules-folder') or config.get('modules_folder')
        if modules_folder:
            search_paths.append(modules_folder)
            self._modules_path = modules_folder
        
        # Add root folder
        root_folder = config.get('root-folder') or config.get('root_folder', '.')
        search_paths.append(root_folder)
        self._root_path = root_folder
        
        # Add any additional loader search paths
        loader_search_path = config.get('loader_search_path', '')
        if loader_search_path:
            if isinstance(loader_search_path, str):
                search_paths.extend(p.strip() for p in loader_search_path.split(',') if p.strip())
            elif isinstance(loader_search_path, list):
                search_paths.extend(loader_search_path)
        
        # Create the environment with sandbox for security
        env = SandboxedEnvironment(
            loader=FileSystemLoader(search_paths, followlinks=False),
            # Disable autoescape since we're working with SQL, not HTML
            autoescape=False,
            # Keep trailing newline for consistency
            keep_trailing_newline=True,
            # Enable line statements and comments for debugging
            line_statement_prefix=None,
            line_comment_prefix=None,
        )
        
        # Add all variables to the global context
        env.globals.update(variables)
        
        # Add utility functions
        env.globals['env_var'] = self._env_var_function
        
        # Add dbt-style builtins if requested
        if config.get('apply_dbt_builtins', False):
            self._add_dbt_builtins(env)
        
        return env

    def _add_dbt_builtins(self, env: Environment):
        """Add dbt-style builtin functions to the Jinja environment."""
        def ref(model_name: str) -> str:
            """Mock dbt ref() function."""
            return model_name
        
        def source(source_name: str, table_name: str) -> str:
            """Mock dbt source() function."""
            return f"{source_name}.{table_name}"
        
        def var(variable_name: str, default_value: Any = None) -> Any:
            """Mock dbt var() function."""
            return env.globals.get(variable_name, default_value)
        
        def config(**kwargs) -> str:
            """Mock dbt config() function."""
            return ""
        
        def is_incremental() -> bool:
            """Mock dbt is_incremental() function."""
            return False

        # Add functions to the environment
        env.globals.update({
            'ref': ref,
            'source': source,
            'var': var,
            'config': config,
            'is_incremental': is_incremental,
        })

    def template(self, fname, in_str, config, **kwargs):
        """
        Template the given string using schemachange-compatible Jinja templating.
        
        Args:
            fname: The filename being templated
            in_str: The input SQL string
            config: SQLFluff configuration object
            **kwargs: Additional keyword arguments
            
        Returns:
            TemplatedFile: The templated result
        """
        try:
            # Load schemachange configuration
            schemachange_config_path = config.get_section(
                (self.templater_selector, self.name, "config_file_path")
            )
            schemachange_config = self._load_schemachange_config(schemachange_config_path)
            
            # Get CLI variables from SQLFluff config
            cli_vars = config.get_section((self.templater_selector, self.name, "vars")) or {}
            
            # Extract and merge all variables
            variables = self._extract_variables(schemachange_config, cli_vars)
            
            # Log variables (filtered for secrets)
            filtered_vars = self._filter_secrets(variables)
            logger.debug(f"Using variables: {json.dumps(filtered_vars, indent=2)}")
            
            # Set up Jinja environment
            env = self._setup_jinja_environment(schemachange_config, variables)
            self._environment = env
            
            # Render the template
            template = env.from_string(in_str)
            rendered_sql = template.render()
            
            # Create the templated file object
            templated_file = TemplatedFile(
                source_str=in_str,
                templated_str=rendered_sql,
                fname=fname,
                sliced_file=[(
                    slice(0, len(in_str)),  # Source slice
                    slice(0, len(rendered_sql))  # Templated slice
                )],
            )
            
            return templated_file
            
        except UndefinedError as e:
            # Handle undefined variables gracefully
            variable_name = str(e).split("'")[1] if "'" in str(e) else "unknown"
            raise SQLTemplaterError(
                f"Undefined variable '{variable_name}' in template. "
                f"Please define it in your schemachange-config.yml vars section "
                f"or pass it via --vars command line argument.",
                line_no=None,
                line_pos=None,
            )
            
        except TemplateError as e:
            raise SQLTemplaterError(
                f"Jinja templating error: {str(e)}",
                line_no=getattr(e, 'lineno', None),
                line_pos=None,
            )
            
        except Exception as e:
            raise SQLTemplaterError(
                f"Unexpected error in schemachange templater: {str(e)}",
                line_no=None,
                line_pos=None,
            )

    def slice_file(self, templated_file, config, **kwargs):
        """
        Slice the templated file to map between raw and templated positions.
        
        For now, we use a simple approach that maps the entire file.
        A more sophisticated implementation would track Jinja blocks and variables.
        """
        # For simplicity, we'll use the parent class implementation
        # which creates a basic slice mapping
        return super().slice_file(templated_file, config, **kwargs)