"""
Schemachange-compatible templater for SQLFluff.

This templater provides standalone schemachange-compatible functionality by
extending SQLFluff's JinjaTemplater (no schemachange dependency required):
- Reads variables and macros from schemachange-config.yml files
- Provides schemachange-compatible env_var() function
- Supports schemachange-style macro loading from modules folder
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from jinja2 import FileSystemLoader, Environment
from sqlfluff.core.templaters.jinja import JinjaTemplater
from sqlfluff.core.errors import SQLTemplaterError

logger = logging.getLogger(__name__)


class SchemachangeTemplater(JinjaTemplater):
    """
    A SQLFluff templater that extends JinjaTemplater with schemachange functionality.
    
    This templater leverages SQLFluff's sophisticated JinjaTemplater while adding
    schemachange-specific features:
    - Reads variables and macros from schemachange-config.yml files
    - Supports schemachange's modules folder for macro loading  
    - Adds env_var() function for environment variable access
    - Maintains full compatibility with schemachange templating behavior
    """
    
    name = "schemachange"
    
    def config_pairs(self):
        """Return configuration options for this templater."""
        return super().config_pairs() + [
            ("config_folder", '.'),
            ("config_file", 'schemachange-config.yml'),
            ("root_folder", '.'),
            ("modules_folder", '.'),
            ("vars", {}),
        ]
    
    def _load_schemachange_config(self, config_folder: str, config_file: str = 'schemachange-config.yml') -> Dict[str, Any]:
        """Load schemachange configuration from YAML file."""
        config_path = Path(config_folder) / config_file
        
        if not config_path.exists():
            logger.debug(f"Schemachange config file not found at {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                schema_config = yaml.safe_load(f) or {}
            logger.debug(f"Loaded schemachange config from {config_path}")
            return schema_config
        except Exception as e:
            logger.warning(f"Failed to load schemachange config from {config_path}: {e}")
            return {}
    
    def _get_context_from_config(self, config, schemachange_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build Jinja context combining SQLFluff config and schemachange config."""
        context = {}
        
        # Start with parent JinjaTemplater context
        try:
            if config:
                parent_context = super()._get_context_from_config(config)
                if parent_context:
                    context.update(parent_context)
        except Exception as e:
            logger.debug(f"No parent context available: {e}")
        
        # Add schemachange variables
        if 'vars' in schemachange_config:
            schema_vars = schemachange_config['vars']
            if isinstance(schema_vars, dict):
                context.update(schema_vars)
        
        # Add templater-specific vars from SQLFluff config
        templater_config = {}
        if config:
            try:
                templater_config = config.get_section(("templater", self.name)) or {}
            except Exception as e:
                logger.debug(f"Could not get templater config for context: {e}")
        
        if 'vars' in templater_config:
            template_vars = templater_config['vars']
            if isinstance(template_vars, dict):
                context.update(template_vars)
            elif isinstance(template_vars, str):
                # Handle string representation of JSON
                try:
                    parsed_vars = json.loads(template_vars)
                    if isinstance(parsed_vars, dict):
                        context.update(parsed_vars)
                except json.JSONDecodeError as e:
                    logger.warning(f"Could not parse vars as JSON: {e}")
            else:
                logger.warning(f"Unexpected vars type: {type(template_vars)}")
        
        logger.debug(f"Built context with {len(context)} variables")
        return context
    
    def _get_env_var(self, var_name: str, default_value: str = '') -> str:
        """Schemachange-compatible env_var function.  (not imported from schemachange)"""
        return os.environ.get(var_name, default_value)
    
    def _get_jinja_env(self, config=None, **kwargs):
        """Override to add schemachange-specific Jinja environment setup."""
        # Get the parent Jinja environment
        env = super()._get_jinja_env(config=config, **kwargs)
        
        # Get templater configuration with proper null checking
        templater_config = {}
        if config:
            try:
                templater_config = config.get_section(("templater", self.name)) or {}
            except Exception as e:
                logger.debug(f"Could not get templater config section: {e}")
                templater_config = {}
        
        config_folder = templater_config.get('config_folder', '.')
        config_file = templater_config.get('config_file', 'schemachange-config.yml')
        
        # Load schemachange configuration
        schemachange_config = self._load_schemachange_config(config_folder, config_file)
        
        # Set up macro loading from modules folder
        modules_folder = templater_config.get('modules_folder') or schemachange_config.get('modules_folder')
        if modules_folder and Path(modules_folder).exists():
            # Set up proper FileSystemLoader for templates
            search_paths = ['.', modules_folder]  # Current directory and modules folder
            
            current_loader = env.loader
            if hasattr(current_loader, 'searchpath'):
                # If we already have a filesystem loader, add to its search path
                for path in search_paths:
                    if path not in current_loader.searchpath:
                        current_loader.searchpath.append(path)
            else:
                # Create a new FileSystemLoader
                env.loader = FileSystemLoader(search_paths)
            
            logger.debug(f"Added modules folder to Jinja loader: {modules_folder}")
        else:
            # Even if no modules folder, ensure we have a basic loader for current directory
            if not env.loader or not hasattr(env.loader, 'searchpath'):
                env.loader = FileSystemLoader(['.'])
                logger.debug("Set up basic FileSystemLoader for current directory")
        
        # Add schemachange-specific functions to Jinja environment
        # if schemachange adds more functions we may need to add a dependancy to track future changes.
        env.globals['env_var'] = self._get_env_var
        
        # Add context variables to environment globals
        context = self._get_context_from_config(config, schemachange_config)
        env.globals.update(context)
        
        logger.debug(f"Configured Jinja environment with {len(env.globals)} globals")
        return env