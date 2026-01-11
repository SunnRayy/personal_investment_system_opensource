# Personal Investment System - UX/UI Redesign Framework

## Overview

A comprehensive design framework for redesigning the Personal Investment System (WealthOS) from a function-first personal tool to a modern, approachable fintech application. This document is intended for Designers to follow and build out the UI.

**Primary Inspiration**: Maybe Finance (open-source app in `/Users/ray/Documents/maybe-finance/maybe`)
**Design Style**: Modern fintech (Robinhood/Wealthfront aesthetic - colorful gradients, approachable)
**Target User**: Sophisticated but not professional investor who consolidates investments across multiple platforms

---

## 1. Design Principles

### 1.1 Core Philosophy

1. **Clarity Over Complexity**: Financial data is inherently complex. The UI must simplify without dumbing down, using progressive disclosure to reveal complexity only when needed.

2. **Confidence Through Visualization**: Charts and graphs should immediately communicate portfolio health. Users should understand their financial position within 3 seconds of viewing the dashboard.

3. **Approachable Sophistication**: Target users are sophisticated but not professional. Use professional terminology but provide contextual help for advanced concepts.

4. **Data First, Action Second**: Information hierarchy should prioritize data comprehension before prompting user actions.

5. **Consistency Builds Trust**: Financial applications require trust. Consistent styling, predictable interactions, and reliable feedback build user confidence.

### 1.2 Design Tenets

| Tenet | Application |
|-------|-------------|
| **Progressive Disclosure** | Hide complexity until needed; use tooltips, expandable sections, and drill-down views |
| **Semantic Color Coding** | Green = gains/positive, Red = losses/negative, Blue = neutral/informational |
| **8px Grid System** | All spacing and sizing based on 8px increments for visual rhythm |
| **Desktop-First Responsive** | Primary use is desktop, ensure key dashboards work on tablet |
| **Accessibility First** | WCAG 2.1 AA compliance, sufficient color contrast, keyboard navigation |

---

## 2. Design System Specification

### 2.1 Color Palette

#### Primary Brand Colors (SunnRayy Identity)

**Brand Philosophy**: "SunnRayy" (阳光金 + 科技蓝) – Warm gold for wealth/prestige, tech blue for trust/action.

```css
/* SunnRayy Brand - Gold accents, Blue interactions */
--brand-gold: #D4AF37;         /* Champagne Gold - 阳光金 */
--brand-gold-light: #E5C158;   /* Light Gold - hover states */
--brand-gold-dark: #C9A227;    /* Deep Gold - emphasis */
--brand-blue: #3B82F6;         /* Tech Blue - 科技蓝 */
--brand-blue-light: #60A5FA;   /* Light Blue - hover */
--brand-blue-dark: #2563EB;    /* Deep Blue - active */

/* Brand Gradient - Subtle accents only, not backgrounds */
--brand-gradient: linear-gradient(135deg, #D4AF37 0%, #3B82F6 100%);
```

#### Semantic Colors (Light Mode - Primary)

```css
/* Backgrounds */
--bg-surface: #FAFAFA;         /* Page background */
--bg-container: #FFFFFF;       /* Cards, modals */
--bg-container-inset: #F5F5F5; /* Nested containers */
--bg-container-hover: #F0F0F0;

/* Text */
--text-primary: #171717;       /* Gray-900 - headings, emphasis */
--text-secondary: #525252;     /* Gray-600 - body text */
--text-tertiary: #A3A3A3;      /* Gray-400 - labels, hints */
--text-inverse: #FFFFFF;

/* Borders */
--border-primary: rgba(0, 0, 0, 0.15);
--border-secondary: rgba(0, 0, 0, 0.10);
--border-tertiary: rgba(0, 0, 0, 0.05);

/* Financial Semantics */
--color-gain: #10B981;         /* Emerald-500 - positive returns */
--color-gain-bg: #D1FAE5;      /* Emerald-100 */
--color-loss: #EF4444;         /* Red-500 - negative returns */
--color-loss-bg: #FEE2E2;      /* Red-100 */
--color-neutral: #6B7280;      /* Gray-500 */

/* Status Colors */
--color-success: #10B981;
--color-warning: #F59E0B;      /* Amber-500 */
--color-error: #EF4444;
--color-info: #3B82F6;         /* Blue-500 */
```

#### Dark Mode (V2 - Nice to Have)

```css
/* Backgrounds */
--bg-surface: #0A0A0A;
--bg-container: #171717;
--bg-container-inset: #262626;

/* Text */
--text-primary: #FAFAFA;
--text-secondary: #A3A3A3;
--text-tertiary: #525252;
```

#### Chart Color Palette

