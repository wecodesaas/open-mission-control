"""Full Auto Executor for autonomous methodology execution.

Story Reference: Story 4.1 - Implement Full Auto Task Executor

This module provides the FullAutoExecutor class that executes all methodology
phases without user intervention. In Full Auto mode, the system executes
planning, coding, and validation phases in sequence, reporting progress
continuously.

Architecture Source: architecture.md#Task-Execution
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

# fcntl is POSIX only - use for file locking on Unix/macOS
try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

from apps.backend.methodologies.protocols import (
    MethodologyRunner,
    Phase,
    PhaseResult,
    PhaseStatus,
    ProgressEvent,
    ProgressStatus,
    RunContext,
    TaskConfig,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of executing a methodology task.

    Story Reference: Story 4.1 Task 1 - TaskResult structure

    Attributes:
        status: Outcome of the task execution. Values:
            - "completed": All phases executed successfully
            - "failed": A phase failed during execution
            - "escalated": Task requires human intervention (Story 4.5 - future scope)
        phase: ID of the phase that failed (if status is "failed")
        error: Error message if execution failed
        artifacts: List of artifact file paths produced
        duration_seconds: Total execution time in seconds

    Note: The "escalated" status is pre-defined for Story 4.5 (Implement Task
    Escalation Handling). Currently only "completed" and "failed" are returned
    by FullAutoExecutor.
    """

    status: Literal["completed", "failed", "escalated"]
    phase: str | None = None
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)
    duration_seconds: float = 0


