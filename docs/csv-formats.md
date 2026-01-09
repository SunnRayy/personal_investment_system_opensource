# CSV Import Formats

This guide describes the supported CSV formats for importing data into the Personal Investment System.

## Supported File Types

- **CSV** (`.csv`) - Comma-separated values, auto-detects delimiter
- **Excel** (`.xlsx`, `.xls`) - Microsoft Excel spreadsheets

## Transactions Format

Import investment transactions including purchases, sales, dividends, and transfers.

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Date` | Transaction date | `2024-01-15` or `01/15/2024` |
| `Amount` | Transaction amount (negative for outflows) | `-1500.00` |

### Optional Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Description` | Transaction description | `Stock Purchase - AAPL` |
| `Category` | Transaction category/type | `Investment`, `Income` |
| `Account` | Account name | `Brokerage`, `IRA`, `401k` |
| `Symbol` | Stock/fund symbol | `AAPL`, `VTI` |
| `Quantity` | Number of shares/units | `10` |
| `Price` | Price per share | `150.00` |
| `Notes` | Additional notes | `Quarterly dividend` |

### Example CSV

```csv
Date,Description,Amount,Category,Account,Notes
2024-01-15,Stock Purchase - AAPL,-1500.00,Investment,Brokerage,Buy 10 shares
2024-01-20,Dividend - VTI,45.23,Income,Brokerage,Quarterly dividend
2024-02-01,401k Contribution,-500.00,Retirement,401k,Monthly contribution
2024-02-15,Salary Deposit,5000.00,Income,Checking,Monthly salary
```

## Holdings Format

Import current portfolio holdings with cost basis information.

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Symbol` | Stock/fund symbol | `AAPL` |
| `Quantity` | Number of shares/units | `50` |

### Optional Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Name` | Asset name | `Apple Inc` |
| `Cost_Basis` | Total cost basis | `7500.00` |
| `Current_Price` | Current market price | `185.50` |
| `Account` | Account name | `Brokerage` |
| `Asset_Type` | Asset classification | `US Stock`, `ETF` |

### Example CSV

```csv
Symbol,Name,Quantity,Cost_Basis,Current_Price,Account,Asset_Type
AAPL,Apple Inc,50,7500.00,185.50,Brokerage,US Stock
VTI,Vanguard Total Stock Market,100,20000.00,225.30,IRA,ETF
BND,Vanguard Total Bond,75,7500.00,72.50,401k,Bond ETF
```

## Balance Sheet Format

Import net worth snapshots with assets and liabilities.

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Date` | Snapshot date | `2024-01-01` |
| `Category` | Asset/liability category | `Asset_Investment` |
| `Amount` | Value (negative for liabilities) | `150000.00` |

### Optional Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Item` | Item description | `Stocks and ETFs` |
| `Type` | Asset or Liability | `Asset` |

### Example CSV

```csv
Date,Category,Item,Amount,Type
2024-01-01,Asset_Investment,Stocks and ETFs,150000.00,Asset
2024-01-01,Asset_Cash,Savings Account,30000.00,Asset
2024-01-01,Liability_Debt,Mortgage,-180000.00,Liability
```

## Date Formats

The system auto-detects common date formats:

- `YYYY-MM-DD` (ISO format, recommended): `2024-01-15`
- `MM/DD/YYYY`: `01/15/2024`
- `DD/MM/YYYY`: `15/01/2024`
- `YYYY/MM/DD`: `2024/01/15`

## Amount Formats

Amounts can include:

- Plain numbers: `1500.00`
- Currency symbols: `$1,500.00` or `¥1,500.00`
- Negative values: `-1500.00` or `(1500.00)`
- Thousand separators: `1,500.00`

## Encoding

- **UTF-8** (recommended)
- **UTF-8 with BOM**
- **ISO-8859-1** (Latin-1)

The system auto-detects file encoding.

## Column Mapping

If your columns have different names, the system provides a mapping interface:

1. Upload your file
2. Match your columns to the expected format
3. Preview the data
4. Confirm and import

## Tips

1. **Start with templates**: Download the template files from the upload page
2. **Check date formats**: Ensure dates are consistent
3. **Use UTF-8**: Save files as UTF-8 to avoid character issues
4. **Remove empty rows**: Clean up trailing empty rows before import
5. **Consistent accounts**: Use the same account names across files

## Troubleshooting

### "Invalid date format" Error

- Check that all dates are valid
- Remove any empty date cells
- Use a consistent date format

### "Invalid amount" Error

- Remove any non-numeric characters except: `$`, `¥`, `,`, `.`, `-`, `(`, `)`
- Check for spaces in numbers

### "File too large" Error

- Maximum file size is 50MB
- For large files, split into multiple smaller files
