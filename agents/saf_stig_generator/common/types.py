"""Common type definitions for SAF STIG Generator."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Type aliases for common data structures
ServiceResult = Dict[str, Any]
STIGControl = Dict[str, Any]
InSpecResult = Dict[str, Any]
BaselineConfig = Dict[str, Any]

# Common path types
PathLike = Union[str, Path]


# Service response types
class ServiceResponse:
    """Standard response format for MCP services."""

    def __init__(
        self,
        status: str,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
        errors: Optional[List[str]] = None,
    ):
        self.status = status
        self.data = data or {}
        self.message = message
        self.errors = errors or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"status": self.status}

        if self.data:
            result["data"] = self.data
        if self.message:
            result["message"] = self.message
        if self.errors:
            result["errors"] = self.errors

        return result


# Agent event types
AgentEvent = Dict[str, Any]
ToolResult = Dict[str, Any]
