# HirePro Quality Insights Dashboard

A premium, high-performance automation reporting ecosystem designed to provide a unified view of UI, API, and Performance test cycles. This dashboard transforms raw test data (HTML, Excel, JSON) into actionable insights with a focus on visual excellence and data integrity.

## 🚀 Key Features

-   **Unified Dashboard**: Consolidates reports from Playwright, Cypress, Pytest, Newman, and Mochawesome.
-   **Performance Tracking**: Historical trend analysis for API response times with interactive Chart.js visualizations.
-   **Liquid Glass UI**: A modern, responsive interface featuring glassmorphism, dynamic transitions, and dark/light mode support.
-   **Data Sanitization**: Automatic masking of PII (emails, phone numbers, Aadhaar/PAN) and sensitive internal URLs before deployment.
-   **CI/CD Integrated**: Automated generation and deployment via GitHub Actions with Google Chat notifications.
-   **Integrity Checks**: Real-time detection of missing reports or stalled execution based on master manifests.

## 📂 Project Structure

```bash
├── Config/                # Centralized configuration (paths, baselines)
├── DashboardReport/       # Core generators (Dashboard, Performance, Utilities)
├── GoogleChat/            # Notification logic and webhook triggers
├── reports/               # Date-wise storage for individual test reports
├── PerformanceReports/    # Excel-based performance logs
├── dashboard.html         # Landing page (Report selection)
├── automationreports.html # Main automation metrics dashboard
└── performance.html       # API performance trend analytics
```

## 🛠️ Setup & Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd Hirepro_QA_Reports
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Secrets**:
    Copy the template and fill in your webhook details:
    ```bash
    cp Config/secrets_config.ini.template Config/secrets_config.ini
    # Edit Config/secrets_config.ini with your live keys
    ```

## 📈 Usage

### Generating Dashboards
Run the generators to sync the latest reports from the `reports/` and `PerformanceReports/` directories:
```bash
# Generate main automation dashboard
python3 DashboardReport/generate_dashboard.py

# Generate performance trend dashboard
python3 DashboardReport/generate_performance.py
```

### Sending Notifications
To trigger the Google Chat notification based on the latest generated dashboard:
```bash
python3 GoogleChat/trigger_notification.py
```

## 🤖 CI/CD Workflow

The project includes a GitHub Action ([Dashboard_Report.yml](.github/workflows/Dashboard_Report.yml)) that:
1.  Sets up the Python environment (3.12).
2.  Injects the `secrets_config.ini` from GitHub Secrets.
3.  Generates all HTML dashboards.
4.  Sends a summary card to Google Chat.
5.  Auto-commits and pushes the updated HTML pages to the repository.

## 🛡️ Security & Privacy

-   **Auto-Masking**: All HTML reports processed by `generate_dashboard.py` undergo a sanitization pass to ensure no sensitive HirePro internal data or customer PII is exposed in the final web view.
-   **Secret Management**: The `secrets_config.ini` is strictly gitignored to prevent credential leaks.

---
© 2026 HirePro Technologies Pvt. Ltd. All rights reserved.
