"""
GitHub Orchestrator Services
============================

Service layer for GitHub automation workflows.
"""

from .auto_pr_review_orchestrator import (
    AutoPRReviewOrchestrator,
    OrchestratorCancelledError,
    OrchestratorResult,
    OrchestratorRunResult,
    OrchestratorUnauthorizedError,
    get_auto_pr_review_orchestrator,
    reset_auto_pr_review_orchestrator,
)
from .autofix_processor import (
    AutoFixProcessor,
    AutofixProcessorResult,
    cancel_auto_pr_review,
    get_all_active_reviews,
    get_auto_pr_review_config,
    get_auto_pr_review_status,
    is_auto_pr_review_enabled,
    trigger_auto_pr_review_on_qa_pass,
    trigger_auto_pr_review_on_qa_pass_sync,
)
from .batch_processor import BatchProcessor
from .bot_verifier import (
    BotVerifier,
    get_bot_verifier,
    is_trusted_bot,
    require_trusted_bot,
)
from .pr_check_waiter import (
    PRCheckWaiter,
    WaitForChecksResult,
    WaitResult,
    get_pr_check_waiter,
    reset_pr_check_waiter,
)
from .pr_review_engine import PRReviewEngine
from .prompt_manager import PromptManager
from .response_parsers import ResponseParser
from .triage_engine import TriageEngine

__all__ = [
    # Auto PR Review Orchestrator
    "AutoPRReviewOrchestrator",
    "OrchestratorResult",
    "OrchestratorRunResult",
    "OrchestratorCancelledError",
    "OrchestratorUnauthorizedError",
    "get_auto_pr_review_orchestrator",
    "reset_auto_pr_review_orchestrator",
    # Core Services
    "PromptManager",
    "ResponseParser",
    "PRReviewEngine",
    "TriageEngine",
    "AutoFixProcessor",
    "BatchProcessor",
    # Bot Verifier
    "BotVerifier",
    "get_bot_verifier",
    "is_trusted_bot",
    "require_trusted_bot",
    # PR Check Waiter
    "PRCheckWaiter",
    "WaitForChecksResult",
    "WaitResult",
    "get_pr_check_waiter",
    "reset_pr_check_waiter",
    # Autofix Processor (QA pass workflow integration)
    "AutofixProcessorResult",
    "trigger_auto_pr_review_on_qa_pass",
    "trigger_auto_pr_review_on_qa_pass_sync",
    "is_auto_pr_review_enabled",
    "get_auto_pr_review_config",
    "cancel_auto_pr_review",
    "get_auto_pr_review_status",
    "get_all_active_reviews",
]