```css
/* Asset Class Colors - SunnRayy harmonized */
--chart-equity: #D4AF37;       /* Gold - Primary investments */
--chart-fixed-income: #3B82F6; /* Tech Blue - Bonds */
--chart-cash: #6B7280;         /* Gray */
--chart-alternatives: #0EA5E9; /* Sky Blue */
--chart-real-estate: #C9A227;  /* Deep Gold */
--chart-crypto: #14B8A6;       /* Teal */
--chart-commodities: #60A5FA;  /* Light Blue */
--chart-other: #78716C;        /* Stone */
```

### 2.2 Typography Scale

**Font Family**: Inter (primary), system fonts as fallback

```css
--font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
```

**Type Scale** (16px base):

| Name | Size | Weight | Line Height | Use Case |
|------|------|--------|-------------|----------|
| `display-xl` | 48px | 700 | 1.1 | Hero headlines |
| `display-lg` | 36px | 700 | 1.2 | Page titles |
| `heading-xl` | 30px | 600 | 1.3 | Section headers |
| `heading-lg` | 24px | 600 | 1.3 | Card titles |
| `heading-md` | 20px | 600 | 1.4 | Subsection headers |
| `heading-sm` | 16px | 600 | 1.5 | Small headers |
| `body-lg` | 18px | 400 | 1.6 | Lead paragraphs |
| `body-md` | 16px | 400 | 1.5 | Body text |
| `body-sm` | 14px | 400 | 1.5 | Secondary text |
| `caption` | 12px | 500 | 1.4 | Labels, captions |
| `overline` | 11px | 600 | 1.4 | Overline text, uppercase |

**Financial Numbers**: Use tabular figures for alignment

```css
.financial-number {
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}
```

### 2.3 Spacing System (8px Grid)

```css
--space-1: 4px;    /* Tight spacing */
--space-2: 8px;    /* Base unit */
--space-3: 12px;
--space-4: 16px;   /* Component padding */
--space-5: 20px;
--space-6: 24px;   /* Card padding */
--space-8: 32px;   /* Section gaps */
--space-10: 40px;
--space-12: 48px;  /* Large sections */
--space-16: 64px;  /* Page margins */
```

### 2.4 Component Library

#### Buttons

| Variant | Use Case | Styling |
|---------|----------|---------|
| `primary` | Main CTAs | Solid brand gradient, white text |
| `secondary` | Secondary actions | Gray-100 bg, dark text |
| `outline` | Tertiary actions | Border only, transparent bg |
| `ghost` | Inline actions | No border, subtle hover |
| `destructive` | Delete/cancel | Red background |

**Sizes**:

- Small: 32px height, 12px padding, 14px text
- Medium: 40px height, 16px padding, 14px text
- Large: 48px height, 24px padding, 16px text

#### Cards

**Metric Card Structure** (for KPIs):

```html
<div class="metric-card border-t-4 border-t-blue-500">
  <div class="metric-card__header">
    <span class="metric-card__label">NET WORTH</span>
    <span class="metric-card__badge positive">+12.5%</span>
  </div>
  <div class="metric-card__value">$1,234,567</div>
  <p class="metric-card__subtitle">vs $1,100,000 last month</p>
</div>
```

#### Forms (Following Maybe Finance Pattern)

```html
<div class="form-field">
  <label class="form-field__label">Account Name</label>
  <input type="text" class="form-field__input" />
</div>
```

#### Badges / Tags

```css
.badge { @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium; }
.badge-success { @apply bg-green-100 text-green-800; }
.badge-warning { @apply bg-amber-100 text-amber-800; }
.badge-error { @apply bg-red-100 text-red-800; }
.badge-info { @apply bg-blue-100 text-blue-800; }
```

#### Alerts (4 variants: info, success, warning, error)

Include: Icon, Title, Message, Optional dismiss button

### 2.5 Icon System

**Recommended**: Lucide Icons (MIT licensed, consistent with Maybe Finance)

**Sizes**: xs (12px), sm (16px), md (20px), lg (24px), xl (32px)

**Financial-Specific Icons**:

- `trending-up` / `trending-down` - Gains/losses
- `wallet` - Net worth
- `pie-chart` - Allocation
- `bar-chart-2` - Performance
- `refresh-cw` - Sync status
- `upload` - Import data
- `git-branch` - Classification rules
- `link` - Integrations

---

## 3. Page-by-Page Redesign

### 3.1 Dashboard (Main Wealth View)

**Priority: HIGH** - First impression for all users

**Layout**:

```
┌────────────────────────────────────────────────────────────────┐
│  Header: Welcome back, [Name]             [Period Selector ▼]  │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  NET WORTH HERO                                          │  │
│  │  $1,234,567.89                                           │  │
│  │  ▲ +$23,456 (+2.1%) this month                           │  │
│  │  [═══════════ TIME SERIES CHART ═══════════════════════] │  │
│  └──────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────┤
│  QUICK METRICS ROW                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ YTD Return │ │ Holdings   │ │ Cash       │ │ XIRR       │  │
│  │ +15.3%     │ │ 47         │ │ $45,000    │ │ 12.4%      │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
├──────────────────────────────┬─────────────────────────────────┤
│  ALLOCATION BREAKDOWN        │  RECENT ACTIVITY               │
│  [Donut Chart]               │  • Dividend: AAPL +$123        │
│  Equity: 65%                 │  • Buy: VTI 10 shares          │
│  Fixed Income: 20%           │  • Sync: Schwab completed      │
│  Cash: 10%                   │                                │
│  Alternatives: 5%            │                                │
└──────────────────────────────┴─────────────────────────────────┘
```

**Key Interactions**:

- Net Worth Chart: Hover shows date value, click-and-drag to zoom, period selector (1W, 1M, 3M, YTD, 1Y, All)
- Allocation Donut: Hover highlights segment, click drills down to asset class
- Metric Cards: Color-coded borders (green/red based on trend)

### 3.2 Data Workbench (Import, Mapping, Validation)

**Priority: HIGH** - Critical for new user success

**Two Modes**:

1. **Wizard Mode (First-Time Users)**:
   - Step indicator: Upload → Map Columns → Review → Complete
   - Large drag-and-drop upload zone
   - Clear "OR connect a data source" option with platform logos
   - Download sample templates prominently displayed

2. **Staging Area (Experienced Users)**:
   - Summary: Total records, Valid count, Error count with visual bars
   - Filter controls: All / Errors Only / Valid Only
   - Table with inline error resolution
   - Batch actions for bulk operations

**Error Resolution Modal**:

- Map to Existing Asset (searchable dropdown)
- Create New Asset (quick form)
- Skip/Ignore option
- Apply to all similar errors checkbox

### 3.3 Logic Studio (Asset Classification, Rules)

**Priority: HIGH** - Essential for organizing investments

**Layout**:

```
┌────────────────────┬───────────────────────────────────────────┐
│  MODULES           │  TAXONOMY EDITOR                          │
│  ● Taxonomy        │  Asset Class                         [+]  │
│  ○ Strategy Rules  │  ├── Equity           ▼                   │
│  ○ Auto-Classify   │  │   ├── US Large Cap                     │
│  ○ Asset Tier      │  │   ├── US Small Cap                     │
│  ○ Target Alloc    │  │   └── International                    │
│                    │  ├── Fixed Income    ▶                    │
│                    │  └── Cash            ▶                    │
│                    │                                           │
│                    │  TAG DETAILS                              │
│                    │  Name: US Large Cap                       │
│                    │  Pattern: *SPY*, *VOO*, *IVV*             │
│                    │  Assets Matched: 12                       │
│                    │  [View Matched Assets]                    │
└────────────────────┴───────────────────────────────────────────┘
```

**Features**:

- Visual tree navigation for taxonomy
- Live preview showing which assets match current rules
- Drag-and-drop reordering
- Search/filter within categories

### 3.4 Reports Hub

**Priority: MEDIUM**

**Layout**: Tab-based report selection

- Portfolio Overview
- Cash Flow Analysis
- Performance Attribution
- Market Compass
- Monte Carlo Simulation

**Consistent Report Structure**:

1. Report header with title, date range, export options
2. Primary visualization (chart)
3. Key metrics row
4. Detailed breakdown table
5. Export button (PDF, CSV)

### 3.5 Integrations Hub

**Priority: MEDIUM**

**Layout**:

- Connected Sources section (cards with status, last sync, record count)
- Add New Connection section (categorized by type: Brokerages, Crypto)
- Sync All button, individual sync buttons per connection
- Clear connection/disconnection states

### 3.6 Onboarding Flow

**Priority: HIGH** - Critical for new user adoption

**Flow Steps**:

1. Welcome Screen - Warm greeting, value proposition
2. Choose Your Path - Demo Mode / Upload Data / Connect Account
3. Import Wizard - (if upload chosen) Guided step-by-step
4. First Dashboard - With contextual walkthrough tooltips

**Contextual Help System**:

- Tooltips: Hover-triggered for icon buttons
- Info Popovers: Click-triggered for complex concepts (XIRR, Attribution)
- Walkthrough Mode: Step-by-step overlay for first-time users (use intro.js or similar)

---

## 4. Data Visualization Guidelines

### 4.1 Chart Types

