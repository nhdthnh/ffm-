import pandas as pd

sheets = pd.read_excel('log/db_log.xlsx', sheet_name=None)
print('Sheets:', list(sheets.keys()))
for s in sheets:
    print(f'\n--- Sheet: {s} ---')
    print('Columns:', sheets[s].columns.tolist())
    print(sheets[s].to_string())
