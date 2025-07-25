"""Custom exceptions for Schemax."""


class SchemaxError(Exception):
    """Base exception for all Schemax errors."""


class ConfigurationError(SchemaxError):
    """Raised when there's a configuration issue."""


class SchemaParsingError(SchemaxError):
    """Raised when schema parsing fails."""


class DatabricksConnectionError(SchemaxError):
    """Raised when Databricks connection fails."""


class ChangeGenerationError(SchemaxError):
    """Raised when change script generation fails."""


class ValidationError(SchemaxError):
    """Raised when schema validation fails."""
