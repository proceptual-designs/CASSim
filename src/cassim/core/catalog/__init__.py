"""Built-in functions and commands, grouped by area and registered on import."""

from cassim.core.catalog import (
    algebra,
    calculus,
    control,
    distributions,
    elementary,
    finance,
    lists,
    matrices,
    solving,
)
from cassim.core.catalog.registry import (
    EagerEntry,
    Entry,
    Host,
    LazyEntry,
    is_builtin,
    lookup,
    lookup_command,
)

__all__ = [
    "EagerEntry",
    "Entry",
    "Host",
    "LazyEntry",
    "algebra",
    "calculus",
    "control",
    "distributions",
    "elementary",
    "finance",
    "is_builtin",
    "lists",
    "lookup",
    "lookup_command",
    "matrices",
    "solving",
]
