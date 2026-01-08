# Specification: Full Autonomous PR Review and Fix System

## Overview

This feature implements a comprehensive autonomous PR review and fix system that automatically reviews PRs after QA passes, waits for CI and external bot checks (CodeRabbit, Cursor, etc.), performs internal AI review, and iteratively fixes issues until the PR is ready for human approval. **The system NEVER auto-merges** - the final state is "Ready for Human Review" where a human must explicitly approve and merge. This addresses the need for end-to-end automation while maintaining human control over the merge decision.

## Workflow Type

**Type**: feature

**Rationale**: This is a major new feature adding significant functionality across both backend (Python) and frontend (TypeScript/Electron). It requires new state machine states, new agents, new security infrastructure, new IPC handlers, and new UI components. The estimated effort is 6-8 weeks for production-ready implementation.

## Task Scope

### Services Involved
- **backend** (primary) - Core orchestration, state machine, agents, security
- **frontend** (integration) - UI components, IPC handlers, progress display

### This Task Will:
- [ ] Extend `IssueLifecycleState` enum with 3 new states: `PR_AWAITING_CHECKS`, `PR_FIXING`, `PR_READY_TO_MERGE`
- [ ] Add valid state transitions for the new PR review loop flow
- [ ] Add 7 new audit events for PR review operations
- [ ] Create security infrastructure: `InputSanitizer`, `PermissionManager`, `BotVerifier`
- [ ] Create backend infrastructure: `PRReviewOrchestratorState`, `PRCheckWaiter`, `PRFixerAgent`, `AutoPRReviewOrchestrator`
- [ ] Create `FrontendStateAdapter` to map backend state to frontend
- [ ] Add `pr_fixer` agent type to `core/client.py`
- [ ] Create frontend hook `useAutoPRReview.ts` with cancellation support
- [ ] Create `AutoPRReviewProgressCard.tsx` with rich progress UI
- [ ] Add Auto-PR-Review toggle to `IssueListHeader.tsx`
- [ ] Add IPC handlers for Auto-PR-Review operations
- [ ] Add i18n translation keys for all new UI text
- [ ] Add structured logging with correlation IDs
- [ ] Add comprehensive unit, integration, and edge case tests

### Out of Scope:
- Auto-merge functionality (explicitly forbidden - human approval required)
- Changes to existing Auto-Fix Issues flow (this is a separate feature)
- External webhook integrations (uses existing GitHub CLI approach)
- Multi-tenant/multi-organization support

## Service Context

### Backend Service

**Tech Stack:**
- Language: Python 3.12+
- Framework: None (CLI-based)
- Key dependencies: claude-agent-sdk, pydantic, python-dotenv

**Key Directories:**
- `apps/backend/runners/github/` - GitHub integration code
- `apps/backend/agents/` - Agent implementations
- `apps/backend/core/` - Client factory, auth, security
- `apps/backend/prompts/` - Agent system prompts

**Entry Point:** `apps/backend/run.py`

**How to Run:**
```bash
cd apps/backend
python run.py --spec 001
```

### Frontend Service

**Tech Stack:**
- Language: TypeScript
- Framework: React + Electron
- Build: Vite
- State: Zustand
- Styling: Tailwind CSS
- Testing: Vitest, Playwright

**Key Directories:**
- `apps/frontend/src/renderer/components/github-issues/` - GitHub UI components
- `apps/frontend/src/main/ipc-handlers/github/` - IPC handlers
- `apps/frontend/src/shared/i18n/locales/` - Translation files

**Entry Point:** `apps/frontend/src/main/index.ts`

**How to Run:**
```bash
npm run dev  # From project root
```

**Port:** 3000 (renderer), 9222 (Electron debug)

## Files to Modify

