"""SQLFluff templater plugin for schemachange integration."""

import importlib.util
import os

from sqlfluff.core.plugin import hookimpl

# Import the module with hyphens in filename
spec = importlib.util.spec_from_file_location(
    "sqlfluff_templater_schemachange",
    os.path.join(os.path.dirname(__file__), "sqlfluff-templater-schemachange.py"),
)
if spec is None or spec.loader is None:
    raise ImportError("Could not load sqlfluff-templater-schemachange module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SchemachangeTemplater = module.SchemachangeTemplater

__version__ = "0.1.1"
__all__ = ["SchemachangeTemplater"]


@hookimpl
def get_templaters():
    """Return the list of templaters provided by this plugin."""
    return [SchemachangeTemplater]
