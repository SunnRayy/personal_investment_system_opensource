# 🗺️ Data Mapping Guide

> **Core Philosophy**: Data is messy; Logic is pure. The Mapping Layer is the bridge.

WealthOS adopts the **Adapter Pattern** to transform your diverse source data (Excel, CSV, API exports) into a standardized internal data structure that the system understands.

This guide will help you configure `config/column_mapping.yaml`, enabling WealthOS to seamlessly ingest your financial data, whether it comes from a broker's CSV export or a manually maintained spreadsheet.

---

## 1. Core Concept: Decoupling Data and Logic

In traditional financial scripts, code is often riddled with hardcoded column names (e.g., `if row['My Stock Code'] ...`). If you change a column header in Excel, the code breaks.

WealthOS fundamentally changes this. The system core (Analytics Engine) interacts **only** with **Internal Keys**, indifferent to your original headers.

**The Workflow:**

```mermaid
graph LR
    A[Your Data Source] -->|Mapping Profile| B(Mapping Layer)
    B -->|Standardization| C[Internal Schema]
    C -->|Calculation| D[Analytics Engine]
```

* **Source Data**: Your bank statement or manual ledger (headers may be in Chinese, English, or abbreviations).
* **Mapping Profile**: The translation dictionary. It tells the system "Source Column A" maps to "Internal Key X".
* **Internal Schema**: The system's built-in standard fields (e.g., `Asset_ID`, `Market_Value_Raw`).

---

## 2. Step-by-Step: Defining Your Profile

All mapping configurations are located in `config/column_mapping.yaml`.

### Step 1: Identify the Source

Define a unique `profile_name` for every file you intend to import. For example, you might have one profile for your manual Excel ledger and another for a Schwab CSV export.

### Step 2: Edit `column_mapping.yaml`

Configure the file using the format `internal_key: source_column_name`.

**Configuration Example:**

```yaml
# config/column_mapping.yaml

profiles:
  # Scenario A: Your manually maintained Excel
  my_manual_excel:
    format: "excel"
    sheet_name: "Holdings"
    header_row: 0
    columns:
      # Internal Key      # Your Excel Header
      Asset_ID:           "Code"
      Asset_Name:         "Name"
      Market_Value_Raw:   "Current Value"
      Cost_Basis:         "Total Cost"
      Date:               "Record Date"
      Currency:           "Curr"

  # Scenario B: Broker CSV Export (e.g., Schwab)
  schwab_export:
    format: "csv"
    columns:
      Asset_ID:           "Symbol"
      Asset_Name:         "Description"
      Quantity:           "Qty"
      Price_Unit:         "Last Price"
      Market_Value_Raw:   "Market Value"
```

### Step 3: Load Data

When running the import script, specify which profile to use:

```bash
# Pseudo-command example
python main.py import --file "./downloads/schwab.csv" --profile "schwab_export"
```

---

## 3. Internal Schema Reference

To ensure the system correctly calculates returns, risk, and asset allocation, map your columns to as many of the following standard keys as possible.

### Core Fields

| Internal Key | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| **`Asset_ID`** | String | ✅ | **Unique Identifier**. Ticker (AAPL, 000300), fund code, or custom ID. Used to link transaction history. |
| **`Date`** | Date | ✅ | **Data Date**. The transaction date or the snapshot date. Format `YYYY-MM-DD` is preferred. |
| **`Asset_Name`** | String | ⚪ | Human-readable name for reports. If missing, the system often defaults to `Asset_ID`. |

### Holdings Specific

| Internal Key | Type | Description |
| :--- | :--- | :--- |
| **`Market_Value_Raw`** | Float | **Raw Market Value**. Calculated as `Quantity * Price`. This is the basis for asset allocation. |
| **`Quantity`** | Float | Number of shares/units held. |
| **`Price_Unit`** | Float | Price per unit/share. |
| **`Cost_Basis`** | Float | Total cost basis (Optional). If provided, system uses it for unrealized P&L; otherwise, it calculates via FIFO from transactions. |

### Transactions Specific

| Internal Key | Type | Description |
| :--- | :--- | :--- |
| **`Transaction_Type`** | String | **Action Type**. Standard values: `Buy`, `Sell`, `Dividend`, `Interest`. The system attempts to normalize your raw types. |
| **`Amount_Net`** | Float | **Net Amount**. Actual cash flow. Buys are typically negative (outflow), Sells are positive (inflow). |
| **`Fee`** | Float | Transaction fees or commissions. |

### Auxiliary Fields

| Internal Key | Type | Description |
| :--- | :--- | :--- |
| **`Currency`** | String | **Currency Code** (USD, CNY, HKD). If missing, defaults to the system base currency (CNY). |
| **`Account`** | String | Account identifier. E.g., "Chase Bank", "Schwab". Used for pivot analysis. |
| **`Tag`** | String | Custom tags for specific filtering rules. |

---

## 4. Best Practices & Advanced Techniques

### 4.1 Multi-Currency Handling

WealthOS includes automatic FX conversion, but it needs to know the source currency.

* **Method A (Recommended): Explicit Column Mapping**
    If your source file has a currency column (e.g., a column named "Curr" with values like "USD"), map it to the internal key `Currency`.

    ```yaml
    columns:
      Market_Value_Raw: "Value"
      Currency: "Curr"  # Values must be standard codes like USD, CNY
    ```

* **Method B: Profile-Level Injection**
    If a file contains purely USD assets (e.g., a US brokerage export) but lacks a currency column, you can inject a default value via the mapping logic (requires importer support) or simply add a column to your source CSV.

### 4.2 Handling Broker Differences

Different brokers name concepts differently.

* Broker A uses `Symbol`, Broker B uses `Stock Code` -> Both map to `Asset_ID`.
* Broker A uses `Market Value`, Broker B uses `Ending Balance` -> Both map to `Market_Value_Raw`.

**Tip**: Never modify the source file structure to fit the code. Instead, create a separate Profile for each broker.

### 4.3 Transaction Normalization

Source data transaction types vary wildly (e.g., "Bought", "Sold", "Div Reinv", "Purchase").

The Mapping Layer aligns column names. **Value Normalization** happens in the cleaning stage (`cleaners.py`), but the mapping is the gateway.

* Ensure `Transaction_Type` is mapped.
* **Sign Convention**: WealthOS standardizes **Cash Outflows (Buys) as Negative** and **Cash Inflows (Sells/Dividends) as Positive**.
  * *Advice*: If your source data lists Buy amounts as positive, ensure there is a column indicating direction (Buy/Sell) so the system logic can flip the sign, or verify the `Amount_Net` mapping logic in the cleaner.

### 4.4 Debugging Mappings

If data appears empty or fields are misaligned after import:

1. Check indentation in `config/column_mapping.yaml`.
2. Verify source headers for **hidden spaces** (e.g., `"Symbol "` vs `"Symbol"`).
3. Check the logs. The system will typically warn: *"Column X not found in source file"*.