| File | Service | What to Change |
|------|---------|---------------|
| `apps/backend/runners/github/lifecycle.py` | backend | Add 3 new states to `IssueLifecycleState` enum, extend `VALID_TRANSITIONS` |
| `apps/backend/runners/github/audit.py` | backend | Add 7 new `AuditAction` enum values for PR review events |
| `apps/backend/agents/tools_pkg/models.py` | backend | Add `pr_fixer` to AGENT_CONFIGS registry (single source of truth for agent tool permissions) |
| `apps/backend/core/client.py` | backend | Verify `pr_fixer` agent type works with `get_agent_config()` (reads from AGENT_CONFIGS) |
| `apps/backend/requirements.txt` | backend | Add structlog>=25.5.0, pybreaker>=1.3.0, filelock>=3.20.0 |
| `apps/frontend/src/main/ipc-handlers/github/autofix-handlers.ts` | frontend | Add 5 new IPC handlers for Auto-PR-Review |
| `apps/frontend/src/shared/constants.ts` | frontend | Add new IPC channel constants |
| `apps/frontend/src/preload/api/modules/github-api.ts` | frontend | Extend types for Auto-PR-Review |
| `apps/frontend/src/renderer/components/github-issues/components/IssueListHeader.tsx` | frontend | Add Auto-PR-Review toggle |
| `apps/frontend/src/renderer/components/github-issues/types.ts` | frontend | Extend AutoFixQueueItem type |
| `apps/frontend/src/shared/i18n/locales/en/github.json` | frontend | Add translation keys |
| `apps/frontend/src/shared/i18n/locales/fr/github.json` | frontend | Add translation keys |

## Files to Create

| File | Service | Purpose |
|------|---------|---------|
| `apps/backend/runners/github/security/input_sanitizer.py` | backend | Extend existing `ContentSanitizer` from `sanitize.py`; add file path validation, dangerous Unicode stripping |
| `apps/backend/runners/github/security/permission_manager.py` | backend | Authorization checks against allowlist |
| `apps/backend/runners/github/services/bot_verifier.py` | backend | Verify bot identity by account ID |
| `apps/backend/runners/github/models/pr_review_state.py` | backend | Durable state for crash recovery |
| `apps/backend/runners/github/services/pr_check_waiter.py` | backend | Poll checks with pybreaker CircuitBreaker; reuse patterns from existing `rate_limiter.py` for exponential backoff |
| `apps/backend/runners/github/services/auto_pr_review_orchestrator.py` | backend | Main orchestration loop |
| `apps/backend/runners/github/adapters/frontend_state.py` | backend | Map IssueLifecycle to frontend format |
| `apps/backend/agents/pr_fixer.py` | backend | Fix PR findings with safety constraints |
| `apps/backend/prompts/github/pr_fixer.md` | backend | System prompt for PR fixer agent |
| `apps/frontend/src/renderer/components/github-issues/hooks/useAutoPRReview.ts` | frontend | Hook with cancellation support |
| `apps/frontend/src/renderer/components/github-issues/components/AutoPRReviewProgressCard.tsx` | frontend | Rich progress UI component |

## Files to Reference

These files show patterns to follow:

| File | Pattern to Copy |
|------|----------------|
| `apps/backend/runners/github/lifecycle.py` | State machine enum, transitions, locking patterns |
| `apps/backend/runners/github/audit.py` | Audit action enum, structured logging patterns |
| `apps/backend/core/client.py` | Agent type registration, create_client() factory |
| `apps/backend/agents/coder.py` | Agent implementation pattern with create_client() |
| `apps/backend/runners/github/services/autofix_processor.py` | Service orchestration patterns |
| `apps/backend/runners/github/sanitize.py` | ContentSanitizer for prompt injection protection (extend for InputSanitizer) |
| `apps/backend/runners/github/rate_limiter.py` | TokenBucket + exponential backoff patterns (reuse for PRCheckWaiter) |
| `apps/backend/agents/tools_pkg/models.py` | AGENT_CONFIGS registry pattern for agent tool permissions |
| `apps/frontend/src/renderer/components/github-issues/hooks/useAutoFix.ts` | Frontend hook pattern with IPC |

## Patterns to Follow

### State Machine Extension Pattern

From `apps/backend/runners/github/lifecycle.py`:

