# Open Mission Control

**Autonomous AI agents that understand your business as deeply as your best engineers.**

[![License](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square)](./LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/KCXaPBr4Dj)

---

## What is Open Mission Control?

Open Mission Control is an **autonomous multi-agent coding framework** that combines:

- **AI Agent Orchestration** — Plan, build, and validate software with parallel AI agents
- **Business Context Layer** — Connect your CRM, support tickets, docs, and data sources
- **Persistent Memory** — Agents learn and improve across sessions via knowledge graph

The result: AI that doesn't just write code, but understands *your* business rules, *your* architecture, and *your* domain.

---

## Dual-System Architecture

Open Mission Control combines **two complementary AI systems**:

| System | Purpose | Interaction |
|--------|---------|-------------|
| **Auto-Claude** | Autonomous coding | Task in → code out (hands-off) |
| **BMAD** | Guided workflows | Menus, commands, human decisions |

### When to Use Each

**Use Auto-Claude for:**
- "Build feature X from this spec"
- "Fix this bug in the payment system"
- CI/CD integration (headless execution)
- Batch processing multiple tasks

**Use BMAD for:**
- Sprint planning sessions
- Architecture design reviews
- Story refinement with stakeholders
- Creative/innovation workshops
- Code review workflows

### How They Connect

```
BMAD (planning) → spec.md → Auto-Claude (building) → code
                     ↓
BMAD (review)   ← QA report ← Auto-Claude (QA)
```

Both systems share the **Graphiti knowledge graph**, so insights from planning sessions inform autonomous builds, and build discoveries feed back into planning.

---

## The Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPEN MISSION CONTROL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  BUSINESS LAYER  │    │   AGENT LAYER    │                  │
│  │  (Your Context)  │◄──►│  (AI Execution)  │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌──────────────────────────────────────────┐                  │
│  │           UNIFIED KNOWLEDGE GRAPH         │                  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐ │                  │
│  │  │Codebase │ │Business │ │  Operational│ │                  │
│  │  │ Memory  │ │ Context │ │    Data     │ │                  │
│  │  └─────────┘ └─────────┘ └─────────────┘ │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Autonomous Tasks** | Describe your goal; agents handle planning, implementation, and validation |
| **Parallel Execution** | Run multiple builds simultaneously with up to 12 agent terminals |
| **Isolated Workspaces** | All changes happen in git worktrees — your main branch stays safe |
| **Self-Validating QA** | Built-in quality assurance loop catches issues before you review |
| **AI-Powered Merge** | Automatic conflict resolution when integrating back to main |
| **Memory Layer** | Graphiti knowledge graph retains insights across sessions |
| **Business Connectors** | Plug in GitHub, Notion, Linear, Zoho, Jira, and more |
| **Cross-Platform** | Native desktop apps for Windows, macOS, and Linux |

---

## Deployment Options

Open Mission Control is the **open source core**. Deploy it as:

| Deployment | Description |
|------------|-------------|
| `open-mission-control` | Generic open source version (this repo) |
| `follosoft-mission-control` | Configured for Follosoft's snow removal SaaS |
| `blend-mission-control` | Configured for Blend e-commerce |
| `[yourcompany]-mission-control` | Your own business context |

---

## Requirements

- **Claude Pro/Max subscription** — [Get one here](https://claude.ai/upgrade)
- **Claude Code CLI** — `npm install -g @anthropic-ai/claude-code`
- **Git repository** — Your project must be initialized as a git repo
- **Python 3.12+** — For the backend agent system

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/wecodesaas/open-mission-control.git
cd open-mission-control

# Install dependencies
npm run install:all

# Configure authentication
claude setup-token

# Start the app
npm run dev
```

---

## Project Structure

```
open-mission-control/
├── apps/
│   ├── backend/     # Auto-Claude engine (Python agents, QA pipeline)
│   └── frontend/    # Electron desktop application
├── _bmad/           # BMAD framework (guided workflows)
│   ├── core/        # Core agents + party mode
│   ├── bmm/         # Software dev (34 workflows, 4 phases)
│   ├── bmb/         # Builder (custom agents/modules)
│   └── cis/         # Creative/innovation module
├── guides/          # Additional documentation
├── tests/           # Test suite
└── scripts/         # Build utilities
```

---

## CLI Usage

For headless operation, CI/CD integration, or terminal-only workflows:

```bash
cd apps/backend

# Create a spec interactively
python spec_runner.py --interactive

# Run autonomous build
python run.py --spec 001

# Review and merge
python run.py --spec 001 --review
python run.py --spec 001 --merge
```

See [guides/CLI-USAGE.md](guides/CLI-USAGE.md) for complete CLI documentation.

---

## BMAD Workflows

BMAD provides guided, menu-driven AI workflows for planning and architecture:

```bash
# Start a BMAD session (invoke bmad-master agent in Claude Code)
# The agent will present menus for:
# - Sprint planning
# - Architecture reviews
# - Story refinement
# - Creative brainstorming

# BMAD outputs go to:
_bmad-output/
```

BMAD includes 21+ specialized agents and 34 workflows across 4 development phases. See the [BMAD documentation](_bmad/README.md) for details.

---

## Connecting Business Context

Open Mission Control supports pluggable data sources via MCP (Model Context Protocol):

```bash
# Configure connectors in apps/backend/.env

# GitHub Issues
GITHUB_TOKEN=ghp_xxxxx

# Notion
NOTION_TOKEN=secret_xxxxx

# Linear
LINEAR_API_KEY=lin_api_xxxxx

# Zoho (CRM, Desk, Books)
ZOHO_CLIENT_ID=xxxxx
ZOHO_CLIENT_SECRET=xxxxx
```

The more context you connect, the smarter your agents become.

---

## Development

```bash
# Run in development mode
npm run dev

# Run tests
npm test
npm run test:backend

# Lint
npm run lint

# Package for distribution
npm run package
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete development setup.

---

## Security

Open Mission Control uses a three-layer security model:

1. **OS Sandbox** — Bash commands run in isolation
2. **Filesystem Restrictions** — Operations limited to project directory
3. **Dynamic Command Allowlist** — Only approved commands based on detected project stack

---

## Roadmap

- [x] **Phase 0**: Dual-system architecture (BMAD + Auto-Claude integration)
- [ ] **Phase 1**: Unified knowledge graph (Graphiti + business entities)
- [ ] **Phase 2**: Shared knowledge layer (BMAD ↔ Graphiti bridge)
- [ ] **Phase 3**: UI integration (Planning Mode vs Build Mode toggle)
- [ ] **Phase 4**: Semantic search across all connected sources
- [ ] **Phase 5**: SaaS offering with managed connectors

---

## Community

- **Discord** — [Join our community](https://discord.gg/KCXaPBr4Dj)
- **Issues** — [Report bugs or request features](https://github.com/wecodesaas/open-mission-control/issues)
- **Discussions** — [Ask questions](https://github.com/wecodesaas/open-mission-control/discussions)

---

## License

**Apache 2.0** — See [LICENSE](./LICENSE)

Open Mission Control is free to use, modify, and distribute. Commercial use is welcome.

---

## Acknowledgments

Open Mission Control builds on two excellent foundations:
- **[Auto-Claude](https://github.com/AndyMik90/Auto-Claude)** by Andre Mikalsen — autonomous agent orchestration
- **[BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)** by BMAD Code Org — guided workflow framework

We're grateful to both projects for the foundations they provide.

---

## Star History

[![GitHub Repo stars](https://img.shields.io/github/stars/wecodesaas/open-mission-control?style=social)](https://github.com/wecodesaas/open-mission-control/stargazers)
