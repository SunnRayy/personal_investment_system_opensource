# Feature: UX/UI Redesign

> **Last Updated**: 2026-01-13
> **Full Plan**: See [development-plan.md](./development-plan.md) for detailed implementation guide.

## Overview

Complete redesign of the Personal Investment System UI following `docs/design-framework.md` and the "SunnRayy" visual identity. The project pivoted from Flask/Jinja2 templates to a React SPA approach after encountering template caching and data contract issues.

**Current Architecture**: React SPA (Vite) → API Client → Flask Backend

---

## Phase Summary

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| 1-4 | Design System Foundation | ✅ Complete | CSS tokens, Jinja macros, base template |
| 5 | Polish & Accessibility | ⏸️ Deferred | Will complete in new Phase 5 |
| 6 | Report Performance | ✅ Complete | SARIMA disabled, reports load fast |
| 7 | SPA Refactor | ✅ Complete | React/Vite project structure |
| 8 | API Integration | ✅ Complete | API client, types, hooks, Dashboard wired |
| 9 | Authentication | 🔜 Next | AuthContext, Login, ProtectedRoute |
| 10 | Reports Migration | ✅ Complete | Portfolio, CashFlow, Compass pages |
| 11 | Remaining Pages | 🔄 In Progress | Simulation (Done), Performance (New), Wealth/Logic (Pending) |
| 12 | Final Polish | 📋 Planned | Dark mode, a11y, deprecate templates |

---

## Detailed Phases

### Phase 1-4: Design System Foundation ✅

- [x] Create `design-tokens.css` with SunnRayy palette
- [x] Update `style.css` to use CSS variables
- [x] Update `base.html` with new navigation
- [x] Create `components.html` Jinja2 macros
- [x] Add comprehensive component CSS (cards, buttons, forms, tables, badges)
- [x] Redesign Dashboard (`/`)
- [x] Redesign Wealth Overview (`/wealth`)
- [x] Redesign Logic Studio (`/logic-studio`)
- [x] Test responsive layouts

### Phase 6: Report Performance Fixes ✅

- [x] Identified SARIMA forecast as performance bottleneck
- [x] Disabled forecast in `wealth_service.py`
- [x] Disabled forecast in `real_report.py`
- [x] Reports now load in <5 seconds

### Phase 7: SPA Architecture Refactor ✅

- [x] Created `src/components`, `src/pages`, `src/lib`, `src/types`
- [x] Configured `vite.config.ts`, `package.json`
- [x] Created `Layout.tsx` (Sidebar/Header)
- [x] Migrated `Dashboard.tsx` from mockup
- [x] Migrated `DataWorkbench.tsx` with Gemini AI integration
- [x] Migrated `Portfolio.tsx`
- [x] Wired up `App.tsx` with `react-router-dom`

### Phase 8: API Integration Layer ✅ (2026-01-13)

- [x] Created `src/api/client.ts` - Type-safe fetch wrapper
- [x] Created `src/api/endpoints.ts` - Centralized endpoint constants
- [x] Created `src/api/types/portfolio.ts` - Portfolio response types
- [x] Created `src/api/types/reports.ts` - Reports response types
- [x] Added `@tanstack/react-query` for data fetching
- [x] Created `src/hooks/usePortfolio.ts` - Portfolio data hooks
- [x] Created `src/hooks/useReports.ts` - Reports data hooks
- [x] Updated `App.tsx` with QueryClientProvider
- [x] Wired `Dashboard.tsx` to fetch real data from `/api/portfolio_overview`
- [x] Added loading spinner, error states, refresh button
- [x] Build verified with no TypeScript errors

### Phase 9: Authentication & State 🔜 NEXT

- [ ] Create `src/contexts/AuthContext.tsx`
  - Manages user state, token, loading
  - Exposes `login()`, `logout()`, `isAuthenticated`
- [ ] Create `src/contexts/PreferencesContext.tsx`
  - Theme preference (light/dark)
  - Currency display preference
- [ ] Create `src/components/ProtectedRoute.tsx`
  - Redirects unauthenticated users to `/login`
- [ ] Create `src/pages/Login.tsx`
  - Form with validation
  - Connects to Flask `/auth/login`

### Phase 10: Dashboard + Reports Migration ✅ (2026-01-13)

- [x] Migrate Portfolio report (`/reports/portfolio`)
  - Data: `/api/unified_analysis`
  - Components: PortfolioSummary, AssetAllocationTable, PerformanceChart