```python
class IssueLifecycleState(str, Enum):
    """Unified issue lifecycle states."""
    # Existing states...
    PR_CREATED = "pr_created"
    PR_REVIEWING = "pr_reviewing"
    # NEW states to add:
    PR_AWAITING_CHECKS = "pr_awaiting_checks"  # Wait for CI + external bots
    PR_FIXING = "pr_fixing"                     # Apply fixes from findings
    PR_READY_TO_MERGE = "pr_ready_to_merge"    # Human approval required

VALID_TRANSITIONS: dict[IssueLifecycleState, set[IssueLifecycleState]] = {
    # ... existing transitions ...
    IssueLifecycleState.PR_CREATED: {
        IssueLifecycleState.PR_AWAITING_CHECKS,  # NEW transition
        IssueLifecycleState.CLOSED,
    },
    # NEW transitions:
    IssueLifecycleState.PR_AWAITING_CHECKS: {
        IssueLifecycleState.PR_REVIEWING,
        IssueLifecycleState.PR_FIXING,  # CI fail goes to fixing
    },
    IssueLifecycleState.PR_FIXING: {
        IssueLifecycleState.PR_AWAITING_CHECKS,  # Loop back after push
    },
    IssueLifecycleState.PR_READY_TO_MERGE: {
        IssueLifecycleState.MERGED,
        IssueLifecycleState.CLOSED,
    },
}
```

**Key Points:**
- States use snake_case string values
- Transitions are defined as sets for O(1) lookup
- Terminal states have empty transition sets

### Audit Event Pattern

From `apps/backend/runners/github/audit.py`:

```python
class AuditAction(str, Enum):
    # ... existing ...
    # NEW PR Review events to add:
    PR_REVIEW_LOOP_STARTED = "pr_review_loop_started"
    PR_REVIEW_LOOP_ITERATION = "pr_review_loop_iteration"
    PR_FIXER_STARTED = "pr_fixer_started"
    PR_FIXER_CHANGES_APPLIED = "pr_fixer_changes_applied"
    EXTERNAL_BOT_COMMENT_TRUSTED = "external_bot_comment_trusted"
    PERMISSION_CHECK_PASSED = "permission_check_passed"
    PERMISSION_CHECK_DENIED = "permission_check_denied"
```

**Key Points:**
- Event names are descriptive snake_case
- Pair started/completed/failed events for tracking
- Include context in audit log details

### Agent Type Registration Pattern

From `apps/backend/agents/tools_pkg/models.py` (AGENT_CONFIGS is the single source of truth):

```python
# Add to AGENT_CONFIGS dictionary in models.py:
AGENT_CONFIGS = {
    # ... existing configs ...
    "pr_fixer": {
        "tools": BASE_READ_TOOLS + BASE_WRITE_TOOLS + WEB_TOOLS,
        "mcp_servers": ["context7", "graphiti", "auto-claude"],
        "mcp_servers_optional": ["linear"],
        "auto_claude_tools": [
            TOOL_GET_BUILD_PROGRESS,
            TOOL_GET_SESSION_CONTEXT,
            TOOL_RECORD_GOTCHA,
        ],
        "thinking_default": "medium",
    },
}
```

From `apps/backend/core/client.py` (uses AGENT_CONFIGS via `get_agent_config()`):

```python
def create_client(
    project_dir: Path,
    spec_dir: Path,
    model: str,
    agent_type: str = "coder",  # "pr_fixer" uses get_agent_config() from models.py
    max_thinking_tokens: int | None = None,
    ...
) -> ClaudeSDKClient:
    # Get allowed tools using phase-aware configuration from AGENT_CONFIGS
    allowed_tools_list = get_allowed_tools(
        agent_type,  # Must exist in AGENT_CONFIGS
        project_capabilities,
        linear_enabled,
        mcp_config,
    )
```

**Key Points:**
- **CRITICAL**: Add `pr_fixer` to `agents/tools_pkg/models.py` AGENT_CONFIGS first
- AGENT_CONFIGS is the single source of truth for agent tool permissions
- `get_agent_config()` reads from AGENT_CONFIGS to determine tools/MCP servers
- Use `create_client()` factory - NEVER use Anthropic API directly

