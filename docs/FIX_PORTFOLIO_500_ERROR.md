# Fix Plan: Portfolio Report 500 Error

> **Priority**: Critical  
> **Estimated Effort**: 1-2 hours  
> **Created**: 2026-01-08  
> **Last Updated**: 2026-01-08  
> **Status**: Partially Fixed - Secondary Issue Remains

---

## Executive Summary

The Portfolio report (`/reports/portfolio`) has **two separate issues** that both cause HTTP 500 errors:

1. **Issue #1 (FIXED)**: `UnboundLocalError` in `unified_data_preparer.py` - Variable used before assignment
2. **Issue #2 (UNRESOLVED)**: `ValueError: unsupported format character ')' (0x29) at index 7` - Jinja2/Flask-Babel translation conflict

The first issue was resolved, but the second issue surfaces immediately after and blocks page rendering.

---

## Issue #1: UnboundLocalError (RESOLVED ✅)

### Error Details

```
UnboundLocalError: cannot access local variable 'holdings_df' where it is not associated with a value
```

### Stack Trace

```
File "src/report_generators/real_report.py", line 1587, in build_real_data_dict
    validated_data = unified_preparer.prepare_all_report_data()
File "src/report_builders/unified_data_preparer.py", line 77, in prepare_all_report_data
    holdings_df = self._get_validated_holdings()
File "src/report_builders/unified_data_preparer.py", line 162, in _get_validated_holdings
    if holdings_df is None or holdings_df.empty:
       ^^^^^^^^^^^
UnboundLocalError: cannot access local variable 'holdings_df' where it is not associated with a value
```

### Root Cause

The `_get_validated_holdings()` method referenced `holdings_df` before assignment.

### Fix Applied

**File**: `src/report_builders/unified_data_preparer.py`  
**Method**: `_get_validated_holdings()` (around line 152-162)

```python
def _get_validated_holdings(self) -> pd.DataFrame:
    """Get holdings with consistent taxonomy classification applied."""
    # FIX: Added this line - get holdings from DataManager first
    holdings_df = self.data_manager.get_holdings()
    
    if holdings_df is None or holdings_df.empty:
        self.logger.warning("No holdings data available")
        return pd.DataFrame()
    # ... rest of method
```

**Status**: ✅ This fix has been applied and verified.

---

## Issue #2: Format Character Error (UNRESOLVED ❌)

### Error Details

```
ValueError: unsupported format character ')' (0x29) at index 7
```

Displayed on the web page as:

```
500 - Internal Server Error
An unexpected error occurred while processing your request.
unsupported format character ')' (0x29) at index 7
```

### Investigation Timeline & Findings

#### Observation 1: Error occurs during template rendering, NOT data preparation

The server logs show:

```
[2026-01-08 10:09:11] INFO in report_service: ✅ ReportService: Using Excel holdings (legacy mode)
[2026-01-08 10:09:11] WARNING in report_service: ⚠️ Failed to load cache: ...
[2026-01-08 10:09:11] "GET /reports/portfolio HTTP/1.1" 500 -
```

The 500 response happens ***immediately*** after the cache load warning, before any report data generation logs appear. This proves the error occurs in the rendering phase, not the data preparation phase.

#### Observation 2: Cache corruption may be a red herring

- Cache file at `data/cache/report_data_cache.json` is corrupted with truncated JSON
- Cache save fails with: `Object of type Timestamp is not JSON serializable`
- Deleting the cache does NOT fix the issue
- The error persists with a completely clean cache directory

#### Observation 3: The error pattern suggests Python %-formatting conflict

- Error: `unsupported format character ')' (0x29) at index 7`
- Character `)` at index 7 in a string suggests a pattern like `"Return %(...)"` or `"XIRR %(...)"`
- This is Python's old-style string formatting (`%` operator) failing

#### Observation 4: Template translation strings with `%%`

Found in `src/web_app/templates/reports/portfolio.html`:

```html
<!-- Lines 341-344 - ORIGINAL (problematic) -->
<th>{{ _('Return %%') }}</th>
<th>{{ _('XIRR %%') }}</th>
```