- [x] Migrate Cash Flow report (`/reports/cashflow`)
  - Data: `/wealth/api/cash-flow`
  - Components: CashFlowSummary, IncomeExpenseChart
- [x] Migrate Compass report (`/reports/compass`)
  - Data: `/api/unified_analysis`
  - Components: RegimeIndicator, DriftAnalysis, RebalanceRecommendations
- [x] **New: Lifetime Performance Report** (`/performance`)
  - Gains Analysis (Realized vs Unrealized)
  - Asset Performance Scorecard

### Phase 11: Remaining Pages 🔄

- [ ] Wealth Overview (`/wealth`)
- [x] Logic Studio (`/logic-studio`) - React SPA with tabs: Rules, Tiers, Profiles
- [x] Simulation (`/reports/simulation`)
- [ ] Settings (`/settings`)

### Phase 12: Final Polish 📋

- [ ] Remove Tailwind CDN from Flask templates
- [ ] Implement dark mode toggle
- [ ] WCAG 2.1 AA accessibility audit
- [ ] Code split with React.lazy()
- [ ] Deprecate unused Flask templates

---

## Progress Log

| Date | Progress | Next |
|------|----------|------|
| 2026-01-11 | Created mockups, updated design-framework.md | Create implementation plan |
| 2026-01-11 | **Phase 1-4 Complete**: Design tokens, component CSS | Migrate Data Workbench |
| 2026-01-11 | **Data Workbench migrated** from Tailwind | Migrate reports |
| 2026-01-11 | **Portfolio Report fixed** (Chart.js loading) | Verify Wizard UI |
| 2026-01-12 | **UI Verified**: Dashboard, Workbench confirmed | Disable SARIMA |
| 2026-01-13 | **Cashflow** Tailwind migration complete | SDM Review |
| 2026-01-13 | **Compass redesign FAILED** - 500 errors | Pivot to React SPA |
| 2026-01-13 | **SPA Refactor Complete** (Phase 7) | API integration |
| 2026-01-13 | **API Integration Complete** (Phase 8) | Auth & Reports |
| 2026-01-13 | **Authentication** (Phase 9) | Reports Migration |
| 2026-01-13 | **Reports Migration Complete** (Phase 10) | Remaining Pages |
| 2026-01-13 | **Simulation & Performance** (Phase 11) | Wealth & Logic Studio |
| 2026-01-13 | **Logic Studio React SPA** complete (Rules, Tiers, Profiles) | Stage & Commit |

---

## Current Blockers

### RESOLVED: Template-to-Implementation Workflow

- **Previous Issue**: Flask Jinja2 templates blocked on data contract mismatches and caching.
- **Resolution**: Pivoted to React SPA with API integration layer.
- **Documentation**: See [post-mortem-2026-01-13.md](./post-mortem-2026-01-13.md)

### Remaining Work

- Reports need React migration (Phase 10)
- Integrations templates still on legacy styling
- Chart.js colors not updated in Flask templates (will be deprecated)

---

## Files Reference

### New Files (Phase 8)

```
src/api/
├── client.ts           # API fetch wrapper
├── endpoints.ts        # Endpoint constants
├── types/
│   ├── portfolio.ts    # Portfolio types
│   ├── reports.ts      # Report types
│   └── index.ts
└── index.ts

src/hooks/
├── usePortfolio.ts     # Portfolio hooks
├── useReports.ts       # Report hooks
└── index.ts
```

### Modified Files

```
src/App.tsx             # Added QueryClientProvider
src/pages/Dashboard.tsx # Now uses real API data
package.json            # Added react-query
```

### Key Flask Files (Backend - Read Only)

```
src/web_app/blueprints/api/routes.py      # API endpoints
src/web_app/services/report_service.py    # Data service
src/web_app/services/wealth_service.py    # Wealth data
```

---

## Handoff Notes

**For the next developer:**

1. **Start here**: Read [development-plan.md](./development-plan.md) for full context
2. **Current state**: Phase 8 complete, Dashboard fetches real data
3. **Next task**: Phase 9 (AuthContext) or Phase 10 (Reports)
4. **Run locally**:

   ```bash
   python main.py run-web --port 5001  # Flask
   npm run dev                          # React
   ```

5. **Verify**: Dashboard at <http://localhost:3000> shows real portfolio data
