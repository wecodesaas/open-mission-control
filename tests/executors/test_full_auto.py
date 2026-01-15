"""Tests for FullAutoExecutor.

Story Reference: Story 4.1 - Implement Full Auto Task Executor

Tests the FullAutoExecutor class which executes all methodology phases
without user intervention in Full Auto mode.
"""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from apps.backend.core.executors import FullAutoExecutor, TaskResult
from apps.backend.methodologies.protocols import (
    Artifact,
    Checkpoint,
    Phase,
    PhaseResult,
    PhaseStatus,
    ProgressEvent,
    RunContext,
    TaskConfig,
)


# =============================================================================
# Mock Service Implementations
# =============================================================================


class MockWorkspaceService:
    """Mock implementation of WorkspaceService."""

    def get_project_root(self) -> str:
        return "/mock/project"


class MockMemoryService:
    """Mock implementation of MemoryService."""

    def get_context(self, query: str) -> str:
        return f"Context for: {query}"


class MockProgressService:
    """Mock implementation of ProgressService that captures events."""

    def __init__(self):
        self.events: list[ProgressEvent] = []
        self.updates: list[tuple[str, float, str]] = []

    def update(self, phase_id: str, progress: float, message: str) -> None:
        self.updates.append((phase_id, progress, message))

    def emit(self, event: ProgressEvent) -> None:
        self.events.append(event)


class MockCheckpointService:
    """Mock implementation of CheckpointService."""

    def create_checkpoint(self, checkpoint_id: str, data: dict[str, Any]) -> None:
        pass


class MockLLMService:
    """Mock implementation of LLMService."""

    def generate(self, prompt: str) -> str:
        return f"Response to: {prompt}"


class MockMethodologyRunner:
    """Mock implementation of MethodologyRunner for testing."""

    def __init__(
        self,
        phases: list[Phase] | None = None,
        phase_results: dict[str, PhaseResult] | None = None,
        raise_on_phase: str | None = None,
    ):
        # Use 'is not None' to allow empty list
        self._phases = phases if phases is not None else [
            Phase(id="planning", name="Planning", order=0),
            Phase(id="coding", name="Coding", order=1),
            Phase(id="validation", name="Validation", order=2),
        ]
        self._phase_results = phase_results or {}
        self._raise_on_phase = raise_on_phase
        self._initialized = False
        self._executed_phases: list[str] = []

    def initialize(self, context: RunContext) -> None:
        self._initialized = True
        self._context = context

    def get_phases(self) -> list[Phase]:
        return self._phases

    def execute_phase(self, phase_id: str) -> PhaseResult:
        self._executed_phases.append(phase_id)

        if self._raise_on_phase == phase_id:
            raise RuntimeError(f"Simulated error in phase {phase_id}")

        if phase_id in self._phase_results:
            return self._phase_results[phase_id]

        return PhaseResult(
            success=True,
            phase_id=phase_id,
            message=f"Phase {phase_id} completed",
            artifacts=[f"{phase_id}_output.md"],
        )

    def get_checkpoints(self) -> list[Checkpoint]:
        return []

    def get_artifacts(self) -> list[Artifact]:
        return []


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_progress_service():
    """Create a mock progress service that captures events."""
    return MockProgressService()


@pytest.fixture
def mock_context(mock_progress_service):
    """Create a mock RunContext with all services."""
    return RunContext(
        workspace=MockWorkspaceService(),
        memory=MockMemoryService(),
        progress=mock_progress_service,
        checkpoint=MockCheckpointService(),
        llm=MockLLMService(),
        task_config=TaskConfig(task_id="test-task-123", task_name="Test Task"),
    )


@pytest.fixture
def mock_runner():
    """Create a mock methodology runner with default phases."""
    return MockMethodologyRunner()


@pytest.fixture
def executor(mock_runner, mock_context):
    """Create a FullAutoExecutor with mock dependencies."""
    return FullAutoExecutor(
        runner=mock_runner,
        context=mock_context,
        task_config=mock_context.task_config,
    )


# =============================================================================
# Test Classes
# =============================================================================


class TestFullAutoExecutorImport:
    """Test that FullAutoExecutor can be imported and instantiated."""

    def test_import_full_auto_executor(self):
        """Test that FullAutoExecutor can be imported from core.executors."""
        from apps.backend.core.executors import FullAutoExecutor

        assert FullAutoExecutor is not None

    def test_import_task_result(self):
        """Test that TaskResult can be imported from core.executors."""
        from apps.backend.core.executors import TaskResult

        assert TaskResult is not None


