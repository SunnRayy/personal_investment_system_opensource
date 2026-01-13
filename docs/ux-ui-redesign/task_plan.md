# Feature: UX/UI Redesign

## Overview

Complete redesign of the Personal Investment System UI following `docs/design-framework.md` and the "SunnRayy" visual identity.

## Phases

### Phase 1: Design System Foundation ✅

- [x] Create `design-tokens.css` with SunnRayy palette
- [x] Update `style.css` to use CSS variables
- [x] Update `base.html` with new navigation
- [x] Create `components.html` Jinja2 macros
- [x] Add comprehensive component CSS (cards, buttons, forms, tables, badges)
- [x] Verify with test page

### Phase 2: High-Impact Pages ✅

- [x] Redesign Dashboard (`/`)
- [x] Redesign Wealth Overview (`/wealth`)
- [x] Redesign Logic Studio (`/logic-studio`)
- [x] Test responsive layouts
- [x] Verified with browser screenshot

### Phase 3: Template Migration (BLOCKED)

- [x] Migrate Data Workbench (`/workbench/`) CSS classes from Tailwind to design system
- [x] **Redesign Data Workbench UI** (Import Wizard implemented)
- [x] Migrate Portfolio report template
- [x] Cash Flow report - Tailwind migration complete (visual match unverified)
- [x] Portfolio report - Jinja syntax error fixed
- [ ] **Compass report - BLOCKED** (500 error, see post-mortem)
- [ ] Simulation report - styling only
- [ ] Migrate Integrations templates (6 files)
- [ ] Update Chart.js colors across all pages to SunnRayy palette

### Phase 4: Import Wizard Backend ✅

- [x] Add `ImportSession` model to database
- [x] `POST /workbench/api/imports` - Create wizard session
- [x] `GET /workbench/api/imports/{id}` - Get session state
- [x] `POST /workbench/api/imports/{id}/upload` - Upload & preview file
- [x] `POST /workbench/api/imports/{id}/configure` - Configure columns
- [x] `POST /workbench/api/imports/{id}/validate` - Validate data
- [x] `POST /workbench/api/imports/{id}/publish` - Publish to production
- [x] Build Import Wizard **frontend** templates (wizard.html, wizard.css)

### Phase 5: Polish & Accessibility

- [ ] Run WCAG accessibility audit
- [ ] (Optional) Add dark mode support
- [ ] Performance optimization (lazy load charts)

### Phase 6: Report Performance Fixes (In Progress)

- [x] Identified SARIMA forecast as performance bottleneck
- [x] Disabled forecast in `wealth_service.py` (`_generate_forecast_data`)
- [x] Disable forecast in `real_report.py` (`build_real_data_dict` lines 904-946)
- [ ] Verify reports load in <5 seconds
- [ ] Investigate `%o format` 500 error if it persists

### Phase 7: Single Page Application Refactor (New Architecture) ✅

- [x] **Project Structure**: Created `src/components`, `src/pages`, `src/lib`, `src/types`.
- [x] **Templates**: Moved logic from templates into `src/` as React components.
- [x] **Configuration**: Configured `vite.config.ts`, `package.json`, and `tsconfig.json` (implied).
- [x] **Unified Types**: Created `src/types/index.ts` merging all interfaces.
- [x] **Core Components**: Created `Layout.tsx` (Sidebar/Header) and `src/lib/gemini.ts`.
- [x] **Page Migration**:
  - `Dashboard.tsx`: Ported from wealthos-dashboard template.
  - `DataWorkbench.tsx`: Merged wizard flow + Gemini mappings into one component.
  - `Portfolio.tsx`: Ported from PortfolioOverview template.
- [x] **Routing**: Wired up `App.tsx` with `react-router-dom` and `main.tsx` entry point.

## Progress Log

| Date | Progress | Next |
|------|----------|------|
| 2026-01-11 | Created mockups, updated design-framework.md with SunnRayy colors | Create implementation plan, start Phase 1 |
| 2026-01-11 | **Phase 1 & 2 Complete**: Design tokens, component CSS, Dashboard, Wealth, Logic Studio redesigned | Migrate Data Workbench from Tailwind |
| 2026-01-11 | **Data Workbench migrated** from Tailwind to SunnRayy design system | Migrate Integration and Report templates |
| 2026-01-11 | **Portfolio Report fixed** (Chart.js loading, CSS utilities). **Wizard UI** set as default for Data Workbench | Verify Wizard UI, migrate remaining reports |
| 2026-01-12 | **UI Verified**: Dashboard, Workbench, Logic Studio styling confirmed. **Performance**: Identified SARIMA as bottleneck, partial fix applied | Disable SARIMA in real_report.py, continue template migration |
| 2026-01-13 | **Cashflow** Tailwind migration complete. **Compass** redesign attempt FAILED - 500 errors (Flask caching, Jinja format issues). | **SDM Review Required** |
| 2026-01-13 | **SPA Refactor Complete**: Migrated templates to React SPA structure with Vite. Merged Data Workbench, Dashboard, and Portfolio components. Missing deps fixed. | Start dev server and verify UI. |

## Blockers

### CRITICAL: Compass Report Redesign Blocked

- **Status**: 500 Internal Server Error
- **Error**: `%d format: a real number is required, not _MarkupEscapeHelper`
- **Root Causes Identified**:
  1. Flask template caching not clearing on file changes
  2. Jinja2 `format()` filter incompatible with Markup objects
  3. Mockup data props (VIX, Treasury) not available in backend
- **Documentation**: See [post-mortem-2026-01-13.md](./post-mortem-2026-01-13.md)
- **Recommendation**: Principal SDM review of mockup-to-implementation workflow

### Other Blockers

- Integrations templates (6 files) still on legacy styling
- Chart.js colors not updated to SunnRayy palette
