"""Custom exceptions for Schemax."""


class SchemaxError(Exception):
    """Base exception for all Schemax errors."""
    pass


class ConfigurationError(SchemaxError):
    """Raised when there's a configuration issue."""
    pass


class SchemaParsingError(SchemaxError):
    """Raised when schema parsing fails."""
    pass


class DatabricksConnectionError(SchemaxError):
    """Raised when Databricks connection fails."""
    pass


class ChangeGenerationError(SchemaxError):
    """Raised when change script generation fails."""
    pass


class ValidationError(SchemaxError):
    """Raised when schema validation fails."""
    pass 