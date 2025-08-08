"""Schemachange-compatible templater for SQLFluff.

This templater provides standalone schemachange-compatible functionality by
extending SQLFluff's JinjaTemplater (no schemachange dependency required):
- Reads variables and macros from schemachange-config.yml files
- Provides schemachange-compatible env_var() function
- Supports schemachange-style macro loading from modules folder
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader
from sqlfluff.core.templaters.jinja import JinjaTemplater

logger = logging.getLogger(__name__)


class SchemachangeTemplater(JinjaTemplater):
    """A SQLFluff templater that extends JinjaTemplater with schemachange functionality.

    This templater leverages SQLFluff's sophisticated JinjaTemplater while adding
    schemachange-specific features:
    - Reads variables and macros from schemachange-config.yml files
    - Supports schemachange's modules folder for macro loading
    - Adds env_var() function for environment variable access
    - Maintains full compatibility with schemachange templating behavior
    """

    name = "schemachange"

    def config_pairs(self):
        """Return configuration options and defaults for this templater."""
        return super().config_pairs() + [
            ("config_folder", "."),
            ("config_file", "schemachange-config.yml"),
        ]

    def _load_schemachange_config(
        self, config_folder: str, config_file: str = "schemachange-config.yml"
    ) -> Dict[str, Any]:
        """Load schemachange configuration from YAML file."""
        config_path = Path(config_folder) / config_file

        if not config_path.exists():
            logger.debug(f"Schemachange config file not found at {config_path}")
            return {}

        try:
            with open(config_path, "r") as f:
                raw_text = f.read()
            jinja_env = Environment()
            jinja_env.globals["env_var"] = SchemachangeTemplater._get_env_var
            rendered_text = jinja_env.from_string(raw_text).render()
            schema_config = yaml.safe_load(rendered_text) or {}
            logger.debug(
                f"Loaded schemachange config from {config_path} (Jinja rendered)"
            )
            return schema_config
        except Exception as e:
            logger.warning(
                f"Failed to load schemachange config from {config_path}: {e}"
            )
            return {}

    def _get_context_from_config(
        self, config, schemachange_config: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        if "vars" in schemachange_config:
            schema_vars = schemachange_config["vars"]
            if isinstance(schema_vars, dict):
                context.update(schema_vars)

        logger.debug(f"Built context with {len(context)} variables")
        return context

    @staticmethod
    def _get_env_var(env_var: str, default: Optional[str] = None) -> str:
        """Schemachange-compatible env_var function."""
        result = default
        if env_var in os.environ:
            result = os.environ[env_var]

        if result is None:
            raise ValueError(
                f"Could not find environmental variable {env_var} "
                + "and no default value was provided"
            )

        return result

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

        config_folder = templater_config.get("config_folder", ".")
        config_file = templater_config.get("config_file", "schemachange-config.yml")

        # Load schemachange configuration
        schemachange_config = self._load_schemachange_config(config_folder, config_file)

        # Set up macro loading from modules folder
        modules_folder = schemachange_config.get("modules-folder")
        search_paths = ["."]  # Always include current directory

        if modules_folder:
            # Resolve modules folder relative to config folder
            modules_path = Path(config_folder) / modules_folder
            if modules_path.exists():
                search_paths.append(str(modules_path))

        # Always ensure we have a FileSystemLoader with the search paths
        env.loader = FileSystemLoader(search_paths)

        # Add schemachange-specific functions to Jinja environment
        # if schemachange adds more functions we may need to add a dependency.
        env.globals["env_var"] = SchemachangeTemplater._get_env_var

        # Add context variables to environment globals
        context = self._get_context_from_config(config, schemachange_config)
        env.globals.update(context)

        logger.debug(f"Configured Jinja environment with {len(env.globals)} globals")
        return env