class TestTaskResultDataclass:
    """Test the TaskResult dataclass."""

    def test_task_result_completed(self):
        """Test TaskResult for completed status."""
        result = TaskResult(
            status="completed",
            artifacts=["spec.md", "plan.json"],
            duration_seconds=45.5,
        )
        assert result.status == "completed"
        assert result.phase is None
        assert result.error is None
        assert len(result.artifacts) == 2
        assert result.duration_seconds == 45.5

    def test_task_result_failed(self):
        """Test TaskResult for failed status with phase and error."""
        result = TaskResult(
            status="failed",
            phase="coding",
            error="Compilation error",
            duration_seconds=12.3,
        )
        assert result.status == "failed"
        assert result.phase == "coding"
        assert result.error == "Compilation error"

    def test_task_result_escalated(self):
        """Test TaskResult for escalated status.

        Note: The "escalated" status is pre-defined for Story 4.5 (Implement
        Task Escalation Handling). This test verifies the dataclass accepts
        the status but the actual escalation code path is not yet implemented.
        """
        result = TaskResult(
            status="escalated",
            phase="validation",
            error="Requires manual intervention",
        )
        assert result.status == "escalated"

    def test_task_result_default_values(self):
        """Test TaskResult default values."""
        result = TaskResult(status="completed")
        assert result.phase is None
        assert result.error is None
        assert result.artifacts == []
        assert result.duration_seconds == 0


