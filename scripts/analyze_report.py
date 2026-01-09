import pandas as pd

report_path = 'output/calibration_report.xlsx'
try:
    df = pd.read_excel(report_path, sheet_name='Discrepancies')
    print(f"Loaded {len(df)} discrepancies.")
    print(f"Columns: {list(df.columns)}")
    
    # Sort by absolute Value_Diff
    df['Abs_Diff'] = df['Value_Diff'].abs()
    top_diffs = df.sort_values('Abs_Diff', ascending=False).head(10)
    
    print("\nAll Discrepancies:")
    # Use available columns
    cols = ['Asset_ID', 'Excel_Quantity', 'DB_Quantity', 'Excel_Market_Value', 'DB_Market_Value', 'Value_Diff', 'Value_Diff_Pct']
    if 'Asset_Name' in df.columns: cols.insert(1, 'Asset_Name')
    print(df[cols].sort_values('Value_Diff', ascending=True).to_string())
    
    print("\n--- Categorization ---")
    missing_in_db = df[df['DB_Quantity'] == 0]
    print(f"Missing in DB ({len(missing_in_db)}): {missing_in_db['Asset_ID'].tolist()}")
    
    missing_in_excel = df[df['Excel_Quantity'] == 0]
    print(f"Missing in Excel ({len(missing_in_excel)}): {missing_in_excel['Asset_ID'].tolist()}")
    
    valuation_diff = df[(df['DB_Quantity'] != 0) & (df['Excel_Quantity'] != 0)]
    print(f"Valuation Differences ({len(valuation_diff)}): {valuation_diff['Asset_ID'].tolist()}")

except Exception as e:
    print(f"Error reading report: {e}")