| Chart Type | Use Case |
|------------|----------|
| **Line Chart** | Time-series data (net worth over time) |
| **Area Chart** | Cumulative values, composition over time |
| **Donut Chart** | Part-to-whole (asset allocation) |
| **Bar Chart** | Comparisons (performance by asset class) |
| **Waterfall Chart** | Attribution, step-by-step changes |
| **Gauge Chart** | Progress toward goal |

### 4.2 Color Coding Standards

```css
/* Positive */
--chart-positive: #10B981;
--chart-positive-gradient: linear-gradient(180deg, rgba(16, 185, 129, 0.2) 0%, transparent 100%);

/* Negative */
--chart-negative: #EF4444;
--chart-negative-gradient: linear-gradient(180deg, rgba(239, 68, 68, 0.2) 0%, transparent 100%);
```

**Trend Indicators**:

- ▲ in green for positive
- ▼ in red for negative
- — in gray for neutral

### 4.3 Interactive Behaviors

**Hover**: Highlight point, show tooltip, display guideline, fade other elements
**Click**: Drill-down to detail, filter to category, toggle visibility
**Responsive**: Hide legend on mobile, use touch tooltip, horizontal scroll for wide charts

### 4.4 Recommended Library

Replace Chart.js with **D3.js** for:

- More control over interactions
- Better performance with large datasets
- Consistent with Maybe Finance patterns
- Reference: `/Users/ray/Documents/maybe-finance/maybe/app/javascript/controllers/time_series_chart_controller.js`

---

## 5. User Flows

### 5.1 First-Time User Onboarding

```
Landing → Choose Path → [Demo/Upload/Connect] → First Dashboard (with walkthrough)
```

### 5.2 Adding New Data Source

```
Workbench → Upload File → Auto-Detect Format → Confirm Mapping → Staging Review → Promote to System
```

### 5.3 Understanding Portfolio Performance

```
Dashboard → Period Select → View Trend → Hover Detail / Click Allocation → Asset Class Detail / Attribution Report
```

---

## 6. Detailed Import User Flow (Mimicking Maybe Finance)

This section provides comprehensive UX specifications for the data import process, based on Maybe Finance's proven wizard-based approach. This is the **highest priority** flow for new user success.

### 6.1 Import Flow Overview

```
┌─────────┐   ┌─────────┐   ┌───────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Select  │──▶│ Upload  │──▶│ Configure │──▶│  Clean  │──▶│   Map   │──▶│ Review  │──▶│ Publish │
│  Type   │   │  File   │   │  Columns  │   │  Data   │   │ Values  │   │ Summary │   │ Import  │
└─────────┘   └─────────┘   └───────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘
     1             2              3              4             5             6             7
```

Each step is a **separate page** with clear progress indication and back navigation.

---

### 6.2 Step 1: Import Type Selection

**Route**: `/imports/new`
**Layout**: Dialog/Modal overlay

**Screen Elements**:

```
┌────────────────────────────────────────────────────────────┐
│  Choose data to import                              [✕]    │
│  Select what you'd like to add to your portfolio           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 📊 Resume pending import          [Orange badge]    │   │
│  │    Continue your Schwab import from yesterday      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 📈 Import Transactions                              │   │
│  │    Add transactions from CSV or spreadsheet        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 💼 Import Holdings                                  │   │
│  │    Add current portfolio positions                 │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🏦 Import Accounts                                  │   │
│  │    Create multiple accounts from CSV               │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Available Import Types**:

| Type | Icon | Description | Prerequisites |
|------|------|-------------|---------------|
| Resume Pending | 🔄 | Continue interrupted import | Has pending import |
| Transactions | 📈 | Buy/sell/dividend records | At least 1 account exists |
| Holdings | 💼 | Current positions snapshot | At least 1 account exists |
| Accounts | 🏦 | Bulk create accounts | None (always available) |

**Design Notes**:

- Show "Resume pending" only if user has incomplete import
- Disable Transaction/Holdings options if no accounts exist (show tooltip explaining why)
- Each option is a clickable card with hover state
- Color-code by type (use chart colors from design system)

---

### 6.3 Step 2: File Upload

**Route**: `/imports/{id}/upload`
**Header**: Step progress indicator showing "Upload" as active

**Screen Layout**:

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back                    Upload (Step 1 of 5)                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Upload your CSV file                                          │
│  Paste or upload your transaction data                         │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  [Upload CSV]  |  [Copy & Paste]                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────┐                     │
│  │ Column Separator                      │                     │
│  │ [Comma (,)              ▼]           │                     │
│  └──────────────────────────────────────┘                     │
│                                                                │
│  ┌──────────────────────────────────────┐                     │
│  │ Target Account (optional)            │                     │
│  │ [Multi-account import    ▼]          │                     │
│  └──────────────────────────────────────┘                     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │         ┌─────────────────────────────┐                 │  │
│  │         │     [Cloud Upload Icon]     │                 │  │
│  │         │                             │                 │  │
│  │         │   Drop your file here       │                 │  │
│  │         │   or click to browse        │                 │  │
│  │         │                             │                 │  │
│  │         │   Supports: CSV, Excel      │                 │  │
│  │         └─────────────────────────────┘                 │  │
│  │                                                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  📥 Download sample template                                   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    [Upload CSV]                          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Tab: Copy & Paste** (alternative to file upload):

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Paste your CSV file contents here                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  (10-row textarea)                                      │ │
│  │                                                         │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Field Specifications**:

| Field | Type | Options | Default |
|-------|------|---------|---------|
| Column Separator | Dropdown | Comma, Semicolon, Tab | Comma |
| Target Account | Dropdown | "Multi-account import" + all accounts | Multi-account |
| File | Drag-drop zone | CSV, XLSX, XLS | - |

**Validation**:

- File must be parseable CSV/Excel
- Must have header row
- Must have at least 1 data row
- Show clear error message if validation fails

**Sample Template Download**:

- Provide type-specific template with required columns marked with asterisks
- Template includes example data rows

---

### 6.4 Step 3: Configure Columns

**Route**: `/imports/{id}/configuration`
**Header**: Step progress indicator showing "Configure" as active

**Template Detection Banner** (if returning user):

```
┌────────────────────────────────────────────────────────────────┐
│  ✓ We found a configuration from your previous Schwab import  │
│                                                                │
│  [Apply Template]            or            Skip to configure   │
└────────────────────────────────────────────────────────────────┘
```

**Configuration Form Layout**:

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back                   Configure (Step 2 of 5)              │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Configure your columns                                        │
│  Map your CSV columns to our system fields                     │
│                                                                │
│  ─────────────────────────────────────────────────────────────│
│  REQUIRED FIELDS                                               │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  Date Column *                    Date Format *                │
│  ┌────────────────────────┐      ┌────────────────────────┐   │
│  │ [Transaction Date ▼]   │      │ [MM/DD/YYYY      ▼]    │   │
│  └────────────────────────┘      └────────────────────────┘   │
│                                                                │
│  Amount Column *                  Number Format *              │
│  ┌────────────────────────┐      ┌────────────────────────┐   │
│  │ [Amount          ▼]    │      │ [1,234.56 (US)   ▼]    │   │
│  └────────────────────────┘      └────────────────────────┘   │
│                                                                │
│  ─────────────────────────────────────────────────────────────│
│  AMOUNT TYPE                                                   │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  How are amounts represented in your file?                     │
│                                                                │
│  ○ Signed amounts (positive = income, negative = expense)      │
│      └─▶ Signage: [Incomes are positive ▼]                    │
│                                                                │
│  ● Column indicates type (e.g., "credit" = income)            │
│      └─▶ Type Column: [Transaction Type ▼]                    │
│          Income Value: [Credit           ▼]                   │
│                                                                │
│  ─────────────────────────────────────────────────────────────│
│  OPTIONAL FIELDS                                               │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  Account Column          Asset/Ticker Column                   │
│  ┌────────────────────┐  ┌────────────────────────┐           │
│  │ [Account Name  ▼]  │  │ [Symbol          ▼]    │           │
│  └────────────────────┘  └────────────────────────┘           │
│                                                                │
│  Category Column         Tags Column                           │
│  ┌────────────────────┐  ┌────────────────────────┐           │
│  │ [Category     ▼]   │  │ [Tags            ▼]    │           │
│  └────────────────────┘  └────────────────────────┘           │
│                                                                │
│  Notes Column            Currency Column                       │
│  ┌────────────────────┐  ┌────────────────────────┐           │
│  │ [Description  ▼]   │  │ [Currency        ▼]    │           │
│  └────────────────────┘  └────────────────────────┘           │
│                                                                │
│  ─────────────────────────────────────────────────────────────│
│  CSV PREVIEW (First 2 rows)                                    │
│  ─────────────────────────────────────────────────────────────│
│                                                                │
│  │ Date       │ Amount  │ Type   │ Symbol │ Description │     │
│  │ 01/15/2024 │ 1000.00 │ Credit │ AAPL   │ Dividend    │     │
│  │ 01/14/2024 │ -500.00 │ Debit  │ VTI    │ Buy shares  │     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              [Apply Configuration]                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Configuration Fields by Import Type**:

**Transaction Import**:

| Field | Required | Description |
|-------|----------|-------------|
| Date Column | Yes | Column containing transaction date |
| Date Format | Yes | e.g., MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD |
| Amount Column | Yes | Column containing transaction amount |
| Number Format | Yes | e.g., 1,234.56 (US), 1.234,56 (EU) |
| Amount Type Strategy | Yes | Signed amounts vs. separate type column |
| Account Column | If multi-account | Column identifying the account |
| Asset/Ticker Column | No | Column with stock symbol |
| Category Column | No | Column for expense/income category |
| Tags Column | No | Column with tags (pipe-separated) |
| Notes Column | No | Column with description/notes |
| Currency Column | No | Column with currency code |

**Holdings Import**:

| Field | Required | Description |
|-------|----------|-------------|
| Date Column | Yes | Snapshot date |
| Asset/Ticker Column | Yes | Stock symbol |
| Shares Column | Yes | Number of shares held |
| Price Column | No | Price per share (or fetched automatically) |
| Cost Basis Column | No | Total cost basis |
| Account Column | If multi-account | Account name |

**Progressive Disclosure Pattern**:

- Show "Signed amounts" fieldset when that radio is selected
- Show "Type column" fieldset when that radio is selected
- Hide irrelevant fields based on selection
- Use Stimulus/JS for real-time UI updates

---

### 6.5 Step 4: Clean Data (Validation)

**Route**: `/imports/{id}/clean`
**Header**: Step progress indicator showing "Clean" as active

**Screen Layout - All Valid**:

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back                     Clean (Step 3 of 5)                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ✓ Your data has been validated                                │
│    All 47 rows are ready for import                            │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                     [Next Step →]                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Screen Layout - Has Errors**:

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back                     Clean (Step 3 of 5)                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ⚠ You have 5 invalid rows that need to be fixed               │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  [All rows (47)]  |  [Error rows (5)]                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  Clean your data                                               │
│  Review each row and fix any issues                            │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ STATUS │ DATE       │ AMOUNT   │ ASSET │ CATEGORY │ ⋮    │ │
│  ├────────┼────────────┼──────────┼───────┼──────────┼──────┤ │
│  │   ✓    │ 01/15/2024 │ $1,000   │ AAPL  │ Dividend │      │ │
│  │   ✓    │ 01/14/2024 │ -$500    │ VTI   │ Buy      │      │ │
│  │   ⚠    │ [invalid]  │ $200     │ GOOG  │ Dividend │ [!]  │ │
│  │        │ ↳ Error: Date must match format MM/DD/YYYY       │ │
│  │   ⚠    │ 01/12/2024 │ [abc]    │ MSFT  │ Buy      │ [!]  │ │
│  │        │ ↳ Error: Amount must be a number                 │ │
│  │   ✓    │ 01/11/2024 │ $750     │ AMZN  │ Dividend │      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ◀ 1  2  3  4  5 ▶                    Showing 1-10 of 47      │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │   [Fix Errors Before Continuing]  (disabled)             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Inline Editing Pattern**:

- Each cell is directly editable (click to edit)
- Auto-submit on blur (no save button needed)
- Red border on invalid cells
- Error tooltip on hover/focus
- Validation runs immediately on field change
- Cell updates via Turbo/HTMX without full page reload

**Validation Rules**:

| Field | Validation | Error Message |
|-------|------------|---------------|
| Date | Matches configured format, between 1900-today | "Date must match format {format}" |
| Amount | Valid number after format parsing | "Amount must be a valid number" |
| Currency | Valid ISO 4217 code | "Invalid currency code" |
| Required fields | Not blank | "{Field} is required" |

**Error Display Patterns**:

- **Desktop**: Red border + tooltip on hover
- **Mobile**: Red error icon, tap to show error popup
- **Row expansion**: Show full error message below row on mobile

---

### 6.6 Step 5: Map Values

**Route**: `/imports/{id}/confirm`
**Header**: Step progress indicator showing "Map" as active

**Multi-Step Mapping** (for Transaction imports):

```
┌────────────────────────────────────────────────────────────────┐
│  Mapping Progress                                              │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐     │
│  │ 1. Categories  │ │ 2. Tags        │ │ 3. Accounts    │     │
│  │    ████████    │ │    ░░░░░░░░    │ │    ░░░░░░░░    │     │
│  │    Complete    │ │    Pending     │ │    Pending     │     │
│  └────────────────┘ └────────────────┘ └────────────────┘     │
└────────────────────────────────────────────────────────────────┘
```

**Category Mapping Screen**:

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back                      Map (Step 4 of 5)                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Map your categories                                           │
│  Match CSV categories to your portfolio categories             │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ CSV VALUE           │ MAP TO                    │ ROWS   │ │
│  ├─────────────────────┼───────────────────────────┼────────┤ │
│  │ Groceries           │ [+ Add as new category ▼] │   12   │ │
│  │ Coffee Shop         │ [Food & Dining       ▼]   │    8   │ │
│  │ Gas Station         │ [Transportation      ▼]   │    5   │ │
│  │ DIVIDEND            │ [Investment Income   ▼]   │   15   │ │
│  │ INTEREST            │ [+ Add as new category ▼] │    3   │ │
│  │ (blank)             │ [Leave unassigned    ▼]   │    4   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   [Next: Map Tags →]                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Dropdown Options**:

1. **"+ Add as new category"** - Creates new category with this name
2. **Existing categories** - Alphabetically sorted list
3. **"Leave unassigned"** - Skip mapping for these rows

**Account Mapping Screen** (for multi-account imports):

```
┌────────────────────────────────────────────────────────────────┐
│  Map your accounts                                             │
│  Assign each account in your CSV to an existing account        │
│                                                                │
│  ⚠ Some accounts need to be assigned                           │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ CSV VALUE           │ MAP TO                    │ ROWS   │ │
│  ├─────────────────────┼───────────────────────────┼────────┤ │
│  │ Schwab Brokerage    │ [Schwab Investment  ▼]    │   25   │ │
│  │ Schwab Checking     │ [Schwab Checking    ▼]    │   10   │ │
│  │ New Account XYZ     │ [── Select ──       ▼]    │    5   │ │
│  │                     │ [+ Create new account]    │        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │      [Assign All Accounts Before Continuing]  (disabled) │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Mapping Behavior**:

