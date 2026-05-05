import pandas as pd
import json
import sys
import os
from datetime import datetime
# Add parent directory to sys.path to find Config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Config import configfile

import subprocess

def get_git_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except:
        return "N/A"

def process_all_sheets(file_path):
    if not os.path.exists(file_path):
        return {}
    
    xl = pd.ExcelFile(file_path)
    sheets_data = {}
    
    for sheet_name in xl.sheet_names:
        if sheet_name in ["BETA_SG", "BETA_EU", "AMS_SG", "AMS_EU"]:
            continue
        
        df = pd.read_excel(xl, sheet_name=sheet_name)
        
        # Ensure Run Date is treated as string for grouping/consistency if it's already a datetime
        df['Run Date'] = df['Run Date'].astype(str)
        
        # Get the last 5 unique dates
        unique_dates = df['Run Date'].unique()
        last_5_dates = unique_dates[-5:]
        
        # Filter for only those dates
        df_filtered = df[df['Run Date'].isin(last_5_dates)].copy()
        
        # If there are multiple runs on the same date, take the latest run for each date
        # Assuming higher index means later run
        df_last_5 = df_filtered.drop_duplicates(subset=['Run Date'], keep='last')
        
        report_data = []
        
        for _, row in df_last_5.iterrows():
            row_entry = {
                "sprint": str(row.get("Sprint", "")),
                "run_date": str(row.get("Run Date", "")),
                "hits": int(row.get("Number of hits", 0)) if pd.notnull(row.get("Number of hits")) else 0,
                "apis": []
            }
            
            # Filter out "Unnamed" columns
            cols = [c for c in df.columns if not str(c).startswith("Unnamed")]
            
            # Only take data columns (starting from index 5)
            # Threshold, Current, Variation
            for i in range(5, len(cols) - 2, 3):
                threshold_col = cols[i]
                current_col = cols[i+1]
                variation_col = cols[i+2]
                
                if any(pd.isnull(c) for c in [threshold_col, current_col, variation_col]):
                    continue

                api_name = str(current_col).replace(" Previous sprint(%)", "").replace(" Threshold", "").strip()
                
                try:
                    thresh_val = float(row[threshold_col]) if pd.notnull(row[threshold_col]) else 0
                    curr_val = float(row[current_col]) if pd.notnull(row[current_col]) else 0
                    var_val = float(row[variation_col]) if pd.notnull(row[variation_col]) else 0
                    
                    row_entry["apis"].append({
                        "name": api_name,
                        "threshold": thresh_val,
                        "current": curr_val,
                        "variation": var_val
                    })
                except (ValueError, TypeError):
                    continue
            
            report_data.append(row_entry)
        
        report_data.reverse() # Latest first
        sheets_data[sheet_name] = report_data
        
    return sheets_data

# Process both reports
get_data = process_all_sheets(configfile.GET_PERFORMANCE_REPORT)
set_data = process_all_sheets(configfile.SET_PERFORMANCE_REPORT)

final_data = {
    "GET": get_data,
    "SET": set_data,
    "environments": list(get_data.keys()) if get_data else []
}

