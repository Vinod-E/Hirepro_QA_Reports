import os
import sys
from bs4 import BeautifulSoup
from GoogleChat import notify
from Config import configfile

def trigger():
    dashboard_path = configfile.DASHBOARD_REPORT
    if not os.path.exists(dashboard_path):
        print(f"Error: {dashboard_path} not found.")
        return

    with open(dashboard_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Find the active day-view
    active_view = soup.find('div', class_='day-view active')
    if not active_view:
        print("Error: Active day-view not found.")
        return

    # Get stats from the active view's stat-grid
    stats_cards = active_view.find_all('div', class_='stat-card')
    
    total_tcs = 0
    passed_testcases = 0
    actual_reports = 0
    expected_reports = None 

    for card in stats_cards:
        label = card.find('span', class_='label').text.strip()
        value = card.find('span', class_='value').text.strip()
        
        label_upper = label.upper()
        if "EXECUTED" in label_upper:
            total_tcs = int(value)
        elif "PASSED" in label_upper:
            passed_testcases = int(value)
        elif "REPORTS" in label_upper:
            if "/" in value:
                parts = value.split("/")
                actual_reports = int(parts[0].strip())
                expected_reports = int(parts[1].strip())
            else:
                actual_reports = int(value)

    # Extract the execution goal (Target TCs) from the Hero section
    expected_tcs = None
    hero_val = soup.find('div', class_='hero-value')
    if hero_val:
        goal_text = hero_val.find('span', class_='hero-target')
        if goal_text:
            try:
                # Remove non-numeric characters to get "2687"
                clean_goal = "".join(filter(str.isdigit, goal_text.text))
                if clean_goal:
                    expected_tcs = int(clean_goal)
            except: pass

    # If parsing failed, use central config as fallback
    if expected_reports is None: expected_reports = configfile.EXPECTED_REPORT_COUNT
    if expected_tcs is None: expected_tcs = configfile.TARGET_EXECUTION_GOAL

    # Count passed suites (suites with presence) IN THE ACTIVE VIEW
    passed_suites = actual_reports

    # Basic info from central config
    env = configfile.ENVIRONMENT
    sprint = configfile.EXPECTED_SPRINT
    suite_name = configfile.AUDIT_SUITE_NAME

    print(f"Parsed Dashboard Context:")
    print(f"  Target TCs: {expected_tcs}")
    print(f"  Expected Reports: {expected_reports}")
    print(f"  Execution Goal Reached: {passed_testcases}/{total_tcs}")

    # Extract Commit ID from footer
    commit_id = "Unknown"
    commit_badge = soup.find('span', class_='commit-badge')
    if commit_badge:
        commit_id = commit_badge.text.strip()

    status_code = notify.send_google_chat_report(
        env=env,
        sprint=sprint,
        suite_name=suite_name,
        total_suites=expected_reports,
        expected_suites=expected_reports,
        passed_suite=passed_suites,
        total_tcs=total_tcs,
        passed_testcases=passed_testcases,
        expected_tcs=expected_tcs,
        commit_id=commit_id
    )

    if status_code == 200:
        print("Success: Google Chat notification sent.")
    else:
        print(f"Error: Failed to send notification (Status: {status_code})")

if __name__ == "__main__":
    trigger()