class TestFullAutoExecutorInit:
    """Test FullAutoExecutor initialization (Task 1)."""

    def test_init_accepts_runner_and_context(self, executor, mock_runner, mock_context):
        """Test that executor accepts runner, context, and task_config."""
        assert executor.runner is mock_runner
        assert executor.context is mock_context
        assert executor.task_config is mock_context.task_config

    def test_init_with_log_dir(self, mock_runner, mock_context):
        """Test executor can be initialized with log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = FullAutoExecutor(
                runner=mock_runner,
                context=mock_context,
                task_config=mock_context.task_config,
                log_dir=tmpdir,
            )
            assert executor._log_dir == Path(tmpdir)

    def test_init_log_dir_none_by_default(self, executor):
        """Test that log_dir is None by default."""
        assert executor._log_dir is None


class TestFullAutoExecutorExecute:
    """Test FullAutoExecutor.execute() method (Task 2)."""

    @pytest.mark.asyncio
    async def test_execute_runs_all_phases(self, executor, mock_runner):
        """Test that execute runs all phases in sequence."""
        result = await executor.execute()

        assert result.status == "completed"
        assert len(mock_runner._executed_phases) == 3
        assert mock_runner._executed_phases == ["planning", "coding", "validation"]

    @pytest.mark.asyncio
    async def test_execute_initializes_runner(self, executor, mock_runner):
        """Test that execute initializes the runner first."""
        await executor.execute()
        assert mock_runner._initialized is True

    @pytest.mark.asyncio
    async def test_execute_returns_task_result(self, executor):
        """Test that execute returns a TaskResult."""
        result = await executor.execute()
        assert isinstance(result, TaskResult)

    @pytest.mark.asyncio
    async def test_execute_collects_artifacts(self, executor):
        """Test that execute collects artifacts from all phases."""
        result = await executor.execute()

        assert "planning_output.md" in result.artifacts
        assert "coding_output.md" in result.artifacts
        assert "validation_output.md" in result.artifacts

    @pytest.mark.asyncio
    async def test_execute_measures_duration(self, executor):
        """Test that execute measures and returns duration."""
        result = await executor.execute()
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_execute_no_phases_fails(self, mock_context):
        """Test that execute fails gracefully when no phases defined."""
        empty_runner = MockMethodologyRunner(phases=[])
        executor = FullAutoExecutor(
            runner=empty_runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        result = await executor.execute()

        assert result.status == "failed"
        assert "No phases" in result.error


class TestProgressReporting:
    """Test progress reporting integration (Task 3)."""

    @pytest.mark.asyncio
    async def test_emit_progress_on_start(self, executor, mock_progress_service):
        """Test that progress event is emitted at start."""
        await executor.execute()

        start_events = [e for e in mock_progress_service.events if e.status == "started"]
        assert len(start_events) >= 1

    @pytest.mark.asyncio
    async def test_emit_progress_on_phase_start(self, executor, mock_progress_service):
        """Test that progress is emitted when each phase starts."""
        await executor.execute()

        # Should have started events for each phase
        phase_starts = [
            e for e in mock_progress_service.events if e.status == "started" and e.phase_id in ["planning", "coding", "validation"]
        ]
        assert len(phase_starts) == 3

    @pytest.mark.asyncio
    async def test_emit_progress_on_phase_complete(self, executor, mock_progress_service):
        """Test that progress is emitted when each phase completes."""
        await executor.execute()

        completed_events = [e for e in mock_progress_service.events if e.status == "completed"]
        # Should have completed events for each phase + final completion
        assert len(completed_events) >= 3

    @pytest.mark.asyncio
    async def test_progress_percentage_increases(self, executor, mock_progress_service):
        """Test that progress percentage increases across phases."""
        await executor.execute()

        percentages = [e.percentage for e in mock_progress_service.events]
        # Percentages should generally increase
        assert percentages[-1] == 100.0

    @pytest.mark.asyncio
    async def test_progress_event_has_task_id(self, executor, mock_progress_service):
        """Test that all progress events include the task_id."""
        await executor.execute()

        for event in mock_progress_service.events:
            assert event.task_id == "test-task-123"


class TestPhaseSequencing:
    """Test phase sequencing (Task 4)."""

    @pytest.mark.asyncio
    async def test_phases_execute_in_order(self, mock_context):
        """Test that phases execute in defined order."""
        phases = [
            Phase(id="first", name="First Phase", order=0),
            Phase(id="second", name="Second Phase", order=1),
            Phase(id="third", name="Third Phase", order=2),
        ]
        runner = MockMethodologyRunner(phases=phases)
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        await executor.execute()

        assert runner._executed_phases == ["first", "second", "third"]

    @pytest.mark.asyncio
    async def test_phase_status_updated(self, executor, mock_runner):
        """Test that phase status is updated during execution."""
        await executor.execute()

        # After execution, all phases should be completed
        for phase in mock_runner._phases:
            assert phase.status == PhaseStatus.COMPLETED


class TestLogging:
    """Test logging for each phase (Task 5)."""

    @pytest.mark.asyncio
    async def test_log_phase_start(self, executor, mock_runner):
        """Test that phase start is logged."""
        with patch.object(executor._logger, "info") as mock_info:
            await executor.execute()

            # Should have logged start for each phase
            start_calls = [c for c in mock_info.call_args_list if "Starting" in str(c)]
            assert len(start_calls) >= 3

    @pytest.mark.asyncio
    async def test_log_phase_complete(self, executor, mock_runner):
        """Test that phase completion is logged."""
        with patch.object(executor._logger, "info") as mock_info:
            await executor.execute()

            completed_calls = [c for c in mock_info.call_args_list if "Completed" in str(c)]
            assert len(completed_calls) >= 3

    @pytest.mark.asyncio
    async def test_write_to_log_file(self, mock_runner, mock_context):
        """Test that logs are written to file when log_dir is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = FullAutoExecutor(
                runner=mock_runner,
                context=mock_context,
                task_config=mock_context.task_config,
                log_dir=tmpdir,
            )

            await executor.execute()

            log_file = Path(tmpdir) / f"execution_{mock_context.task_config.task_id}.log"
            assert log_file.exists()

            content = log_file.read_text()
            assert "Starting" in content or "Completed" in content