# Latest update date
latest_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/png" href="https://lh3.googleusercontent.com/proxy/98it6d0vGqaPttxE8ImrHhVvaz5XpPeZ7qiXHcnm9PiPrwTBGvZcWp2vdQVdgZt5b7Vfu7kXnkh6mrKs_q_JIE5GGlw8uRAOeSvJOEtgNXWrXgOoGjGFCnKCA1gITLLZKNxv1mV6szDHEnNLK7RbJnfk-eFMZPlGXRpU2iKeBGr2Gm3-i_Lnv-IVisLlJwRR55nNMx9HndfYnmLOlraDHGgp9Rc7V4pNO1N8S1ZugYR5SUVMi8K_WGFwvYWsEh2cEnW6x-Zw-ncSM27yX509d6pmuUvfohenPAxHMNORCeWO">
    <title>Daily Performance Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');
        
        :root {
            --primary: #FF6B00;
            --primary-gradient: linear-gradient(135deg, #FF6B00 0%, #FF9E00 100%);
            --bg: #fdfdfd;
            --card-bg: #ffffff;
            --text: #000000;
            --text-main: #000000;
            --text-dim: #1a1a1a;
            --border: #f1f5f9;
            --success: #10b981;
            --danger: #ef4444;
            --glass: rgba(255, 255, 255, 0.8);
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.02);
            --shadow-md: 0 10px 15px -3px rgba(0,0,0,0.05);
            --shadow-lg: 0 20px 25px -5px rgba(0,0,0,0.05);
        }

        * { 
            margin: 0; padding: 0; box-sizing: border-box; 
            font-family: 'Outfit', sans-serif; 
            -webkit-tap-highlight-color: transparent;
        }

        html, body {
            scrollbar-width: none;
            -ms-overflow-style: none;
            overflow-x: hidden;
            scroll-behavior: smooth;
        }
        html::-webkit-scrollbar, body::-webkit-scrollbar {
            display: none;
        }
        body {
            background-color: #ffffff;
            color: var(--text-main);
            min-height: 100vh;
        }

        header {
            padding: 10px 0;
            background: white;
        }

        .header-container {
            max-width: 1300px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            padding: 10px 20px;
            border-bottom: 1px solid #D9D7D7;
        }

        .logo-section { display: flex; align-items: center; gap: 1rem; justify-self: start; }
        .logo-img { height: 35px; }
        
        .title-section { text-align: center; }
        .title-section h1 { font-size: 1.6rem; font-weight: 800; color: #000000; line-height: 1.2; }
        .subtitle { font-size: 0.85rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

        .audit-section { justify-self: end; text-align: right; }
        .audit-label { font-size: 0.7rem; color: #64748b; font-weight: 700; }
        .audit-time { 
            font-weight: 800; 
            font-size: 0.9rem; 
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 6px;
        }

        .header-home-btn {
            display: none;
            width: 38px;
            height: 38px;
            background: rgba(255, 107, 0, 0.1);
            color: var(--primary);
            border-radius: 10px;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            font-size: 1.2rem;
            margin-bottom: 8px;
            transition: all 0.3s;
        }
        .header-home-btn:active { transform: scale(0.9); background: var(--primary); color: white; }

        main { max-width: 1300px; margin: 10px auto; padding: 0 20px; }
        #report-content { 
            transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Multi-level Navigation */
        .nav-container {
            display: flex;
            flex-direction: column;
            gap: 25px;
            margin-bottom: 30px;
            align-items: center;
        }

        .nav-group {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            width: 100%;
        }

        .nav-label {
            font-size: 0.65rem;
            font-weight: 800;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.15em;
        }

        .glass-nav {
            display: inline-flex;
            background: #f1f5f9;
            padding: 5px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.03);
            position: relative;
            gap: 4px;
        }

        .nav-btn {
            padding: 12px 32px;
            border-radius: 12px;
            border: none;
            background: transparent;
            color: #64748b;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .nav-btn i { font-size: 1rem; opacity: 0.8; transition: transform 0.3s ease; }
        .nav-btn:hover { color: var(--primary); background: rgba(255, 107, 0, 0.04); }
        .nav-btn:hover i { transform: translateY(-1px); }
        .nav-btn:active { transform: scale(0.97); }

        .nav-btn.active {
            background: white;
            color: var(--primary);
            box-shadow: 0 4px 20px rgba(255, 107, 0, 0.12), 0 2px 5px rgba(0,0,0,0.05);
            transform: translateY(0);
        }

        .env-nav .nav-btn {
            padding: 8px 18px;
            font-size: 0.75rem;
            border-radius: 10px;
        }
        .env-nav .nav-btn.active {
            box-shadow: 0 4px 12px rgba(255, 107, 0, 0.1);
        }

        /* Content Sections */
        .report-section { display: none; animation: fadeIn 0.4s ease; }
        .report-section.active { display: block; }
        .mobile-only-label { display: none; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .section-title {
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding-bottom: 8px;
        }

        @media (max-width: 768px) {
            .section-title { flex-wrap: wrap; justify-content: center; text-align: center; gap: 16px; font-size: 1rem; }
            .section-title div { white-space: nowrap; }
            .section-title span { margin-left: 0; }
        }

        .section-card {
            background: white;
            border-radius: 16px;
            padding: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 20px rgba(0,0,0,0.02);
            margin-bottom: 20px;
        }

        .chart-container { height: 400px; position: relative; }
        .chart-section { display: none; padding-top: 20px; }
        .chart-section.active { display: block; }
        
        .toggle-graph-btn {
            background: #f1f5f9;
            color: var(--primary);
            border: 1px solid #e2e8f0;
            padding: 6px 14px;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .toggle-graph-btn:hover { background: #e2e8f0; color: var(--primary); }
        .toggle-graph-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

        /* Custom Legend */
        .commit-badge { background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 6px; font-family: monospace; font-weight: 700; color: #0f172a; border: 1px solid var(--border); font-size: 0.75rem; }
        .home-btn {
            position: fixed; right: 1.5rem; width: 42px; height: 42px; 
            background: var(--primary); color: white; border-radius: 14px; 
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 10px 30px rgba(255, 107, 0, 0.3);
            z-index: 9999; border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            text-decoration: none; font-size: 1.1rem;
            backdrop-filter: blur(8px);
        }
        .home-btn { bottom: calc(50% + 25px); }

        
        .home-btn:hover { transform: scale(1.1) translateX(-5px); box-shadow: 0 15px 40px rgba(255, 107, 0, 0.45); }
        .home-btn i { transition: transform 0.3s ease; }
        .home-btn:hover i { transform: rotate(-10deg); }
        .home-btn:active { transform: scale(0.9); }

        .custom-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 25px;
            justify-content: center;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            background: white;
            border: 1px solid var(--border);
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .legend-item.hidden { opacity: 0.5; grayscale: 1; }

        .legend-dot { 
            width: 12px; 
            height: 12px; 
            border-radius: 50%; 
            border: 2.5px solid;
            background: transparent;
        }

        /* Table Styles */
        .data-table-container { overflow-x: auto; margin-top: 20px; }
        table { width: 100%; border-collapse: separate; border-spacing: 0 8px; }
        th { text-align: left; padding: 12px 15px; font-size: 0.7rem; text-transform: uppercase; color: #64748b; font-weight: 800; }
        td { padding: 15px; background: #fff; border-top: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; }
        tr td:first-child { border-left: 1px solid #f1f5f9; border-radius: 12px 0 0 12px; }
        tr td:last-child { border-right: 1px solid #f1f5f9; border-radius: 0 12px 12px 0; }
        
        tr:hover td { background: #fffcf9; border-color: #fee2e2; }

        .api-name { font-weight: 700; font-size: 0.9rem; }
        .val-badge { 
            padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 800;
            display: inline-block;
        }
        .val-pass { background: #d1fae5; color: #065f46; }
        .val-fail { background: #fee2e2; color: #991b1b; }

        .variation { font-weight: 700; font-size: 0.8rem; }
        .var-up { color: #ef4444; }
        .var-down { color: #10b981; }

        .text-orange { color: var(--primary) !important; }

        .chart-header {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
            margin-top: -10px;
        }
        .axis-label {
            font-size: 0.7rem;
            font-weight: 800;
            color: #94a3b8;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .legend-controls {
            display: flex;
            gap: 8px;
        }

        .control-btn {
            padding: 10px 22px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 800;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid transparent;
        }
        .control-btn i { font-size: 0.8rem; }

        .toggle-btn {
            background: #eff6ff;
            color: #2563eb;
            border: 1px solid #dbeafe;
            padding: 10px 24px;
            border-radius: 14px;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 20px;
        }
        .toggle-btn:hover { background: #dbeafe; transform: translateY(-2px); }
        .toggle-btn:active { transform: scale(0.95); }

        .api-visibility-label {
            font-size: 0.75rem;
            font-weight: 800;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 15px;
            text-align: center;
        }

        @media (min-width: 769px) {
            .toggle-btn, .api-visibility-label {
                display: none;
            }
            .chart-header {
                flex-direction: row;
                justify-content: flex-end;
                align-items: center;
                margin-top: 0;
                margin-bottom: 20px;
            }
            #controlsWrapper {
                flex-direction: row !important;
                justify-content: flex-end !important;
                gap: 20px;
                width: 100%;
            }
        }

        .btn-select {
            background: #fff7ed;
            color: #f97316;
            border-color: #ffedd5;
        }

        .btn-select:hover {
            background: #ffedd5;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(249, 115, 22, 0.1);
        }

        .btn-clear {
            background: #f1f5f9;
            color: #64748b;
            border-color: #e2e8f0;
        }

        .btn-clear:hover {
            background: #e2e8f0;
            color: #475569;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(100, 116, 139, 0.1);
        }



        /* Environment Cards */
        .env-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .env-card {
            padding: 20px;
            background: white;
            border: 1px solid var(--border);
            border-radius: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .env-card.active {
            border-color: #2563eb;
            background: #eff6ff;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
        }
        .env-card h3 { font-size: 1rem; font-weight: 800; margin-bottom: 5px; }
        .env-card p { font-size: 0.7rem; color: #64748b; font-weight: 600; }

        footer {
            margin-top: 50px; padding: 30px 20px; border-top: 1px solid #f1f5f9;
            color: #64748b; font-size: 0.85rem; font-weight: 700;
        }
        .footer-container {
            max-width: 1300px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }



        @media (max-width: 768px) {
            .header-container { grid-template-columns: 1fr; gap: 1rem; }
            .logo-section { justify-self: center; flex-direction: column; }
            .title-section h1 { font-size: 1.3rem; }
            .audit-section { justify-self: center; text-align: center; }
            main { padding: 0 10px; }
            .home-btn { display: none !important; }
            .header-home-btn { display: flex; width: 32px; height: 32px; font-size: 0.85rem; }
            .footer-container { flex-direction: column; gap: 1rem; text-align: center; }
            
            .nav-container { width: 100%; padding-bottom: 0; margin-bottom: 15px; gap: 15px; }
            .nav-group { gap: 8px; }
            .glass-nav { border-radius: 14px; width: auto; display: inline-flex; gap: 5px; padding: 5px; }
            .nav-btn { padding: 12px 24px; font-size: 0.85rem; justify-content: center; border-radius: 10px; }
            .env-nav .nav-btn { padding: 8px 15px; }
            .section-title { font-size: 1rem; }
            .chart-container { height: 280px; }
            .mobile-only-label { display: block; margin-bottom: 8px; }
        }

        /* Premium Loader */
        #loader {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: #ffffff;
            z-index: 100000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: opacity 0.5s ease;
        }
        .loader-logo { width: 120px; animation: logoPulse 1.5s ease-in-out infinite; }
        .loader-spinner {
            width: 50px; height: 50px; border: 3px solid rgba(255, 107, 0, 0.1);
            border-top: 3px solid #FF6B00; border-radius: 50%;
            animation: spin 1s linear infinite; margin-bottom: 24px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes logoPulse { 
            0% { opacity: 0.4; transform: scale(0.95); } 
            50% { opacity: 1; transform: scale(1.05); } 
            100% { opacity: 0.4; transform: scale(0.95); } 
        }
    </style>
</head>
<body>

    <div id="loader">
        <div class="loader-spinner"></div>
        <img src="https://hirepro.in/wp-content/uploads/2025/05/HirePro-logo.svg" alt="HirePro Logo" class="loader-logo">
    </div>

    <header>
        <div class="header-container">
            <div class="logo-section">
                <a href="dashboard.html" class="header-home-btn"><i class="fas fa-home"></i></a>

                <a href="dashboard.html" style="text-decoration: none; display: flex; align-items: center;">
                    <img src="https://hirepro.in/wp-content/uploads/2025/05/HirePro-logo.svg" alt="HirePro Logo" class="logo-img">
                </a>
            </div>
            <div class="title-section">
                <h1>Daily Performance</h1>
                <div class="subtitle">Multi-Environment API Audit</div>
            </div>
            <div class="audit-section">
                <div class="audit-label">LATEST AUDIT</div>
                <div class="audit-time">
                    <i class="fas fa-sync-alt" style="color: var(--success); font-size: 0.8rem;"></i>
                    __LATEST_DATE__
                </div>
            </div>
        </div>
    </header>

    <main>
        <div class="nav-container">
            <!-- Operation Selector -->
            <div class="glass-nav op-nav">
                <button class="nav-btn active" onclick="switchOp('GET', this)">
                    <i class="fas fa-chart-line"></i> GET APIs
                </button>
                <button class="nav-btn" onclick="switchOp('SET', this)">
                    <i class="fas fa-upload"></i> SET APIs
                </button>
            </div>

            <!-- Environment Selector -->
            <div class="nav-group">
                <div class="nav-label">ENVIRONMENT SELECTION</div>
                <div class="glass-nav env-nav">
                    __ENV_BTNS__
                </div>
            </div>
        </div>

        <div id="report-content">
            <!-- Dynamic Content -->
        </div>
    </main>

    <footer>
        <div class="footer-container">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; font-weight: 700;">Build ID:</span>
                <span class="commit-badge"><i class="fas fa-code-branch" style="margin-right:0.4rem; opacity:0.5;"></i>{commit_id}</span>
            </div>
            <div>&copy; 2026 HirePro. All rights reserved.</div>
        </div>
    </footer>

    <a href="dashboard.html" class="home-btn" title="Go to Dashboard">
        <i class="fas fa-home"></i>
    </a>


    <script>
        const rawData = __DATA_JSON__;
        let currentEnv = "__DEFAULT_ENV__";
        let currentOp = "GET";
        let charts = {};

        const colors = [
            '#FF6B00', '#2563eb', '#10b981', '#f59e0b', '#8b5cf6', 
            '#ec4899', '#06b6d4', '#64748b', '#1e293b', '#ef4444'
        ];

        function switchEnv(env, btn) {
            currentEnv = env;
            document.querySelectorAll('.env-nav .nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderContent();
        }

        function switchOp(op, btn) {
            currentOp = op;
            document.querySelectorAll('.op-nav .nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderContent();
        }

        function toggleChart(btn) {
            const card = btn.closest('.section-card');
            const section = card.querySelector('.chart-section');
            const isVisible = section.classList.toggle('active');
            btn.classList.toggle('active', isVisible);
            btn.querySelector('span').innerText = isVisible ? 'Hide Graph' : 'Show Graph';
        }

        function renderContent() {
            const container = document.getElementById('report-content');
            container.style.opacity = '0';
            container.style.transform = 'translateY(15px)';
            
            setTimeout(() => {
                const data = rawData[currentOp][currentEnv] || [];
                
                if (data.length === 0) {
                    container.innerHTML = `<div style="text-align:center; padding: 50px; color: #64748b;">No data available for ${currentEnv}</div>`;
                    container.style.opacity = '1';
                    container.style.transform = 'translateY(0)';
                    return;
                }

            // Prepare Chart Data
            const isWebView = window.innerWidth > 768;
            const labels = data.map(d => d.run_date).reverse();
            const apiNames = data[0].apis.map(a => a.name);
            const datasets = apiNames.map((name, idx) => {
                return {
                    label: name,
                    data: data.map(d => {
                        const api = d.apis.find(a => a.name === name);
                        return api ? api.current : null;
                    }).reverse(),
                    borderColor: colors[idx % colors.length],
                    backgroundColor: colors[idx % colors.length] + '20',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    hidden: idx >= 5 // Hide some by default to avoid clutter
                };
            });

            container.innerHTML = `
                <div class="section-card">
                    <div class="section-title">
                        <div>${currentOp} Performance Trend | <span class="text-orange">${currentEnv}</span></div>
                        <button class="toggle-graph-btn" onclick="toggleMainChart()">
                            <i class="${isWebView ? 'fas fa-eye-slash' : 'fas fa-eye'}" id="toggleIcon"></i> 
                            <span id="toggleText">${isWebView ? 'Hide Graph' : 'Show Graph'}</span>
                        </button>
                    </div>
                    <div class="chart-header">
                        <div id="controlsWrapper" style="display: ${isWebView ? 'flex' : 'none'}; flex-direction: column; align-items: center; width: 100%;">
                            <div class="api-visibility-label">API VISIBILITY CONTROL</div>
                            
                            <div class="legend-controls">
                                <button class="control-btn btn-select" onclick="toggleAllDatasets(true)">
                                    <i class="fas fa-check-double"></i> SELECT ALL
                                </button>
                                <button class="control-btn btn-clear" onclick="toggleAllDatasets(false)">
                                    <i class="fas fa-times-circle"></i> CLEAR ALL
                                </button>
                            </div>
                        </div>
                    </div>
                    <div id="chartWrapper" style="display: ${isWebView ? 'block' : 'none'};">
                        <div class="axis-label">
                            <i class="fas fa-stopwatch" style="color: var(--primary); font-size: 0.8rem;"></i>
                            RESPONSE TIME (S)
                        </div>
                        <div class="chart-container">
                            <canvas id="mainChart"></canvas>
                        </div>
                        <div id="chartLegend" class="custom-legend"></div>
                    </div>
                </div>

                <div class="section-card">
                    <div class="section-title">
                        <div>Detailed Audit | <span class="text-orange">${currentEnv}</span></div>
                    </div>
                    <div class="chart-header">
                        <div class="mobile-only-label" style="font-size: 0.8rem; font-weight: 700; color: #64748b;">API PERFORMANCE METRICS</div>
                    </div>
                    <div class="data-table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>API Endpoint</th>
                                    <th>Threshold (s)</th>
                                    <th>Response Time (s)</th>
                                    <th>Variation (%)</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data[0].apis.map(api => `
                                    <tr>
                                        <td><div class="api-name">${api.name}</div></td>
                                        <td><span style="font-weight:700;">${api.threshold.toFixed(2)}s</span></td>
                                        <td><span class="api-name" style="color:var(--primary)">${api.current.toFixed(2)}s</span></td>
                                        <td>
                                            <span class="variation ${api.variation > 0 ? 'var-up' : 'var-down'}">
                                                ${api.variation > 0 ? '+' : ''}${api.variation.toFixed(1)}%
                                                <i class="fas fa-caret-${api.variation > 0 ? 'up' : 'down'}"></i>
                                            </span>
                                        </td>
                                        <td>
                                            <span class="val-badge ${api.current <= api.threshold ? 'val-pass' : 'val-fail'}">
                                                ${api.current <= api.threshold ? 'PASSED' : 'BREACHED'}
                                            </span>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            initChart(labels, datasets);
            
            // Trigger Fade In with a slight delay to ensure DOM update
            setTimeout(() => {
                container.style.opacity = '1';
                container.style.transform = 'translateY(0)';
            }, 50);
        }, 150);
    }

        function initChart(labels, datasets) {
            const ctx = document.getElementById('mainChart').getContext('2d');
            
            if (charts.main) charts.main.destroy();

            charts.main = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            enabled: window.innerWidth > 768,
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            titleColor: '#1e293b',
                            bodyColor: '#1e293b',
                            borderColor: '#e2e8f0',
                            borderWidth: 1,
                            padding: 12,
                            boxPadding: 6,
                            usePointStyle: true,
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(3) + 's';
                                }
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            grid: { borderDash: [5, 5], color: '#f1f5f9' },
                            ticks: { font: { weight: '600' }, callback: value => value + 's' }
                        },
                        x: { grid: { display: false }, ticks: { font: { weight: '600' } } }
                    }
                }
            });

            // Custom Legend
            const legendContainer = document.getElementById('chartLegend');
            legendContainer.innerHTML = datasets.map((ds, idx) => `
                <div class="legend-item ${ds.hidden ? 'hidden' : ''}" onclick="toggleDataset(${idx}, this)">
                    <div class="legend-dot" style="border-color:${ds.borderColor}"></div>
                    <span>${ds.label}</span>
                </div>
            `).join('');
        }

        function toggleDataset(idx, el) {
            const meta = charts.main.getDatasetMeta(idx);
            meta.hidden = meta.hidden === null ? !charts.main.data.datasets[idx].hidden : null;
            el.classList.toggle('hidden');
            charts.main.update();
        }

        function toggleAllDatasets(show) {
            if (!charts.main) return;
            charts.main.data.datasets.forEach((ds, idx) => {
                const meta = charts.main.getDatasetMeta(idx);
                meta.hidden = !show;
            });
            charts.main.update();
            
            // Update legend UI
            document.querySelectorAll('.legend-item').forEach(el => {
                if (show) el.classList.remove('hidden');
                else el.classList.add('hidden');
            });
        }

        function toggleMainChart() {
            const wrapper = document.getElementById('chartWrapper');
            const controls = document.getElementById('controlsWrapper');
            const icon = document.getElementById('toggleIcon');
            const text = document.getElementById('toggleText');
            
            if (wrapper.style.display === 'none') {
                wrapper.style.display = 'block';
                controls.style.display = 'flex';
                icon.className = 'fas fa-eye-slash';
                text.innerText = 'Hide Graph';
                if (charts.main) charts.main.resize();
            } else {
                wrapper.style.display = 'none';
                controls.style.display = 'none';
                icon.className = 'fas fa-eye';
                text.innerText = 'Show Graph';
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            renderContent();
        });
        // Loader Cleanup
        window.addEventListener('load', () => {
            const loader = document.getElementById('loader');
            setTimeout(() => {
                if (loader) {
                    loader.style.opacity = '0';
                    setTimeout(() => loader.style.display = 'none', 500);
                }
            }, 800);
        });
    </script>
</body>
</html>
"""

# Generate environment buttons
env_btns = ""
default_env = final_data["environments"][0] if final_data["environments"] else ""
for env in final_data["environments"]:
    active_class = "active" if env == default_env else ""
    env_btns += f'<button class="nav-btn {active_class}" onclick="switchEnv(\'{env}\', this)">{env}</button>\n'

full_html = html_template.replace("__DATA_JSON__", json.dumps(final_data))
full_html = full_html.replace("__LATEST_DATE__", latest_date)
full_html = full_html.replace("__ENV_BTNS__", env_btns)
full_html = full_html.replace("__DEFAULT_ENV__", default_env)
commit_id = get_git_commit()
full_html = full_html.replace("{commit_id}", commit_id)

with open(os.path.join(configfile.AUTOMATION_PATH, "performance_daily.html"), "w") as f:
    f.write(full_html)

print("Daily Performance Report generated successfully!")
