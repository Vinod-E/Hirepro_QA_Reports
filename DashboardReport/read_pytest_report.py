import json
import re
import html
import sys
from pathlib import Path

def read_pytest_report(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return

    content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Locate the JSON blob in the data-container
    match = re.search(r'id="data-container"\s+data-jsonblob="(.*?)"', content, re.DOTALL)
    if not match:
        print("Could not find data-jsonblob in the report.")
        return

    # Unescape HTML entities in the JSON string
    json_str = html.unescape(match.group(1))
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    tests = data.get("tests", {})
    
    pass_cases = []
    fail_cases = []
    
    for test_id, results in tests.items():
        # results is a list of results (for reruns)
        for result in results:
            status = result.get("result", "Unknown")
            if status == "Passed":
                pass_cases.append(test_id)
            elif status == "Failed":
                fail_cases.append(test_id)
                
    print(f"Summary for {path.name}:")
    print(f"Total Passed: {len(pass_cases)}")
    print(f"Total Failed: {len(fail_cases)}")
    print("-" * 30)
    
    if fail_cases:
        print("\nFAILED CASES:")
        for case in fail_cases:
            print(f"  - {case}")
            
    if pass_cases:
        print("\nPASSED CASES:")
        for case in pass_cases:
            print(f"  - {case}")

if __name__ == "__main__":
    report_file = ""
    if len(sys.argv) > 1:
        report_file = sys.argv[1]
    else:
        print("Please provide a report file path as an argument.")
        sys.exit(1)
    read_pytest_report(report_file)