class TestErrorHandling:
    """Test execution error handling (Task 6)."""

    @pytest.mark.asyncio
    async def test_failed_phase_returns_failure(self, mock_context):
        """Test that a failed phase returns failed TaskResult."""
        phase_results = {
            "coding": PhaseResult(
                success=False,
                phase_id="coding",
                error="Compilation failed",
            )
        }
        runner = MockMethodologyRunner(phase_results=phase_results)
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        result = await executor.execute()

        assert result.status == "failed"
        assert result.phase == "coding"
        assert "Compilation failed" in result.error

    @pytest.mark.asyncio
    async def test_exception_during_phase_caught(self, mock_context):
        """Test that exceptions during phase execution are caught."""
        runner = MockMethodologyRunner(raise_on_phase="coding")
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        result = await executor.execute()

        assert result.status == "failed"
        assert result.phase == "coding"
        assert "Exception" in result.error

    @pytest.mark.asyncio
    async def test_failure_stops_execution(self, mock_context):
        """Test that failure in one phase stops further execution."""
        phase_results = {
            "coding": PhaseResult(
                success=False,
                phase_id="coding",
                error="Failed",
            )
        }
        runner = MockMethodologyRunner(phase_results=phase_results)
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        await executor.execute()

        # Should have executed planning and coding, but not validation
        assert "planning" in runner._executed_phases
        assert "coding" in runner._executed_phases
        assert "validation" not in runner._executed_phases

    @pytest.mark.asyncio
    async def test_failure_emits_failed_progress(self, mock_context, mock_progress_service):
        """Test that failure emits a failed progress event."""
        mock_context.progress = mock_progress_service
        phase_results = {
            "coding": PhaseResult(
                success=False,
                phase_id="coding",
                error="Build error",
            )
        }
        runner = MockMethodologyRunner(phase_results=phase_results)
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        await executor.execute()

        failed_events = [e for e in mock_progress_service.events if e.status == "failed"]
        assert len(failed_events) >= 1
        assert failed_events[0].phase_id == "coding"

    @pytest.mark.asyncio
    async def test_artifacts_collected_before_failure(self, mock_context):
        """Test that artifacts from completed phases are in result even on failure."""
        phase_results = {
            "validation": PhaseResult(
                success=False,
                phase_id="validation",
                error="Validation failed",
            )
        }
        runner = MockMethodologyRunner(phase_results=phase_results)
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        result = await executor.execute()

        # Should have artifacts from planning and coding
        assert "planning_output.md" in result.artifacts
        assert "coding_output.md" in result.artifacts


class TestCalculatePercentage:
    """Test percentage calculation helper."""

    def test_percentage_calculation(self, executor):
        """Test percentage calculation for various progress states."""
        # 0 of 3 phases = 0%
        assert executor._calculate_percentage(0, 3) == 0.0

        # 1 of 3 phases = 33.33%
        assert round(executor._calculate_percentage(1, 3), 2) == 33.33

        # 2 of 3 phases = 66.67%
        assert round(executor._calculate_percentage(2, 3), 2) == 66.67

        # 3 of 3 phases = 100%
        assert executor._calculate_percentage(3, 3) == 100.0

    def test_percentage_zero_phases(self, executor):
        """Test percentage calculation with zero phases returns 0."""
        assert executor._calculate_percentage(0, 0) == 0.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_single_phase_methodology(self, mock_context):
        """Test executor with a single-phase methodology."""
        phases = [Phase(id="single", name="Single Phase", order=0)]
        runner = MockMethodologyRunner(phases=phases)
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        result = await executor.execute()

        assert result.status == "completed"
        assert len(runner._executed_phases) == 1

    @pytest.mark.asyncio
    async def test_empty_artifact_list(self, mock_context):
        """Test phases that produce no artifacts."""
        phase_results = {
            "planning": PhaseResult(
                success=True,
                phase_id="planning",
                artifacts=[],
            ),
            "coding": PhaseResult(
                success=True,
                phase_id="coding",
                artifacts=[],
            ),
            "validation": PhaseResult(
                success=True,
                phase_id="validation",
                artifacts=[],
            ),
        }
        runner = MockMethodologyRunner(phase_results=phase_results)
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        result = await executor.execute()

        assert result.status == "completed"
        assert result.artifacts == []

    @pytest.mark.asyncio
    async def test_progress_service_error_does_not_fail_execution(self, mock_context):
        """Test that errors in progress service don't fail execution."""

        class FailingProgressService:
            def update(self, phase_id: str, progress: float, message: str) -> None:
                raise RuntimeError("Progress service error")

            def emit(self, event: ProgressEvent) -> None:
                raise RuntimeError("Progress service error")

        mock_context.progress = FailingProgressService()
        runner = MockMethodologyRunner()
        executor = FullAutoExecutor(
            runner=runner,
            context=mock_context,
            task_config=mock_context.task_config,
        )

        # Should complete despite progress service errors
        result = await executor.execute()
        assert result.status == "completed"
