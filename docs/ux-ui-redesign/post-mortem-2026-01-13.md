# Redesign Post-Mortem & Handoff Document

**Date**: 2026-01-13  
**Status**: BLOCKED - Requires Principal SDM Review

---

## Executive Summary

The mockup-to-implementation workflow for report template redesign has significant friction. The Compass report redesign attempt on 2026-01-13 failed after multiple iterations due to:

1. Flask template caching behavior
2. Jinja2/Python type compatibility issues with `format()`
3. Missing validation between mockup components and backend data availability

---

## What Was Attempted

### Compass Report Redesign (FAILED)

**Goal**: Transform `compass.html` from legacy table-heavy layout to modern chart-based design matching `templates/wealthos-reports/pages/Compass.tsx` mockup.

**Mockup Features**:

- Blue gradient hero card with regime status + VIX/Treasury KPIs
- Target vs Current Allocation bar chart  
- Drift Analysis horizontal bar chart with critical indicators
- Asset Correlation Matrix (styled heatmap table)
- Risk/Return Profile scatter chart

**Implementation Blockers**:

| Issue | Root Cause | Attempts to Fix |
|-------|------------|-----------------|
| `url_for('reports.simulation')` error | Wrong Flask endpoint name | Changed to `simulation.index` |
| `%d format: a real number` error | Jinja `format()` filter receives Markup objects | Added `\|float` and `\|int` filters |
| Server shows old template | Flask Jinja2 template caching | Multiple server restarts (4+) |
| Template still broken after fixes | Unknown - possibly bytecode cache or import caching | Unable to resolve |

**Files Modified**:

- `/src/web_app/templates/reports/compass.html` - Complete rewrite (490 lines)

---

## What DID Work Previously

### Cashflow Report (PARTIAL SUCCESS)

Bootstrap → Tailwind migration completed for `cashflow.html`:

- ✅ All 6 tabs converted (Net Worth, Cash Flow, Expenses, Income, Analysis, Forecast)
- ✅ Tab JS updated to use `hidden` class instead of `d-none`
- ✅ Chart containers use Tailwind height classes
- ⚠️ Visual consistency with mockup not verified due to time constraints

### Portfolio Report (FIXED)

- ✅ Fixed missing `{% endif %}` Jinja syntax error (line 271)
- ✅ Page now loads without 500 error

---

## Technical Learnings

### 1. Flask Template Caching is Aggressive

Even with `TEMPLATES_AUTO_RELOAD=True`, template changes may require:

- Full server restart
- Clearing `__pycache__` directories  
- Potentially Flask bytecode compilation cache

**Recommendation**: Add `app.config['TEMPLATES_AUTO_RELOAD'] = True` AND `app.jinja_env.auto_reload = True` in development mode.

### 2. Jinja2 `format()` Filter Type Issues

```jinja2
{# BROKEN - Returns Markup object #}
{{ "%.1f"|format(item.drift) }}

{# WORKS - Explicit type conversion #}
{{ "%.1f"|format(item.drift|float) }}
{{ "{:,.0f}".format((trade_amount|abs)|int) }}
```

**Recommendation**: Create custom Jinja filters for common patterns:

```python
@app.template_filter('currency')
def currency_filter(value):
    return f"¥{float(value):,.0f}"
```

### 3. Mockup → Template Data Mismatch

The Compass.tsx mockup assumes data that may not exist:

- VIX Index / 10Y Treasury → Not in current backend
- Correlation Matrix values → Not computed in route
- Risk/Return scatter coordinates → Not in template context

**Recommendation**: Before implementing mockup, validate all data props exist in Flask route.

### 4. Mixed CSS Framework Pain

Current templates mix:

- Bootstrap 5 classes (`row`, `col-lg-*`, `d-none`)
- Tailwind utility classes (`flex`, `grid`, `hidden`)
- Custom component classes (`.card`, `.glass-card`, `.chart-title`)

**Recommendation**: Decide on ONE approach and document in design-framework.md.

---

## Files Status

| Template | Status | Notes |
|----------|--------|-------|
| `dashboard/index.html` | ✅ Done | Phase 2 complete |
| `wealth/overview.html` | ✅ Done | Phase 2 complete |
| `logic_studio/index.html` | ✅ Done | Phase 2 complete |
| `data_workbench/wizard.html` | ✅ Done | Phase 4 complete |
| `reports/portfolio.html` | ✅ Fixed | Jinja error fixed, loads correctly |
| `reports/cashflow.html` | ⚠️ Partial | Tailwind migration done, visual match unverified |
| `reports/compass.html` | ❌ Broken | 500 error, needs debugging |
| `reports/simulation.html` | ⚠️ Legacy | Minor styling updates only |

---

## Recommended Next Steps (for Principal SDM)

### Immediate (P0)

1. **Debug Compass 500 Error** - Run Flask in debug mode, check actual traceback
2. **Verify Tailwind Setup** - Confirm Tailwind is properly compiled/loaded

### Short-term (P1)

3. **Create Data Validation Checklist** - Before implementing any mockup, verify:
   - All data props exist in Flask route
   - Data types match expected format
   - Fallback/default values defined

2. **Add Custom Jinja Filters** - For currency, percentage, date formatting

### Process Improvement (P2)

5. **Simplify Mockup Delivery** - Consider:
   - Static HTML exports instead of React/TSX
   - Design tokens as JSON for both design and dev
   - Component-level mockups vs full-page designs

2. **Template Testing Infrastructure** - Add:
   - Jinja template syntax validation in CI
   - Screenshot regression tests for key pages

---

## Reference Materials

| Resource | Path |
|----------|------|
| Design Framework | `docs/design-framework.md` |
| HTML Mockups | `templates/wealthos-reports/pages/` |
| Design Tokens | `src/web_app/static/css/design-tokens.css` |
| Component CSS | `src/web_app/static/css/style.css` |

---

*Document created by AI agent session. Review recommended before implementation.*
