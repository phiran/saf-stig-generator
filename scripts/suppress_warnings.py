"""
Utility module to suppress common deprecation warnings from websockets and uvicorn.

This module should be imported early in MCP tools to suppress deprecation warnings
that don't affect functionality but clutter the output.
"""

import warnings
import sys


def suppress_websocket_warnings():
    """Suppress deprecation warnings from websockets and uvicorn."""

    # Suppress websockets.legacy deprecation warnings
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, module="websockets.legacy.*"
    )

    # Suppress uvicorn websocket protocol warnings
    warnings.filterwarnings(
        "ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets.*"
    )

    # More specific patterns for the exact warnings you're seeing
    warnings.filterwarnings(
        "ignore", message=".*websockets.legacy.*", category=DeprecationWarning
    )

    warnings.filterwarnings(
        "ignore", message=".*websockets_impl.*", category=DeprecationWarning
    )


def configure_warnings_for_mcp():
    """Configure warnings for MCP tools - suppress known harmless deprecations."""

    # Only suppress websocket warnings, keep other deprecation warnings visible
    suppress_websocket_warnings()

    # Optionally, you can also suppress all DeprecationWarnings if they're too noisy:
    # warnings.filterwarnings("ignore", category=DeprecationWarning)


# Auto-configure if imported
if __name__ != "__main__":
    configure_warnings_for_mcp()