- Auto-submit on dropdown change (no save button)
- Try to auto-match by name (case-insensitive)
- Show row count to indicate impact
- "Create new account" opens inline modal for quick creation

---

### 6.7 Step 6: Review & Publish

**Route**: `/imports/{id}`
**Header**: Step progress indicator showing "Confirm" as active

**Dry Run Summary**:

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back                    Confirm (Step 5 of 5)               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Ready to import                                               │
│  Review what will be created                                   │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                                                           │ │
│  │  ┌────────────────────────────────┬──────────────────┐   │ │
│  │  │ Item                           │ Count            │   │ │
│  │  ├────────────────────────────────┼──────────────────┤   │ │
│  │  │ 📊 Transactions                │        47        │   │ │
│  │  │ 🏦 Accounts (new)              │         2        │   │ │
│  │  │ 📁 Categories (new)            │         3        │   │ │
│  │  │ 🏷️ Tags (new)                  │         5        │   │ │
│  │  └────────────────────────────────┴──────────────────┘   │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   [Publish Import]                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Processing State**:

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                    ◉ Import in progress                        │
│                                                                │
│  Your import is being processed. You can continue using        │
│  the app. Check back here or the imports menu for status.      │
│                                                                │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │  [Check Status]  │  │ [Back to Dashboard] │                │
│  └──────────────────┘  └──────────────────┘                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Success State**:

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                    ✓ Import successful                         │
│                                                                │
│  Your 47 transactions have been added to your portfolio.       │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │               [View Dashboard →]                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Failure State**:

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                    ✕ Import failed                             │
│                                                                │
│  There was an error processing your import. Please check       │
│  your file format and try again.                               │
│                                                                │
│  Error: Duplicate transaction found on row 23                  │
│                                                                │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │   [Try Again]    │  │ [Edit Import]    │                   │
│  └──────────────────┘  └──────────────────┘                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

