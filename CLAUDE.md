# Claude Code Guide for Personal Investment System

## Dual Repository Setup

**IMPORTANT**: This project exists in TWO repositories. Read this section first.

| Repository | Type | Location | GitHub |
|------------|------|----------|--------|
| **Open Source** (this repo) | Public | `/Users/ray/Documents/personal_investment_system` | `github.com/SunnRayy/personal_investment_system_opensource` |
| **Legacy** | Private/Personal | `/Users/ray/Documents/personal_investment_system Legacy` | `github.com/SunnRayy/personal_investment_system` |

### Workflow Rules

1. **Develop new features HERE** (Open Source) using demo data in `data/demo_source/`
2. **Sync features TO Legacy** using `~/bin/sync-investment-repos.sh`
3. **NEVER include personal financial data** in this repository
4. **Personal-only features** go in Legacy repo with `personal/` branch prefix

### Before Any Commit

```bash
# Verify you're in the correct repo
git remote -v | grep opensource  # Should match for this repo
```

For complete AI agent instructions, see: `~/Documents/Investment_System_AI_Agent_Instructions.md`

---

## Project Overview

A comprehensive Python system for tracking, analyzing, and optimizing personal investments. Features multi-source data integration, portfolio analytics, Monte Carlo simulations, and HTML reporting.

**Architecture**: `Excel/CSV → DataManager → Analysis Modules → Unified Engine → Reports`

```
src/
├── data_manager/           # Central data hub - ALL modules depend on this
├── financial_analysis/     # Balance sheet, cash flow, XIRR calculations
├── portfolio_lib/          # Asset taxonomy, MPT optimization, risk analytics
├── investment_optimization/ # Market regime detection
├── performance_attribution/ # Brinson-Fachler attribution
├── goal_planning/          # Monte Carlo simulation, goal tracking
├── recommendation_engine/  # Intelligent advice generation
├── unified_analysis/       # Main orchestrator (FinancialAnalysisEngine)
├── report_generators/      # HTML report generation
└── web_app/               # Flask app (avoid unless requested)
```

## Critical Rules

### File Organization

- **Core logic**: `.py` files in `src/` only
- **Documentation**: `docs/` subdirectories
- **Tests**: `tests/` directory
- **Notebooks**: Orchestration/visualization only, never core logic

### Documentation File Locations

| File Type | Location | Purpose |
|-----------|----------|---------|
| **System-level docs** | Project root (`/`) | `CHANGELOG.md`, `architecture.md`, `project-status.md` |
| **Feature/project docs** | `docs/<feature>/` | `task_plan.md`, `notes.md`, `implementation.md` |
| **API documentation** | `docs/api/` | Module and function reference |
| **User guides** | `docs/guides/` | How-to and tutorials |

### Code Quality

- Type hints on all function signatures
- Docstrings on all public functions
- Keep files under 300 lines (refactor at 500)
- Use absolute imports from `src/`
- Follow existing patterns - check similar files first

### Prohibitions

- **NEVER** modify `development_log.md` unless explicitly asked
- **NEVER** include personal financial data in commits (amounts, account numbers)
- **NEVER** commit files with user specific settings (use `.example` templates)
- **NEVER** create new `run_*.py` scripts - use `main.py` CLI
- **NEVER** add features without user approval

### Backup Requirement

Before modifying non-Git-tracked files (Excel, CSV, databases), create backup:

```python
# Pattern: data/backups/{filename}_backup_{YYYYMMDD_HHMMSS}.{ext}
```

## Key Patterns

### Entry Point

```bash
python main.py run-all              # Complete analysis pipeline
python main.py generate-report      # HTML report only
python main.py update-funds         # Process fund data
python main.py --help               # All commands
```

### Standard Integration

```python
from src.data_manager.manager import DataManager
from src.portfolio_lib.data_integration import PortfolioAnalysisManager
from src.unified_analysis.engine import FinancialAnalysisEngine

# Always initialize DataManager first
data_manager = DataManager(config_path='config/settings.yaml')
engine = FinancialAnalysisEngine(config_path='config/settings.yaml')
results = engine.run_complete_analysis()
```

### Configuration Files

- `config/settings.yaml` - File paths, Excel sheet mappings
- `config/asset_taxonomy.yaml` - **PRIMARY** asset classification (single source of truth)
- `config/benchmark.yaml` - Performance benchmarks
- `config/goals.yaml` - Investment goals

**Note**: `investment_config.yaml` is deprecated - always use `asset_taxonomy.yaml`

## Git Workflow

### Session Start

```bash
git status && git branch --show-current && git log --oneline -3
```

### Pre-Commit Checklist

1. Correct branch? (`main` for fixes, `feature/*` for WIP)
2. Expected files only? (match session work)
3. No personal data? (scan for amounts, account numbers)
4. Sanitized message? (no financial values)
5. **Documentation updated?** (see below)

