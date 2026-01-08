"""
Autofix Processor
=================

Connects the Auto-PR-Review workflow to QA pass events.

When QA passes on a PR, this processor triggers the AutoPRReviewOrchestrator
to automatically review and fix any remaining issues before human approval.

Key Features:
- Triggers auto PR review after QA passes
- Respects authorization checks
- Supports async and sync invocation
- NEVER auto-merges (human approval always required)

Usage:
    # Async usage
    result = await trigger_auto_pr_review_on_qa_pass(
        pr_number=123,
        repo="owner/repo",
        pr_url="https://github.com/owner/repo/pull/123",
        branch_name="feature-branch",
        triggered_by="qa-agent",
    )

    # Check if auto PR review is enabled
    if is_auto_pr_review_enabled():
        # Proceed with auto review
        pass
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import structlog

    logger = structlog.get_logger(__name__)
    STRUCTLOG_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    STRUCTLOG_AVAILABLE = False

from .auto_pr_review_orchestrator import (
    OrchestratorResult,
    OrchestratorRunResult,
    get_auto_pr_review_orchestrator,
)

# =============================================================================
# Configuration
# =============================================================================

# Environment variable to enable/disable auto PR review
AUTO_PR_REVIEW_ENABLED_ENV = "GITHUB_AUTO_PR_REVIEW_ENABLED"

# Default settings
DEFAULT_GITHUB_DIR = Path(".auto-claude/github")
DEFAULT_SPEC_DIR = Path(".auto-claude/specs")


# =============================================================================
# Result Types
# =============================================================================


@dataclass
class AutofixProcessorResult:
    """Result of the autofix processor."""

    success: bool
    triggered: bool
    pr_number: int
    repo: str
    orchestrator_result: OrchestratorRunResult | None = None
    error_message: str | None = None
    skipped_reason: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "triggered": self.triggered,
            "pr_number": self.pr_number,
            "repo": self.repo,
            "error_message": self.error_message,
            "skipped_reason": self.skipped_reason,
        }
        if self.orchestrator_result:
            result["orchestrator_result"] = self.orchestrator_result.to_dict()
        return result


# =============================================================================
# Configuration Helpers
# =============================================================================


def is_auto_pr_review_enabled() -> bool:
    """
    Check if auto PR review is enabled via environment variable.

    Returns:
        True if GITHUB_AUTO_PR_REVIEW_ENABLED is set to "true", "1", or "yes"
    """
    value = os.environ.get(AUTO_PR_REVIEW_ENABLED_ENV, "").lower().strip()
    return value in ("true", "1", "yes", "on")


def get_auto_pr_review_config() -> dict[str, Any]:
    """
    Get the current auto PR review configuration.

    Returns:
        Dictionary with configuration settings
    """
    return {
        "enabled": is_auto_pr_review_enabled(),
        "allowed_users_env": os.environ.get("GITHUB_AUTO_PR_REVIEW_ALLOWED_USERS", ""),
        "expected_bots_env": os.environ.get("GITHUB_EXPECTED_BOTS", ""),
        "max_iterations": int(
            os.environ.get("GITHUB_AUTO_PR_REVIEW_MAX_ITERATIONS", "5")
        ),
    }


# =============================================================================
# Logging Helpers
# =============================================================================


def _log_info(message: str, **kwargs: Any) -> None:
    """Log an info message with context."""
    if STRUCTLOG_AVAILABLE:
        logger.info(message, **kwargs)
    else:
        logger.info(f"{message} {kwargs}")


def _log_warning(message: str, **kwargs: Any) -> None:
    """Log a warning message with context."""
    if STRUCTLOG_AVAILABLE:
        logger.warning(message, **kwargs)
    else:
        logger.warning(f"{message} {kwargs}")


def _log_error(message: str, **kwargs: Any) -> None:
    """Log an error message with context."""
    if STRUCTLOG_AVAILABLE:
        logger.error(message, **kwargs)
    else:
        logger.error(f"{message} {kwargs}")


# =============================================================================
# Main Entry Point
# =============================================================================


async def trigger_auto_pr_review_on_qa_pass(
    pr_number: int,
    repo: str,
    pr_url: str,
    branch_name: str,
    triggered_by: str,
    github_dir: Path | None = None,
    project_dir: Path | None = None,
    spec_dir: Path | None = None,
    on_progress: Callable[[str, Any], None] | None = None,
    force: bool = False,
) -> AutofixProcessorResult:
    """
    Trigger auto PR review after QA passes.

    This is the main entry point for connecting QA pass events to the
    AutoPRReviewOrchestrator. Call this function when QA passes on a PR
    to initiate the automatic review and fix workflow.

    Args:
        pr_number: PR number to review
        repo: Repository in owner/repo format
        pr_url: Full URL to the PR
        branch_name: PR branch name
        triggered_by: Username who triggered the review (usually "qa-agent")
        github_dir: Directory for GitHub state files (default: .auto-claude/github)
        project_dir: Project root directory (default: current directory)
        spec_dir: Spec directory for this task (default: .auto-claude/specs)
        on_progress: Optional callback for progress updates
        force: If True, skip the enabled check

    Returns:
        AutofixProcessorResult with status and optional orchestrator result

    Notes:
        - This function NEVER auto-merges. Human approval is always required.
        - The orchestrator result will indicate READY_TO_MERGE when all checks pass,
          but a human must explicitly approve and merge the PR.
    """
    _log_info(
        "QA passed - checking if auto PR review should trigger",
        pr_number=pr_number,
        repo=repo,
        triggered_by=triggered_by,
    )

    # Check if auto PR review is enabled
    if not force and not is_auto_pr_review_enabled():
        _log_info(
            "Auto PR review is disabled, skipping",
            pr_number=pr_number,
            repo=repo,
        )
        return AutofixProcessorResult(
            success=True,
            triggered=False,
            pr_number=pr_number,
            repo=repo,
            skipped_reason="Auto PR review is disabled (set GITHUB_AUTO_PR_REVIEW_ENABLED=true to enable)",
        )

    # Resolve directories
    resolved_github_dir = github_dir or Path.cwd() / DEFAULT_GITHUB_DIR
    resolved_project_dir = project_dir or Path.cwd()
    resolved_spec_dir = spec_dir or Path.cwd() / DEFAULT_SPEC_DIR

    try:
        # Get or create orchestrator instance
        orchestrator = get_auto_pr_review_orchestrator(
            github_dir=resolved_github_dir,
            project_dir=resolved_project_dir,
            spec_dir=resolved_spec_dir,
        )

        # Run the review workflow
        _log_info(
            "Triggering auto PR review",
            pr_number=pr_number,
            repo=repo,
            triggered_by=triggered_by,
        )

        result = await orchestrator.run(
            pr_number=pr_number,
            repo=repo,
            pr_url=pr_url,
            branch_name=branch_name,
            triggered_by=triggered_by,
            on_progress=on_progress,
        )

        # Determine success based on result
        success = result.result in (
            OrchestratorResult.READY_TO_MERGE,
            OrchestratorResult.NO_FINDINGS,
            OrchestratorResult.PR_MERGED,  # Merged externally is OK
        )

        if result.result == OrchestratorResult.READY_TO_MERGE:
            _log_info(
                "Auto PR review completed - ready for human review",
                pr_number=pr_number,
                repo=repo,
                iterations=result.iterations_completed,
                findings_fixed=result.findings_fixed,
            )
        elif result.result == OrchestratorResult.UNAUTHORIZED:
            _log_warning(
                "Auto PR review unauthorized",
                pr_number=pr_number,
                repo=repo,
                triggered_by=triggered_by,
            )
        else:
            _log_info(
                "Auto PR review completed",
                pr_number=pr_number,
                repo=repo,
                result=result.result.value,
            )

        return AutofixProcessorResult(
            success=success,
            triggered=True,
            pr_number=pr_number,
            repo=repo,
            orchestrator_result=result,
            error_message=result.error_message if not success else None,
        )

    except Exception as e:
        _log_error(
            f"Auto PR review failed: {e}",
            pr_number=pr_number,
            repo=repo,
        )
        return AutofixProcessorResult(
            success=False,
            triggered=True,
            pr_number=pr_number,
            repo=repo,
            error_message=str(e),
        )


def trigger_auto_pr_review_on_qa_pass_sync(
    pr_number: int,
    repo: str,
    pr_url: str,
    branch_name: str,
    triggered_by: str,
    **kwargs,
) -> AutofixProcessorResult:
    """
    Synchronous wrapper for trigger_auto_pr_review_on_qa_pass.

    Use this when calling from synchronous code that cannot use async/await.

    Args:
        Same as trigger_auto_pr_review_on_qa_pass

    Returns:
        AutofixProcessorResult with status and optional orchestrator result
    """
    return asyncio.run(
        trigger_auto_pr_review_on_qa_pass(
            pr_number=pr_number,
            repo=repo,
            pr_url=pr_url,
            branch_name=branch_name,
            triggered_by=triggered_by,
            **kwargs,
        )
    )


# =============================================================================
# Cancellation Support
# =============================================================================


def cancel_auto_pr_review(pr_number: int) -> bool:
    """
    Cancel an in-progress auto PR review.

    Args:
        pr_number: PR number to cancel

    Returns:
        True if cancellation was requested, False if no active review found
    """
    try:
        orchestrator = get_auto_pr_review_orchestrator()
        return orchestrator.cancel(pr_number)
    except ValueError:
        # Orchestrator not initialized
        return False


# =============================================================================
# Status Queries
# =============================================================================


def get_auto_pr_review_status(pr_number: int) -> dict | None:
    """
    Get the status of an auto PR review.

    Args:
        pr_number: PR number to check

    Returns:
        Status dictionary or None if no active review
    """
    try:
        orchestrator = get_auto_pr_review_orchestrator()
        active_reviews = orchestrator.get_active_reviews()
        if pr_number in active_reviews:
            state = active_reviews[pr_number]
            return {
                "pr_number": state.pr_number,
                "repo": state.repo,
                "status": state.status.value,
                "current_iteration": state.current_iteration,
                "max_iterations": state.max_iterations,
                "ci_all_passed": state.ci_all_passed,
                "started_at": state.started_at,
            }
        return None
    except ValueError:
        # Orchestrator not initialized
        return None


def get_all_active_reviews() -> list[dict]:
    """
    Get all active auto PR reviews.

    Returns:
        List of status dictionaries for all active reviews
    """
    try:
        orchestrator = get_auto_pr_review_orchestrator()
        active_reviews = orchestrator.get_active_reviews()
        return [
            {
                "pr_number": state.pr_number,
                "repo": state.repo,
                "status": state.status.value,
                "current_iteration": state.current_iteration,
                "max_iterations": state.max_iterations,
            }
            for state in active_reviews.values()
        ]
    except ValueError:
        return []


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Main entry points
    "trigger_auto_pr_review_on_qa_pass",
    "trigger_auto_pr_review_on_qa_pass_sync",
    # Configuration
    "is_auto_pr_review_enabled",
    "get_auto_pr_review_config",
    # Cancellation
    "cancel_auto_pr_review",
    # Status queries
    "get_auto_pr_review_status",
    "get_all_active_reviews",
    # Result type
    "AutofixProcessorResult",
]