### Frontend i18n Pattern

From `apps/frontend/src/shared/i18n/locales/en/github.json`:

```json
{
  "autoPRReview": {
    "title": "Auto-PR-Review",
    "tooltip": "Automatically review PRs and fix issues until ready to merge",
    "requiresAutoFix": "Enable Auto-Fix first",
    "status": {
      "awaiting_checks": "Waiting for Checks",
      "pr_reviewing": "AI Reviewing",
      "pr_fixing": "Fixing Issues",
      "pr_ready_to_merge": "Ready to Merge",
      "cancelled": "Cancelled"
    }
  }
}
```

**Key Points:**
- ALL user-facing text MUST use translation keys per CLAUDE.md
- Format: `t('namespace:section.key')`
- Add to both `en` and `fr` locales

## Requirements

### Functional Requirements

1. **State Machine Extension**
   - Description: Add 3 new states to `IssueLifecycleState` enum for PR review loop
   - Acceptance: New states visible in lifecycle transitions, valid transitions enforced

2. **Security Infrastructure**
   - Description: Create `InputSanitizer` to remove prompt injection patterns, validate file paths
   - Acceptance: Sanitizer blocks dangerous Unicode, path traversal, limits content to 10K chars

3. **Permission Manager**
   - Description: Check `GITHUB_AUTO_PR_REVIEW_ALLOWED_USERS` env var for authorization
   - Acceptance: Only allowlisted users can trigger auto-PR-review, all decisions logged

4. **Bot Identity Verification**
   - Description: Verify external bot comments by account ID, not just name
   - Acceptance: Bot comments verified before processing, suspicious comments rejected

5. **PR Check Waiter**
   - Description: Poll CI/bot checks with pybreaker `CircuitBreaker(fail_max=3, reset_timeout=300)` + exponential backoff (60s base, 300s max)
   - Acceptance: Graceful handling of sustained API failures, PR open check at each poll

6. **PR Fixer Agent**
   - Description: Fix PR findings with safety constraints - only modify files in original PR diff
   - Acceptance: Agent respects file scope constraints, validates syntax before applying

7. **Auto-PR-Review Orchestrator**
   - Description: Main orchestration with state persistence for crash recovery
   - Acceptance: Orchestrator resumes from last checkpoint after crash, max 5 iterations enforced

8. **Frontend State Adapter**
   - Description: Map `IssueLifecycle` to `AutoFixQueueItem` frontend format
   - Acceptance: Frontend displays accurate status from backend state machine

9. **Progress UI**
   - Description: Rich progress card with iteration count, elapsed time, CI status, bot status
   - Acceptance: Real-time progress updates via IPC, accessible with ARIA labels

10. **Cancellation Support**
    - Description: Graceful cancellation with cleanup via `CancellationToken`
    - Acceptance: Cancel button works, resources cleaned up, state persisted

11. **Human Approval Required**
    - Description: System NEVER auto-merges - final state is "Ready for Human Review"
    - Acceptance: Merge button only enabled by human, no auto-merge code paths

### Edge Cases

1. **PR Closed During Review** - Detect PR closure at each poll iteration, exit gracefully with cleanup
2. **PR Merged Externally** - Detect merged status, transition to COMPLETED state
3. **CI Never Completes** - Timeout after 30 minutes, transition to failed state with user notification
4. **Bot Never Comments** - Timeout after 15 minutes, proceed with available findings
5. **Fixer Creates Invalid Code** - Detect syntax errors via validation, retry or fail after 3 attempts
6. **Force Push During Review** - Detect SHA mismatch, restart review from current state
7. **User Pushes During Fixing** - Handle merge conflicts gracefully, notify user
8. **Max Iterations Reached** - Stop after 5 iterations, mark for manual intervention
9. **Concurrent PR Reviews** - Semaphore limit (3 concurrent), queue additional requests

## Implementation Notes

