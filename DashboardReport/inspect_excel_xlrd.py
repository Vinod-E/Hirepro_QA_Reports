import xlrd
import os

REPORTS_DIR = '../reports'

def inspect_xlrd(filename):
    print(f"--- Inspecting {filename} ---")
    try:
        workbook = xlrd.open_workbook(os.path.join(REPORTS_DIR, filename))
        sheet = workbook.sheet_by_index(0)
        
        # Print header
        header = [sheet.cell_value(0, i) for i in range(sheet.ncols)]
        print("Header:", header)
        
        # Look for status columns
        status_cols = [i for i, h in enumerate(header) if 'status' in str(h).lower() or h == 'Actual_status']
        
        counts = {}
        for col_idx in status_cols:
            col_name = header[col_idx]
            col_values = [sheet.cell_value(row, col_idx) for row in range(1, sheet.nrows)]
            print(f"Counts for {col_name}:")
            from collections import Counter
            print(Counter(col_values))
            
    except Exception as e:
        print(f"Error: {e}")

inspect_xlrd('API_Assessment_Slot.xls')
inspect_xlrd('API_UploadCandidates.xls')
inspect_xlrd('UI_RAZORPAY_REGISTRATION.xls')
