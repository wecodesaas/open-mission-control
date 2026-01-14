"""Methodology plugin framework for Auto Claude.

This package provides the core infrastructure for methodology plugins.
All Protocol interfaces and supporting types are exported here.

Usage:
    from apps.backend.methodologies import (
        MethodologyRunner,
        RunContext,
        Phase,
        PhaseResult,
        Checkpoint,
        Artifact,
    )

Architecture Source: architecture.md#Core-Architectural-Decisions
"""

from apps.backend.methodologies.exceptions import (
    AutoClaudeError,
    ManifestValidationError,
    PluginError,
    PluginLoadError,
    ProtocolViolationError,
)
from apps.backend.methodologies.protocols import (
    Artifact,
    Checkpoint,
    CheckpointService,
    CheckpointStatus,
    ComplexityLevel,
    # Enums
    ExecutionMode,
    LLMService,
    MemoryService,
    MethodologyInfo,
    # Additional Protocols
    MethodologyRegistry,
    # Core Protocol
    MethodologyRunner,
    NotificationService,
    Phase,
    PhaseResult,
    PhaseStatus,
    ProgressService,
    # Supporting dataclasses
    RunContext,
    TaskConfig,
    TaskStateManager,
    # Service protocols (for type hints)
    WorkspaceService,
)

__all__ = [
    # Core Protocol
    "MethodologyRunner",
    # Supporting dataclasses
    "RunContext",
    "Phase",
    "PhaseResult",
    "Checkpoint",
    "Artifact",
    "TaskConfig",
    "MethodologyInfo",
    # Service protocols
    "WorkspaceService",
    "MemoryService",
    "ProgressService",
    "CheckpointService",
    "LLMService",
    # Enums
    "ExecutionMode",
    "ComplexityLevel",
    "PhaseStatus",
    "CheckpointStatus",
    # Additional Protocols
    "MethodologyRegistry",
    "TaskStateManager",
    "NotificationService",
    # Exceptions
    "AutoClaudeError",
    "PluginError",
    "ManifestValidationError",
    "PluginLoadError",
    "ProtocolViolationError",
]