### DO
- Follow the state machine pattern in `lifecycle.py` for new states
- Use `LifecycleManager.acquire_lock()` before ANY orchestrator operations
- Use `create_client()` from `core/client.py` with agent_type="pr_fixer"
- **Add `pr_fixer` to `agents/tools_pkg/models.py` AGENT_CONFIGS first** (single source of truth)
- Add structured logging with correlation IDs via structlog (`from structlog import get_logger`)
- Use `filelock.FileLock` for atomic state file writes (`from filelock import FileLock`)
- Use `pybreaker.CircuitBreaker` for API resilience (`from pybreaker import CircuitBreaker, CircuitBreakerError`)
- **Extend existing `ContentSanitizer` from `sanitize.py`** for InputSanitizer
- **Reuse patterns from `rate_limiter.py`** for exponential backoff in PRCheckWaiter
- Use translation keys for ALL frontend text per CLAUDE.md
- Persist state to disk for crash recovery

### DON'T
- Create dual state systems - `IssueLifecycle` is the SINGLE source of truth
- Use Anthropic API directly - always use `create_client()` wrapper
- Auto-merge PRs - ALWAYS require human approval
- Trust bot comments by name alone - verify by account ID
- Allow PR fixer to modify files outside the original PR diff
- Skip locking - race conditions cause data corruption
- Hardcode frontend strings - always use i18n translation keys

## Development Environment

### Start Services

```bash
# Backend (from apps/backend/)
cd apps/backend
python run.py --spec 001

# Frontend (from project root)
npm run dev
```

### Service URLs
- Frontend: http://localhost:3000
- Electron Debug: http://localhost:9222

### Required Environment Variables
- `CLAUDE_CODE_OAUTH_TOKEN`: OAuth token for Claude SDK authentication
- `GRAPHITI_ENABLED`: Enable memory system (default: true)
- `GITHUB_TOKEN`: GitHub API token for CLI operations
- `GITHUB_AUTO_PR_REVIEW_ALLOWED_USERS`: Comma-separated list of authorized usernames

### New Dependencies to Install
```bash
cd apps/backend
pip install structlog>=25.5.0 pybreaker>=1.3.0 filelock>=3.20.0
```

## Success Criteria

The task is complete when:

1. [ ] `IssueLifecycleState` enum has 3 new states: `PR_AWAITING_CHECKS`, `PR_FIXING`, `PR_READY_TO_MERGE`
2. [ ] `VALID_TRANSITIONS` includes all new state transitions
3. [ ] `AuditAction` enum has 7 new PR review events
4. [ ] `InputSanitizer` blocks prompt injection, path traversal, dangerous Unicode
5. [ ] `PermissionManager` enforces allowlist authorization
6. [ ] `BotVerifier` validates bot identity by account ID
7. [ ] `PRCheckWaiter` polls with circuit breaker and exponential backoff
8. [ ] `PRFixerAgent` fixes findings within file scope constraints
9. [ ] `AutoPRReviewOrchestrator` runs full loop with crash recovery
10. [ ] `pr_fixer` agent type registered in `agents/tools_pkg/models.py` AGENT_CONFIGS
11. [ ] `FrontendStateAdapter` maps backend state to frontend format
12. [ ] `useAutoPRReview.ts` hook works with IPC
13. [ ] `AutoPRReviewProgressCard.tsx` displays rich progress
14. [ ] Auto-PR-Review toggle visible in `IssueListHeader.tsx`
15. [ ] i18n keys added to both `en/github.json` and `fr/github.json`
16. [ ] IPC handlers implemented for all Auto-PR-Review operations
17. [ ] System NEVER auto-merges - requires human approval
18. [ ] No console errors during operation
19. [ ] Existing tests still pass
20. [ ] New unit tests cover all edge cases

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| State Machine Transitions | `tests/test_lifecycle.py` | New states and transitions are valid, invalid transitions rejected |
| Input Sanitizer | `tests/test_input_sanitizer.py` | Prompt injection blocked, path traversal blocked, content limited |
| Permission Manager | `tests/test_permission_manager.py` | Allowlist enforced, denials logged |
| Bot Verifier | `tests/test_bot_verifier.py` | Account ID verification works, suspicious bots rejected |
| PR Check Waiter | `tests/test_pr_check_waiter.py` | Circuit breaker triggers, backoff works, timeout handling |
| PR Fixer Agent | `tests/test_pr_fixer.py` | File scope constraints enforced, syntax validation works |
| Orchestrator | `tests/test_auto_pr_review_orchestrator.py` | State persistence, crash recovery, max iterations |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| Full Review Loop | backend | Issue -> Build -> QA -> PR -> Review -> Ready flow works |
| Frontend State Sync | backend + frontend | State adapter maps correctly, UI updates in real-time |
| Cancellation Flow | backend + frontend | Cancel stops orchestrator, resources cleaned up |
| Crash Recovery | backend | Kill mid-loop, verify resume from checkpoint |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| Happy Path | 1. Create issue 2. Auto-fix builds 3. QA passes 4. PR created 5. Checks pass 6. Review clean | Status shows "Ready to Merge", merge button enabled |
| Fix Loop | 1. PR has findings 2. Fixer applies changes 3. Re-push 4. Re-check | Iteration count increases, findings resolved |
| Max Iterations | 1. PR has unfixable issues 2. Loop 5 times | Status shows "Manual Intervention Required" |
| Cancellation | 1. Start review 2. Click Cancel | Status shows "Cancelled", no orphaned processes |