The `%%` was intended to escape a `%` sign, but when passed through Flask-Babel's `_()` translation function, the escaping rules differ.

#### Observation 5: Partial fix attempted but error persists

Changed to:

```html
<!-- Lines 341-344 - ATTEMPTED FIX -->
<th>{{ _('Return') }} %</th>
<th>{{ _('XIRR') }} %</th>
```

**Result**: Error still occurs. This suggests there are more problematic strings or the issue is elsewhere.

### Possible Root Causes (Hypotheses)

#### Hypothesis A: More `%%` patterns exist in templates or translation files

- Need to search ALL template files for `%%` inside `_()` calls
- Need to search `.po` translation files for `%%` patterns

#### Hypothesis B: Translation file (.po/.mo) has malformed format strings

- The compiled `.mo` file may contain format strings that conflict with Jinja2
- Location: `translations/zh/LC_MESSAGES/messages.po` and `messages.mo`

#### Hypothesis C: Data being passed to template contains `%` characters

- Some data value (e.g., asset name, description) might contain `%` or `%(...)` pattern
- When Jinja2 auto-escapes or the template uses `|safe`, this could cause format string interpretation

#### Hypothesis D: Jinja2/Flask-Babel interaction bug

- The `_()` function in templates is Flask-Babel's gettext
- When the translation returns a string with `%`, Jinja2 may misinterpret it
- Especially if the template uses Python-style string formatting anywhere

### Diagnostic Commands To Run

```bash
# 1. Find ALL occurrences of %% in translation function calls
grep -rn "_('.*%%.*')" src/web_app/templates/

# 2. Find %% in translation files
grep -n "%%" translations/*/LC_MESSAGES/messages.po

# 3. Find any % formatting that might conflict
grep -rn "| format" src/web_app/templates/reports/portfolio.html
grep -rn "%[sd]" src/web_app/templates/reports/portfolio.html

# 4. Check if error changes with different locales
# Set language to English first, then Chinese

# 5. Test template rendering in isolation
python -c "
from flask import Flask, render_template_string
from flask_babel import Babel

app = Flask(__name__)
babel = Babel(app)

with app.app_context():
    # Test the problematic pattern
    try:
        result = render_template_string(\"{{ _('Return') }} %\")
        print('Render OK:', result)
    except Exception as e:
        print('Render ERROR:', e)
"
```

### To Get Full Traceback

The current error handler in `routes.py` catches the exception but only shows the message. To get the full traceback:

```python
# In src/web_app/blueprints/reports/routes.py
# Modify the portfolio() function temporarily:

@reports_bp.route('/portfolio')
@login_required
def portfolio():
    try:
        # ... existing code ...
    except Exception as e:
        import traceback
        logger.error(f"Portfolio error: {e}")
        logger.error(traceback.format_exc())  # Add this line
        # Also print to console for immediate visibility:
        traceback.print_exc()
        return render_template('errors/500.html', error=e), 500
```

Then check server terminal output for the full stack trace.

### Files to Investigate

| File | Why |
|------|-----|
| `src/web_app/templates/reports/portfolio.html` | Main template - search for `%` patterns |
| `src/web_app/templates/base.html` | Base template - any `%` in nav/footer |
| `translations/zh/LC_MESSAGES/messages.po` | Chinese translations - may have format conflicts |
| `translations/zh/LC_MESSAGES/messages.mo` | Compiled translations - may need rebuild |
| `src/web_app/__init__.py` | Flask-Babel configuration |
| `src/web_app/services/report_service.py` | Data being passed to template |

### Recommended Next Steps

1. **Enable verbose debug logging** in Flask to get the full traceback with line numbers

2. **Search comprehensively** for all `%` patterns in templates:

   ```bash
   grep -rn "%" src/web_app/templates/reports/portfolio.html | grep -v "{% \| class="
   ```

3. **Rebuild translation files**:

   ```bash
   pybabel compile -d translations
   ```

4. **Test with translations disabled** to isolate if it's a Flask-Babel issue:

   ```python
   # Temporarily in __init__.py
   # Comment out: babel = Babel(app)
   ```

