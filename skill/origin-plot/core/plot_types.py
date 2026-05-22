"""Plot type catalogue for v1.0.

The v1.0 core surface restricts itself to plot types that have been verified
end-to-end through the v0.8.7 stability work:

* line
* scatter
* line_symbol
* errorbar
* line / line_symbol with curve fitting overlays
"""
from __future__ import annotations

from typing import Iterable

CORE_GRAPH_TYPES: frozenset[str] = frozenset(
    {"line", "scatter", "line_symbol", "errorbar"}
)


def is_supported(graph_type: str) -> bool:
    return graph_type.lower() in CORE_GRAPH_TYPES


def supported_types() -> Iterable[str]:
    return sorted(CORE_GRAPH_TYPES)


__all__ = ["CORE_GRAPH_TYPES", "is_supported", "supported_types"]