class FullAutoExecutor:
    """Executor for Full Auto mode that runs all phases without pausing.

    In Full Auto mode, the executor:
    - Loops through all methodology phases in sequence
    - Executes each phase without user prompts
    - Reports progress continuously via ProgressService
    - Continues until completion or failure
    - Logs phase start/complete with timestamps

    Story Reference: Story 4.1 - Implement Full Auto Task Executor
    Architecture Source: architecture.md#Task-Execution

    Example:
        runner = get_methodology_runner("native")
        context = create_run_context(task_config)
        executor = FullAutoExecutor(
            runner=runner,
            context=context,
            task_config=task_config,
        )
        result = await executor.execute()
        if result.status == "completed":
            print("Task completed successfully!")
    """

    def __init__(
        self,
        runner: MethodologyRunner,
        context: RunContext,
        task_config: TaskConfig,
        log_dir: str | Path | None = None,
    ) -> None:
        """Initialize the Full Auto executor.

        Story Reference: Story 4.1 Task 1 - Accept task configuration and methodology runner

        Args:
            runner: The methodology runner that provides phases and execution logic
            context: RunContext with access to all framework services
            task_config: Configuration for the task being executed
            log_dir: Optional directory for storing execution logs
        """
        self.runner = runner
        self.context = context
        self.task_config = task_config
        self._log_dir = Path(log_dir) if log_dir else None
        self._start_time: float = 0
        self._collected_artifacts: list[str] = []
        self._phases: list[Phase] = []

        # Task-specific logger for filtering logs by task ID.
        # Logger name format: "apps.backend.core.executors.full_auto.{task_id}"
        # This allows log filtering with: logging.getLogger("...full_auto.task-123")
        self._logger = logging.getLogger(f"{__name__}.{task_config.task_id}")

    async def execute(self) -> TaskResult:
        """Execute all phases without user intervention.

        Story Reference: Story 4.1 Task 2 - Implement execute method

        This method:
        1. Initializes the methodology runner with context
        2. Gets all phases from the runner
        3. Executes each phase in sequence
        4. Reports progress continuously
        5. Collects artifacts from each phase
        6. Returns a TaskResult with final status

        Returns:
            TaskResult indicating success/failure and execution details

        Raises:
            No exceptions are raised; errors are captured in TaskResult
        """
        self._start_time = time.time()

        # Initialize the methodology runner
        self._log_info("Initializing methodology runner")
        self.runner.initialize(self.context)

        # Get all phases from the methodology
        self._phases = self.runner.get_phases()
        total_phases = len(self._phases)

        if total_phases == 0:
            self._log_warning("No phases defined in methodology")
            return TaskResult(
                status="failed",
                error="No phases defined in methodology",
                duration_seconds=self._get_elapsed_time(),
            )

        self._log_info(f"Starting execution with {total_phases} phases")
        self._emit_progress_event(
            phase_id="init",
            status=ProgressStatus.STARTED,
            message=f"Starting Full Auto execution with {total_phases} phases",
            percentage=0.0,
        )

        # Execute each phase in sequence
        for index, phase in enumerate(self._phases):
            phase_result = self._execute_phase(phase, index, total_phases)

            if not phase_result.success:
                self._log_error(
                    f"Phase {phase.name} failed: {phase_result.error}",
                    phase_id=phase.id,
                )
                self._emit_progress_event(
                    phase_id=phase.id,
                    status=ProgressStatus.FAILED,
                    message=f"Phase {phase.name} failed: {phase_result.error}",
                    percentage=self._calculate_percentage(index, total_phases),
                )
                return TaskResult(
                    status="failed",
                    phase=phase.id,
                    error=phase_result.error,
                    artifacts=self._collected_artifacts,
                    duration_seconds=self._get_elapsed_time(),
                )

            # Collect artifacts from this phase
            if phase_result.artifacts:
                self._collected_artifacts.extend(phase_result.artifacts)

        # All phases completed successfully
        duration = self._get_elapsed_time()
        self._log_info(f"All phases completed successfully in {duration:.2f}s")
        self._emit_progress_event(
            phase_id="complete",
            status=ProgressStatus.COMPLETED,
            message=f"Task completed successfully in {duration:.2f}s",
            percentage=100.0,
        )

        return TaskResult(
            status="completed",
            artifacts=self._collected_artifacts,
            duration_seconds=duration,
        )

    def _execute_phase(
        self, phase: Phase, index: int, total_phases: int
    ) -> PhaseResult:
        """Execute a single phase and report progress.

        Story Reference: Story 4.1 Task 4 - Implement phase sequencing

        Note: This method is synchronous because MethodologyRunner.execute_phase()
        is defined as synchronous in the Protocol (protocols.py). The outer
        execute() method is async to allow for async context setup and future
        async runner support.

        Args:
            phase: The phase to execute
            index: Current phase index (0-based)
            total_phases: Total number of phases

        Returns:
            PhaseResult from the methodology runner
        """
        percentage = self._calculate_percentage(index, total_phases)

        # Log and emit phase start
        self._log_info(f"Starting phase: {phase.name}", phase_id=phase.id)
        self._emit_progress_event(
            phase_id=phase.id,
            status=ProgressStatus.STARTED,
            message=f"Starting phase: {phase.name}",
            percentage=percentage,
        )

        # Update phase status to in-progress
        phase.status = PhaseStatus.IN_PROGRESS

        try:
            # Execute the phase
            result = self.runner.execute_phase(phase.id)

            if result.success:
                phase.status = PhaseStatus.COMPLETED
                self._log_info(
                    f"Completed phase: {phase.name}",
                    phase_id=phase.id,
                )
                self._emit_progress_event(
                    phase_id=phase.id,
                    status=ProgressStatus.COMPLETED,
                    message=f"Completed phase: {phase.name}",
                    percentage=self._calculate_percentage(index + 1, total_phases),
                )
            else:
                phase.status = PhaseStatus.FAILED

            return result

        except Exception as e:
            # Catch and handle execution errors
            phase.status = PhaseStatus.FAILED
            error_msg = f"Exception during phase execution: {e}"
            self._log_error(error_msg, phase_id=phase.id)
            return PhaseResult(
                success=False,
                phase_id=phase.id,
                error=error_msg,
            )

    def _calculate_percentage(self, completed_phases: int, total_phases: int) -> float:
        """Calculate overall progress percentage.

        Story Reference: Story 4.1 Task 3 - Report overall task percentage

        Args:
            completed_phases: Number of phases completed
            total_phases: Total number of phases

        Returns:
            Percentage as float (0.0 to 100.0)
        """
        if total_phases == 0:
            return 0.0
        return (completed_phases / total_phases) * 100.0

    def _emit_progress_event(
        self,
        phase_id: str,
        status: ProgressStatus,
        message: str,
        percentage: float,
    ) -> None:
        """Emit a progress event through the context's progress service.

        Story Reference: Story 4.1 Task 3 - Emit progress events during execution

        Args:
            phase_id: ID of the current phase
            status: Progress status enum value
            message: Human-readable progress message
            percentage: Current overall percentage (0.0 to 100.0)
        """
        event = ProgressEvent(
            task_id=self.task_config.task_id,
            phase_id=phase_id,
            status=status.value,
            message=message,
            percentage=percentage,
            artifacts=list(self._collected_artifacts),
            timestamp=datetime.now(),
        )

        try:
            self.context.progress.emit(event)
        except Exception as e:
            self._logger.warning(f"Failed to emit progress event: {e}")

    def _get_elapsed_time(self) -> float:
        """Get elapsed time since execution started.

        Returns:
            Elapsed time in seconds
        """
        return time.time() - self._start_time

    def _log_info(self, message: str, phase_id: str | None = None) -> None:
        """Log an info message with timestamp and optional phase ID.

        Story Reference: Story 4.1 Task 5 - Log phase start with timestamp

        Args:
            message: Message to log
            phase_id: Optional phase identifier
        """
        timestamp = datetime.now().isoformat()
        prefix = f"[{phase_id}] " if phase_id else ""
        log_message = f"{prefix}{message}"
        self._logger.info(log_message)

        # Also store to log file if log_dir is configured
        self._write_to_log_file("INFO", timestamp, log_message)

    def _log_warning(self, message: str, phase_id: str | None = None) -> None:
        """Log a warning message.

        Story Reference: Story 4.1 Task 5 - Log any errors or warnings

        Args:
            message: Warning message
            phase_id: Optional phase identifier
        """
        timestamp = datetime.now().isoformat()
        prefix = f"[{phase_id}] " if phase_id else ""
        log_message = f"{prefix}{message}"
        self._logger.warning(log_message)
        self._write_to_log_file("WARNING", timestamp, log_message)

    def _log_error(self, message: str, phase_id: str | None = None) -> None:
        """Log an error message.

        Story Reference: Story 4.1 Task 5 - Log phase result (success/failure)

        Args:
            message: Error message
            phase_id: Optional phase identifier
        """
        timestamp = datetime.now().isoformat()
        prefix = f"[{phase_id}] " if phase_id else ""
        log_message = f"{prefix}{message}"
        self._logger.error(log_message)
        self._write_to_log_file("ERROR", timestamp, log_message)

    def _write_to_log_file(self, level: str, timestamp: str, message: str) -> None:
        """Write a log entry to the task's log file.

        Story Reference: Story 4.1 Task 5 - Store logs in task directory

        Uses file locking (fcntl.flock) on POSIX systems to prevent
        interleaved log entries when multiple executors write concurrently.

        Args:
            level: Log level (INFO, WARNING, ERROR)
            timestamp: ISO format timestamp
            message: Log message
        """
        if not self._log_dir:
            return

        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            log_file = self._log_dir / f"execution_{self.task_config.task_id}.log"

            with open(log_file, "a") as f:
                # Acquire exclusive lock on POSIX systems to prevent race conditions
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(f"[{timestamp}] [{level}] {message}\n")
                finally:
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            self._logger.warning(f"Failed to write to log file: {e}")