5. **Examine data for `%` characters**:

   ```python
   # Add to report_service.py before returning data
   for key, value in data.items():
       if isinstance(value, str) and '%' in value:
           logger.warning(f"Data key '{key}' contains % character: {value}")
   ```

---

## Related Issues Found During Investigation

### Minor Issue: Cache JSON Serialization Failure

```
❌ Failed to save cache: Object of type Timestamp is not JSON serializable
```

**Location**: `src/web_app/services/report_service.py` line ~126  
**Fix**: Need to convert pandas Timestamps to ISO strings before JSON serialization:

```python
def _save_cache(self, data: Dict[str, Any]):
    import pandas as pd
    
    def serialize(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(self.CACHE_FILE, 'w') as f:
        json.dump({'timestamp': time.time(), 'data': data}, f, default=serialize)
```

### Minor Issue: Missing XIRR Column

```
KeyError: 'XIRR'
```

**Location**: `src/recommendation_engine/recommendation_engine.py` line 369  
**Impact**: Recommendations fail to generate but don't block page load  
**Fix**: Add defensive check for XIRR column existence

---

## Session Artifacts

Screenshots captured during debugging:

- `portfolio_500_error_*.png` - Error page screenshots
- `portfolio_final_*.webp` - Browser session recordings

---

## Summary for Senior SDE

**The bottom line**: The `UnboundLocalError` was fixed, but a secondary `ValueError` now blocks the portfolio page. This error occurs during Jinja2 template rendering and appears to be related to `%` character handling in either:

1. Translation strings (`_()` function)
2. Data values being rendered
3. Some Jinja2/Flask-Babel interaction

The error message `unsupported format character ')' (0x29) at index 7` is cryptic because:

- It doesn't show which file/line
- It doesn't show which variable/value
- The Flask error handler catches it too generically

**Recommended approach**: Enable Flask debug mode with `FLASK_DEBUG=1 FLASK_ENV=development` and add explicit traceback logging to get the exact template line causing the issue. The fix is likely a simple string escaping change once the location is identified.

---

## Phase 2 Investigation: Root Cause Identified (FINAL)

**Status**: Verified Root Cause Identified 🎯

### The "Smoking Gun"

The error `ValueError: unsupported format character ')' (0x29) at index 7` perfectly matches the string `"XIRR (%)"`.

- Index 0-3: `XIRR`
- Index 4: ` ` (space)
- Index 5: `(`
- Index 6: `%` (Format start)
- Index 7: `)` (Invalid format character)

### Location of the Bug

While the table headers (HTML) were previously fixed, the **JavaScript Chart configurations** were missed. The issue exists in `src/web_app/templates/reports/portfolio.html` within the `<script>` block.

**File**: `src/web_app/templates/reports/portfolio.html`

| Line | Current Code (BUG) | Proposed Fix |
|------|-------------------|--------------|
| **816** | `label: '{{ _("XIRR (%)") }}',` | `label: '{{ _("XIRR") }} (%)',` |
| **848** | `label: '{{ _("XIRR (%)") }}',` | `label: '{{ _("XIRR") }} (%)',` |
| **882** | `label: '{{ _("Portfolio Growth (%)") }}',` | `label: '{{ _("Portfolio Growth") }} (%)',` |

### Technical Explanation

The `_()` function (Flask-Babel/Gettext) marks the string for translation. Somewhere in the pipeline (likely during a logging event that captures the rendered template context or error helper), Python attempts to format this string using `%` formatting rules. Since `%` is followed immediately by `)`, it fails.

### Action Plan for SDE

1. **Edit `src/web_app/templates/reports/portfolio.html`**:
   - Locate lines 816, 848, and 882.
   - Move the `(%)` **outside** the `_()` translation function calls.
   - Example: Change `{{ _("XIRR (%)") }}` to `{{ _("XIRR") }} (%)`.

2. **Verify Translation keys**:
   - Ensure `messages.po` has entries for `"XIRR"` and `"Portfolio Growth"`.
   - Run `pybabel compile -d translations` to ensure the clean strings are available.

3. **Restart & Verify**:
   - Restart the web server.
   - Load `/reports/portfolio`. The 500 error should necessarily vanish.
