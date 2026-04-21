import os
import platform

# Detect if the OS is Windows
IS_WINDOWS = platform.system() == "Windows"

# Get home directory in a cross-platform way
if IS_WINDOWS:
    # Windows: C:\Users\<Username>\Desktop
    username = os.getenv("USERNAME") or "user"
    HOME_PATH = os.path.join("C:\\Users", username, "Desktop")
else:
    # Linux/macOS (incl. GitHub Actions): /home/<username>
    HOME_PATH = os.path.expanduser("~")

# Construct automation path
AUTOMATION_PATH = os.path.join(HOME_PATH, "hirepro_automation", "Hirepro_QA_Reports")


# Paths
REPORT_DIR = os.path.join(AUTOMATION_PATH, "reports")
CONFIG_DIR = os.path.join(AUTOMATION_PATH, "Config", "secrets_config.ini")
DASHBOARD_REPORT = os.path.join(AUTOMATION_PATH, "automationreports.html")
PERFORMANCE_DIR = os.path.join(AUTOMATION_PATH, "PerformanceReports")
GET_PERFORMANCE_REPORT = os.path.join(PERFORMANCE_DIR, "GET_PERFORMANCE_API_REPORT.xlsx")
SET_PERFORMANCE_REPORT = os.path.join(PERFORMANCE_DIR, "SET_PERFORMANCE_API_REPORT.xlsx")
PERFORMANCE_HTML = os.path.join(AUTOMATION_PATH, "performance.html")

# Ensure report directory exists
os.makedirs(REPORT_DIR, exist_ok=True)

# Slash based on OS
SLASH = '\\' if IS_WINDOWS else '/'

# --- Audit & Notification Baselines ---
EXPECTED_REPORT_COUNT = 72
TARGET_EXECUTION_GOAL = 2901
EXPECTED_SPRINT = "217"
ENVIRONMENT = "QA"
AUDIT_SUITE_NAME = "Daily Run | Central QA Automation Reports"
MASTER_REPORTS_LIST = os.path.join(AUTOMATION_PATH, "DashboardReport", "master_reports.txt")
