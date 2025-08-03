"""SQLFluff templater plugin for schemachange integration."""

from sqlfluff.core.plugin import hookimpl

from sqlfluff_templater_schemachange.templater import SchemachangeTemplater

__version__ = "0.1.0"
__all__ = ["SchemachangeTemplater"]


@hookimpl
def get_templaters():
    """Return the list of templaters provided by this plugin."""
    return [SchemachangeTemplater]