### Browser Verification (Frontend)
| Page/Component | URL | Checks |
|----------------|-----|--------|
| Auto-PR-Review Toggle | `http://localhost:3000/#github-issues` | Toggle visible next to Auto-Fix, tooltip shows |
| Progress Card | `http://localhost:3000/#github-issues` | Iteration count, elapsed time, CI status, bot badges visible |
| Cancel Button | `http://localhost:3000/#github-issues` | Confirmation dialog appears, cancel works |
| Error Recovery | `http://localhost:3000/#github-issues` | Error card shows with recovery actions |

### Database/State Verification
| Check | Query/Command | Expected |
|-------|---------------|----------|
| State Persisted | `cat .auto-claude/github/pr_review_state/pr_*.json` | State file exists with valid JSON |
| Audit Logged | `cat .auto-claude/github/audit/audit_*.jsonl` | PR review events logged with correlation IDs |
| Lifecycle Updated | `cat .auto-claude/github/lifecycle/*.json` | State matches expected lifecycle phase |

### QA Sign-off Requirements
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Browser verification complete
- [ ] State persistence verified
- [ ] No regressions in existing Auto-Fix functionality
- [ ] Code follows established patterns
- [ ] No security vulnerabilities introduced
- [ ] System NEVER auto-merges (critical security check)
- [ ] i18n keys present in both en and fr locales
- [ ] Accessibility verified (ARIA labels, keyboard navigation)

## Configuration Defaults

```json
{
  "autoPRReviewEnabled": false,
  "autoPRReviewConfig": {
    "maxPRReviewIterations": 5,
    "ciCheckTimeout": 1800000,
    "externalBotTimeout": 900000,
    "pollInterval": 60000,
    "requireHumanApproval": true,
    "allowedUsers": []
  }
}
```

## Risk Mitigations

| Risk | Mitigation | Implementation |
|------|------------|----------------|
| Dual state systems | Single source of truth | Use `IssueLifecycle` only, frontend adapter |
| Race conditions | Mandatory locking | `LifecycleManager.acquire_lock()` |
| Crash during loop | State persistence | `PRReviewOrchestratorState.save()` |
| Rate limit exhaustion | Circuit breaker | `pybreaker.CircuitBreaker` in `PRCheckWaiter` |
| Prompt injection | Input sanitization | `InputSanitizer` class |
| Unauthorized access | Permission manager | `PermissionManager` with allowlist |
| Auto-merge danger | Human approval required | No auto-merge code paths |
| Silent failures | Structured logging | `structlog` with correlation IDs |
