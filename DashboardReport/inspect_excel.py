import pandas as pd
import os

REPORTS_DIR = '../reports'

def inspect(filename):
    print(f"--- Inspecting {filename} ---")
    try:
        df = pd.read_excel(os.path.join(REPORTS_DIR, filename))
        print("Columns:", df.columns.tolist())
        print("Head:")
        print(df.head(10))
        # Look for status column
        for col in df.columns:
            if 'status' in str(col).lower():
                print(f"Status counts in {col}:")
                print(df[col].value_counts())
    except Exception as e:
        print(f"Error: {e}")

inspect('API_Assessment_Slot.xls')
inspect('API_UploadCandidates.xls')
inspect('UI_RAZORPAY_REGISTRATION.xls')