### 6.8 Import History & Management

**Route**: `/imports`
**Location**: Settings menu

**Import List View**:

```
┌────────────────────────────────────────────────────────────────┐
│  Imports                                      [+ New Import]   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ✓ Complete │ Schwab Brokerage │ Transactions │ Jan 15    │ │
│  │            │ 47 records imported                    [⋮]  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ○ Pending  │ Fidelity 401k    │ Holdings     │ Jan 14    │ │
│  │            │ Waiting at Configure step              [⋮]  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ✕ Failed   │ Coinbase         │ Transactions │ Jan 10    │ │
│  │            │ Error: Invalid date format             [⋮]  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Status Badges**:

| Status | Color | Icon | Actions |
|--------|-------|------|---------|
| Pending | Gray | ○ | Resume, Delete |
| Importing | Orange (pulsing) | ◉ | View |
| Complete | Green | ✓ | View, Revert |
| Failed | Red | ✕ | Retry, Delete |

**Revert Confirmation Modal**:

```
┌────────────────────────────────────────────────────────────────┐
│  Revert import?                                        [✕]    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  This will delete the 47 transactions that were imported.     │
│  You will still be able to review and re-import your data.    │
│                                                                │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │     [Cancel]     │  │  [Revert Import] │                   │
│  └──────────────────┘  └──────────────────┘                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