### Documentation Update Rule (MANDATORY)

**Before every git push/sync, update these files:**

1. **`CHANGELOG.md`** - For open source users
   - Add entry under `[Unreleased]` section
   - Use categories: Added, Changed, Fixed, Removed
   - Keep entries concise and user-focused
   - Move to versioned section on release

2. **`development_log.md`** - For internal development context
   - More detailed technical notes
   - Architecture decisions and rationale
   - Debugging insights and lessons learned

**Format for CHANGELOG entries:**

```markdown
## [Unreleased]

### Added
- Feature description (brief, user-facing)

### Fixed
- Bug fix description
```

**When to version:** Create new version (e.g., `[1.1.0]`) for:

- Major feature completions
- Breaking changes
- Significant milestones

### Commit Message Format

```
<type>: <summary>

- Detail 1
- Detail 2
```

Types: `fix:`, `feat:`, `docs:`, `refactor:`, `test:`

### Branch Strategy

- `main` - Completed, tested code only
- `feature/<name>` - Work in progress
- `fix/<name>` - Bug fixes
- `experimental/<name>` - Exploration

## Common Debugging

1. **Path issues**: Ensure working directory is project root
2. **Excel errors**: Verify sheet names match `settings.yaml`
3. **Import errors**: Use `sys.path.insert(0, project_root)` in entry points
4. **XIRR failures**: Need inflows (negative) + outflows (positive), min 2 points
5. **Asset classification**: Check patterns in `asset_taxonomy.yaml`

## Development Context

Primary context sources:

- `development_log.md` - Detailed project history and technical decisions
- `CHANGELOG.md` - User-facing version history (update before every push)
- `docs/` - Feature-specific documentation

When implementing features:

1. Check existing patterns in similar modules
2. Add to appropriate `src/` subdirectory
3. Integrate via `unified_analysis/` if system-wide
4. Update `main.py` CLI if user-facing
5. Add tests in `tests/`
6. Test with `python main.py run-all`

## Continuous Documentation (Auto-Update)

**During development, automatically maintain these system documents:**

### System-Level Documents (Project Root)

| Document | Update When | Content |
|----------|-------------|---------|
| `architecture.md` | Architecture changes | System design, module relationships, data flow |
| `CHANGELOG.md` | Any user-facing change | Version history following Keep a Changelog format |
| `project-status.md` | End of each session | Current progress, next steps, blockers |

### Update Triggers

- **architecture.md**: New modules, changed dependencies, refactored components
- **CHANGELOG.md**: Before every commit (see Git Workflow section)
- **project-status.md**: Before context compression, session end, or task handoff

## Context Window Management

**The context window will auto-compress when approaching token limits.**

### Before Context Refresh (MANDATORY)

1. **Save progress to `project-status.md`:**

   ```markdown
   ## Current Status - [DATE]

   ### Completed
   - [List of completed tasks]

   ### In Progress
   - [Current task and its state]
   - [Files being modified]

   ### Next Steps
   - [Immediate next actions]
   - [Remaining tasks]

   ### Important Context
   - [Key decisions made]
   - [Blockers or issues encountered]
   ```

2. **Commit or stash work-in-progress**
3. **Update relevant feature docs if mid-project**

### Autonomy Principle

- Always persist work to survive context refresh
- Complete tasks as far as possible before stopping
- Leave clear breadcrumbs for continuation

## Complex Project Documentation

**For multi-session features or complex projects, create a dedicated folder:**

```
docs/<feature-name>/
├── task_plan.md      # Phases, milestones, progress tracking
├── notes.md          # Research findings, design decisions, alternatives considered
└── implementation.md # Final specs, API docs, usage examples
```

### task_plan.md Template

```markdown
# Feature: [Name]

## Overview
Brief description and goals

## Phases
### Phase 1: [Name]
- [ ] Task 1
- [x] Task 2 (completed)
- [ ] Task 3

### Phase 2: [Name]
- [ ] Task 4

## Progress Log
| Date | Progress | Next |
|------|----------|------|
| YYYY-MM-DD | Completed X | Start Y |

## Blockers
- [Any current blockers]
```

### notes.md Template

```markdown
# Research Notes: [Feature]

## Key Findings
- Finding 1
- Finding 2

## Design Decisions
| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| Choice A | Reason | Option B, Option C |

## References
- [Links, docs, examples]
```

### implementation.md Template

```markdown
# Implementation: [Feature]

## Architecture
[How it fits into the system]

## API Reference
[Functions, classes, parameters]

## Usage Examples
[Code samples]

## Testing
[How to verify it works]
```

### When to Create Feature Docs

- Feature spans multiple sessions
- Multiple developers may work on it
- Complex enough to need research phase
- Requires design decisions with trade-offs
