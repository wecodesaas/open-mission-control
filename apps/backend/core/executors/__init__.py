"""Executor implementations for methodology task execution.

This module provides executors that orchestrate the execution of methodology phases.

Available Executors:
- FullAutoExecutor: Executes all phases without user intervention

Story Reference: Epic 4 - Full Auto Execution Pipeline
"""

from .full_auto import FullAutoExecutor, TaskResult

__all__ = ["FullAutoExecutor", "TaskResult"]