### 6.9 Key UI Patterns Summary

| Pattern | Usage | Implementation |
|---------|-------|----------------|
| **Step-Based Wizard** | All import flows | Separate pages, header progress indicator |
| **Progressive Disclosure** | Configuration | Show/hide fields based on selections |
| **Inline Editing** | Clean step | Click-to-edit cells, auto-submit on blur |
| **Template Reuse** | Configuration | Detect previous config, offer one-click apply |
| **Dry Run Preview** | Before publish | Show counts of what will be created |
| **Auto-Submit** | Mapping dropdowns | No save button, submit on change |
| **Real-Time Validation** | Clean step | Immediate feedback, no page reload |

---

### 6.10 Number Format Handling

Support international number formats:

| Format | Example | Regions |
|--------|---------|---------|
| `1,234.56` | US, UK | Comma thousands, period decimal |
| `1.234,56` | Europe | Period thousands, comma decimal |
| `1 234,56` | France | Space thousands, comma decimal |
| `1,234` | Japan | Comma thousands, no decimal |

**Processing Logic**:

1. User selects format during configuration
2. System removes delimiter (thousands separator)
3. Replaces separator with period for parsing
4. Stores normalized decimal value

---

### 6.11 Error Handling Matrix

| Error Type | When | User Action |
|------------|------|-------------|
| Invalid CSV | Upload step | Re-upload corrected file |
| Missing required column | Configure step | Select correct column |
| Invalid date format | Clean step | Edit cell inline |
| Invalid amount | Clean step | Edit cell inline |
| Unmapped required field | Map step | Select from dropdown |
| Row limit exceeded | Publish step | Split into smaller imports |
| Processing error | Publish step | Retry or edit |

---

## 7. Accessibility Guidelines

### 7.1 Requirements (WCAG 2.1 AA)

- Color contrast: 4.5:1 for normal text, 3:1 for large text
- Focus states: Visible ring on all interactive elements
- Keyboard navigation: All actions accessible via keyboard
- Screen reader: ARIA labels on icons, charts, dynamic content
- Motion: Respect `prefers-reduced-motion`

### 7.2 Financial Data Accessibility

- Don't rely solely on color: Use icons (▲▼) in addition to green/red
- Provide text alternatives for charts
- Use `aria-live` for dynamic updates
- Clear number formatting with currency symbols

---

## 8. Responsive Breakpoints

```css
--screen-sm: 640px;   /* Mobile landscape */
--screen-md: 768px;   /* Tablet portrait */
--screen-lg: 1024px;  /* Tablet landscape */
--screen-xl: 1280px;  /* Desktop */
--screen-2xl: 1536px; /* Large desktop */
```

### Responsive Behavior

| Component | Mobile (<768px) | Tablet | Desktop |
|-----------|-----------------|--------|---------|
| Navigation | Hamburger | Collapsible | Full sidebar |
| Dashboard Grid | 1 column | 2 columns | 3-4 columns |
| Metric Cards | Full width | 2 per row | 4 per row |
| Charts | Full width, reduced | Full width | Inline |
| Data Tables | Horizontal scroll | Scroll | Full display |

---

## 9. Implementation Roadmap

### Phase 1: Design System Foundation

1. Implement CSS tokens and utilities
2. Create component macros (Jinja2)
3. Update base template with new navigation

### Phase 2: High-Impact Pages

1. Dashboard redesign
2. Wealth overview
3. Onboarding flow with walkthrough

### Phase 3: Data Management

1. Data Workbench wizard mode
2. Logic Studio tree interface
3. Integrations hub

### Phase 4: Reports & Polish

1. Report templates with consistent styling
2. D3.js chart upgrades
3. Dark mode (if time permits)

---

## 10. Critical Files for Implementation

| File | Purpose |
|------|---------|
| `/src/web_app/templates/base.html` | Base template - update first for new design system |
| `/src/web_app/static/css/style.css` | Replace with new design tokens |
| `/src/web_app/templates/dashboard/index.html` | Main dashboard - highest impact |
| `/maybe-finance/maybe/app/assets/tailwind/maybe-design-system.css` | Reference for tokens |
| `/maybe-finance/maybe/app/javascript/controllers/time_series_chart_controller.js` | Reference for D3.js charts |

---

## 11. Design Deliverables Checklist

- [ ] Figma/Sketch file with component library
- [ ] Color palette with all semantic tokens
- [ ] Typography scale reference
- [ ] Icon set selection and usage guide
- [ ] Page mockups for each key view
- [ ] Interactive prototype for onboarding flow
- [ ] Responsive breakpoint examples
- [ ] Accessibility checklist per component
