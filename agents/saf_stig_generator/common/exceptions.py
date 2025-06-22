"""Custom exceptions for SAF STIG Generator."""


class SAFSTIGGeneratorError(Exception):
    """Base exception for all SAF STIG Generator errors."""

    def __init__(self, message: str, details: str = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ConfigurationError(SAFSTIGGeneratorError):
    """Raised when there's a configuration problem."""

    pass


class ServiceError(SAFSTIGGeneratorError):
    """Raised when a service operation fails."""

    pass


class AgentError(SAFSTIGGeneratorError):
    """Raised when an agent operation fails."""

    pass


class ValidationError(SAFSTIGGeneratorError):
    """Raised when validation fails."""

    pass


class NetworkError(SAFSTIGGeneratorError):
    """Raised when network operations fail."""

    pass


class FileOperationError(SAFSTIGGeneratorError):
    """Raised when file operations fail."""

    pass


class InSpecError(SAFSTIGGeneratorError):
    """Raised when InSpec operations fail."""

    pass


class DockerError(SAFSTIGGeneratorError):
    """Raised when Docker operations fail."""

    pass
