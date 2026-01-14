"""Exception hierarchy for the plugin framework.

Defines all custom exceptions used by the methodologies/plugin system.
Following architecture-defined patterns from Error-Handling-Patterns.
"""


class AutoClaudeError(Exception):
    """Base exception for all Auto Claude errors.

    All framework-level exceptions should inherit from this class
    to enable catching all Auto Claude errors with a single except clause.
    """

    pass


class PluginError(AutoClaudeError):
    """Base exception for plugin-related errors.

    All plugin-specific exceptions should inherit from this class.
    Use this for general plugin failures that don't fit other categories.
    """

    pass


class ManifestValidationError(PluginError):
    """Raised when manifest.yaml is invalid.

    This exception is raised when:
    - manifest.yaml is missing required fields
    - Field values have incorrect types
    - Schema validation fails
    - Version constraints cannot be satisfied
    """

    pass


class PluginLoadError(PluginError):
    """Raised when plugin module fails to load.

    This exception is raised when:
    - Plugin directory structure is invalid
    - Required Python modules cannot be imported
    - Plugin entry point is missing or invalid
    - Dependencies are missing
    """

    pass


class ProtocolViolationError(PluginError):
    """Raised when a plugin violates its Protocol contract.

    This exception is raised when:
    - A plugin doesn't implement all required Protocol methods
    - Method signatures don't match the Protocol definition
    - Return types don't match expected types
    - Runtime behavior violates Protocol semantics
    """

    pass
