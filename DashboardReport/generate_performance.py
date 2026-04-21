import pandas as pd
import json
import os
import subprocess
from datetime import datetime
from Config import configfile

def process_report(file_path):
    if not os.path.exists(file_path):
        return []
    
    df = pd.read_excel(file_path)
    # Take last 5 results based on index (assuming they are chronological) or sorted by Sprint
    # Sort by 'Sprint' might be tricky if it's string 'Sprint_196', 'Sprint_200'
    # Let's try to extract numeric part for sorting if needed, but tail(5) usually works for these reports.
    df_last_5 = df.tail(5).copy()
    
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
        for i in range(5, len(cols) - 2, 3):
            threshold_col = cols[i]
            current_col = cols[i+1]
            variation_col = cols[i+2]
            
            # Skip if any of these columns are beyond index or headers are missing
            if any(pd.isnull(c) for c in [threshold_col, current_col, variation_col]):
                continue

            # API name from current column header
            api_name = str(current_col).replace(" Previous sprint(%)", "").replace(" Threshold", "").strip()
            
            # Map values, handling potential non-numeric data
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
    
    report_data.reverse() # Make latest sprint first
    return report_data

get_report = process_report(configfile.GET_PERFORMANCE_REPORT)
set_report = process_report(configfile.SET_PERFORMANCE_REPORT)

final_data = {
    "get_report": get_report,
    "set_report": set_report
}

# Write data to a JSON for the HTML to consume or just generate the HTML directly
# I will generate the HTML directly with the data embedded.

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/png" href="https://lh3.googleusercontent.com/proxy/98it6d0vGqaPttxE8ImrHhVvaz5XpPeZ7qiXHcnm9PiPrwTBGvZcWp2vdQVdgZt5b7Vfu7kXnkh6mrKs_q_JIE5GGlw8uRAOeSvJOEtgNXWrXgOoGjGFCnKCA1gITLLZKNxv1mV6szDHEnNLK7RbJnfk-eFMZPlGXRpU2iKeBGr2Gm3-i_Lnv-IVisLlJwRR55nNMx9HndfYnmLOlraDHGgp9Rc7V4pNO1N8S1ZugYR5SUVMi8K_WGFwvYWsEh2cEnW6x-Zw-ncSM27yX509d6pmuUvfohenPAxHMNORCeWO">
    <title>Performance Analytics</title>
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

        body {
            background-color: #f8fafc;
            background-image: 
                radial-gradient(at 0% 0%, rgba(255, 107, 0, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.05) 0px, transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
            padding-bottom: 40px;
            overflow-x: hidden;
            width: 100vw;
        }

        /* Premium Loader */
        #loader {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: white; z-index: 10000; display: flex; flex-direction: column;
            align-items: center; justify-content: center; transition: opacity 0.5s ease;
        }
        .loader-spinner {
            width: 60px; height: 60px; border: 4px solid #f1f5f9;
            border-top: 4px solid var(--primary); border-radius: 50%;
            animation: spin 1s linear infinite; margin-bottom: 20px;
        }
        .loader-logo { width: 120px; opacity: 0; animation: logoPulse 1.5s ease-in-out infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes logoPulse { 0% { opacity: 0.3; transform: scale(0.95); } 50% { opacity: 0.8; transform: scale(1); } 100% { opacity: 0.3; transform: scale(0.95); } }

        header {
            padding: 15px 0;
            margin: 0 auto 1.5rem auto;
            max-width: 1400px;
            z-index: 1000;
            position: relative;
            border-bottom: 1px solid #D9D7D7;
        }

        .header-container {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            padding: 5px 20px;
        }

        .nav-section { display: flex; align-items: center; gap: 1rem; }
        .title-section { text-align: center; }
        .audit-section { text-align: right; }

        .home-link {
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: #FFFFFF;
            color: #6366F1;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.2s;
        }

        .home-link:hover {
            background: #E5E7EB;
            transform: scale(1.05);
        }

        .logo-img {
            height: 32px;
            width: auto;
        }

        .title-section h1 {
            font-size: 1.6rem;
            font-weight: 800;
            color: #000000;
            line-height: 1.2;
        }

        .subtitle {
            color: #64748b;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 5px;
        }

        .audit-label {
            font-size: 0.75rem;
            color: #64748b;
            font-weight: 700;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .audit-time {
            font-weight: 700;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 8px;
            justify-content: flex-end;
            font-size: 1.1rem;
        }

        .audit-time i {
            color: var(--success);
            font-size: 1rem;
        }

        .report-section {
            display: none;
        }

        .report-section.active {
            display: block;
            animation: fadeIn 0.4s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        main {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 5%;
        }

        /* Liquid Glass Navigation */
        .main-nav { 
            display: flex; position: relative; justify-content: center; gap: 0; 
            margin-bottom: 2.5rem; background: rgba(241, 245, 249, 0.75); 
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            padding: 0.45rem; border-radius: 99px; width: fit-content; margin: 0 auto 2.5rem auto;
            border: 1px solid rgba(255,255,255,0.6); box-shadow: 0 8px 32px rgba(0,0,0,0.06);
            overflow: hidden;
        }
        .nav-btn { 
            position: relative; z-index: 2; padding: 0.75rem 2.8rem; border-radius: 99px; 
            border: none; background: transparent; color: var(--text-dim); 
            font-weight: 700; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
            display: flex; align-items: center; gap: 0.75rem; font-size: 0.9rem; 
            text-transform: uppercase; letter-spacing: 0.05em;
            user-select: none; -webkit-user-select: none; white-space: nowrap;
        }
        .nav-btn:hover { color: var(--text-main); }
        .nav-btn.active { color: var(--primary); }
        .nav-indicator {
            position: absolute; height: calc(100% - 0.9rem); top: 0.45rem; left: 0.45rem;
            background: white; border-radius: 99px; z-index: 1;
            transition: all 0.45s cubic-bezier(0.23, 1, 0.32, 1.2);
            box-shadow: 0 4px 15px rgba(255, 107, 0, 0.15);
            width: 0; pointer-events: none;
        }

        main { max-width: 1400px; margin: 0 auto; padding: 0 20px; }

        .chart-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 32px;
            padding: 2rem;
            margin-bottom: 4rem;
            box-shadow: 0 15px 45px rgba(0,0,0,0.03);
            position: relative;
            overflow: hidden;
            border-top: 5px solid var(--primary);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        /* Glass Legend System */
        .legend-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px; padding: 0 0.5rem;
        }
        .legend-title { font-size: 0.75rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; }
        .legend-controls { display: flex; gap: 8px; }
        
        .legend-btn {
            padding: 0.5rem 1.25rem; border-radius: 12px; border: 1px solid rgba(255,107,0,0.2);
            background: rgba(255,107,0,0.05); color: var(--primary); font-size: 0.7rem; font-weight: 800;
            cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex; align-items: center; gap: 8px; text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        .legend-btn i { font-size: 0.8rem; }
        .legend-btn:hover { 
            background: var(--primary); color: white; 
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255,107,0,0.25);
        }
        .legend-btn:active { transform: translateY(0); }
        .legend-btn.unselect { background: #f1f5f9; color: #64748b; border-color: #e2e8f0; }
        .legend-btn.unselect:hover { background: #e2e8f0; color: #1e293b; }

        .custom-legend {
            display: flex; flex-wrap: wrap; gap: 10px; padding: 1.5rem;
            background: rgba(248, 250, 252, 0.5); border-radius: 24px;
            margin-top: 20px; border: 1px solid rgba(255,107,0,0.05);
            backdrop-filter: blur(8px);
        }
        .legend-item {
            display: flex; align-items: center; gap: 8px;
            padding: 6px 14px; border-radius: 99px; cursor: pointer;
            background: white; border: 1px solid var(--border);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none; -webkit-tap-highlight-color: transparent;
        }
        .legend-item:hover { transform: translateY(-2px); border-color: var(--primary); box-shadow: 0 4px 12px rgba(255,107,0,0.1); }
        .legend-item.hidden { opacity: 0.4; background: #f8fafc; filter: grayscale(1); }
        .legend-item.hidden i { border-color: #94a3b8 !important; background: transparent !important; }
        
        .legend-dot { width: 10px; height: 10px; border-radius: 50%; border: 2.5px solid transparent; }
        .legend-text { font-size: 0.75rem; font-weight: 600; color: #334155; }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.3rem;
            font-weight: 800;
            color: #494444;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
            padding-left: 5px;
            border-left: 4px solid var(--primary);
        }

        .section-title i {
            color: var(--primary);
            font-size: 1.1rem;
        }
        
        .chart-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: var(--primary-gradient); opacity: 0.8;
        }

        .chart-container { height: 450px; }

        /* Collapse Section Branding */
        details { 
            background: white; 
            border: 1px solid var(--border); 
            border-radius: 24px; 
            margin-bottom: 1.5rem; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.02); 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
            overflow: hidden;
        }
        details:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 12px 25px rgba(0,0,0,0.05);
            border-color: rgba(255, 107, 0, 0.2);
        }
        
        summary { 
            padding: 1.75rem 2rem; 
            cursor: pointer; 
            background: white; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            list-style: none; 
            transition: background 0.3s;
            outline: none;
        }
        summary::-webkit-details-marker { display: none; }
        
        .content-wrapper { 
            display: grid; 
            grid-template-rows: 0fr; 
            transition: grid-template-rows 0.5s cubic-bezier(0.4, 0, 0.2, 1); 
            background: #fff;
        }
        details[open] .content-wrapper { grid-template-rows: 1fr; }
        .content-inner { overflow: hidden; }

        summary::after { 
            content: '\f078'; 
            font-family: "Font Awesome 6 Free"; 
            font-weight: 900; 
            transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1); 
            color: var(--text-dim);
            background: #f8fafc;
            width: 40px; height: 40px;
            display: flex; align-items: center; justify-content: center;
            border-radius: 50%;
            font-size: 0.85rem;
        }
        details[open] summary::after { transform: rotate(180deg); background: rgba(255, 107, 0, 0.1); color: var(--primary); }
        details[open] summary { border-bottom: 1px solid var(--border); }
        
        .sprint-label { display: flex; align-items: center; gap: 1.25rem; }
        .sprint-id { font-size: 1.1rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em; }
        
        .sprint-meta { display: flex; gap: 1.5rem; }
        .meta-item { display: flex; align-items: center; gap: 8px; font-size: 0.90rem; font-weight: 800; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
        .meta-item i { color: var(--primary); }

        /* Beautiful Rows for Table */
        .table-wrapper { padding: 0.5rem; }
        table { width: 100%; border-collapse: separate; border-spacing: 0 12px; }
        th { padding: 1.25rem; font-size: 0.7rem; font-weight: 900; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.1em; border: none; text-align: left; }
        
        .api-row td { 
            background: #ffffff; 
            padding: 1.5rem 1.25rem; 
            border-top: 1px solid #f8fafc;
            border-bottom: 1px solid #f8fafc;
            transition: all 0.3s;
        }
        .api-row td:first-child { border-left: 1px solid #f8fafc; border-radius: 20px 0 0 20px; }
        .api-row td:last-child { border-right: 1px solid #f8fafc; border-radius: 0 20px 20px 0; }
        
        .api-row:hover td { 
            background: #fffcf9; 
            border-color: rgba(255, 107, 0, 0.1); 
            transform: scale(1.005);
        }

        .api-info { display: flex; align-items: center; gap: 1rem; }
        .api-icon { 
            width: 44px; height: 44px; border-radius: 14px; 
            background: #f8fafc; display: flex; align-items: center; justify-content: center;
            color: var(--primary); font-size: 1.1rem;
            transition: all 0.3s;
        }
        .api-row:hover .api-icon { background: var(--primary); color: white; transform: rotate(10deg); }
        
        .api-details h4 { font-size: 1rem; font-weight: 800; color: var(--text-main); margin-bottom: 2px; }
        .api-details p { font-size: 0.7rem; color: var(--text-dim); font-weight: 700; text-transform: uppercase; }

        .stat-value { font-size: 1.1rem; font-weight: 900; color: var(--text-main); }
        .stat-label { font-size: 0.65rem; color: var(--text-dim); font-weight: 700; text-transform: uppercase; margin-top: 4px; }
        
        .variation-badge {
            display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 12px;
            font-size: 0.85rem; font-weight: 900;
        }
        .var-up { background: #fee2e2; color: #dc2626; }
        .var-down { background: #d1fae5; color: #059669; }

        .status-pill {
            display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 15px;
            font-size: 0.75rem; font-weight: 900; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        .status-pass { background: var(--success); }
        .status-fail { background: var(--danger); box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2); }

        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            header { margin: 15px 3% 20px 3%; }
            .header-container { grid-template-columns: 1fr; gap: 1rem; text-align: center; }
            .nav-section { justify-content: center; }
            .audit-section { text-align: center; }
            .audit-time { justify-content: center; }

            .main-nav { 
                width: 94%; padding: 0.35rem; margin-bottom: 2rem; 
                flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch;
            }
            .nav-btn { padding: 0.6rem 1.25rem; font-size: 0.75rem; flex-shrink: 0; }

            .chart-card { padding: 1rem; border-radius: 20px; margin-bottom: 1.5rem; }
            .chart-container { height: 260px !important; }

            .section-title { font-size: 1rem; padding-left: 0; border-left: none; border-bottom: 2px solid var(--primary); width: fit-content; margin-bottom: 1.25rem; }

            /* Refined Table to Card Transformation */
            .table-wrapper { padding: 0; overflow-x: hidden; }
            table, thead, tbody, th, td, tr { display: block; width: 100%; }
            thead { display: none; }
            
            .api-row { 
                margin-bottom: 1.25rem; border: 1px solid var(--border); 
                border-radius: 16px !important; background: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.03); overflow: hidden;
            }
            .api-row td { 
                border: none !important; padding: 0.85rem 1rem !important; 
                display: flex; justify-content: space-between; align-items: center;
                background: transparent !important; min-height: 50px;
            }
            .api-row td:not(:last-child) { border-bottom: 1px dashed #f1f5f9 !important; }
            
            .api-row td:first-child { 
                background: #f8fafc !important; border-radius: 0 !important;
                padding: 1.15rem 1rem !important; flex-direction: column; align-items: flex-start; gap: 4px;
            }
            .api-row td:last-child { border-radius: 0 !important; padding: 1rem !important; }
            
            .api-info { width: 100%; }
            .api-details h4 { font-size: 0.85rem; word-break: break-all; width: 100%; white-space: normal; }
            .api-details p { font-size: 0.6rem; opacity: 0.8; }
            
            .stat-value { font-size: 0.9rem; }
            .stat-label { font-size: 0.55rem; }
            
            .variation-badge { padding: 4px 10px; font-size: 0.75rem; }
            
            summary { padding: 1.15rem 1rem; }
            .sprint-id { font-size: 1rem; }
            .sprint-label { gap: 0.75rem; }
            .sprint-meta { flex-direction: column; gap: 2px; }
            .meta-item { font-size: 0.6rem; }
            
            .floating-home, .api-icon { display: none !important; }
        }

        /* Column Widths */
        th:nth-child(1), td:nth-child(1) { width: 40%; }
        th:nth-child(2), td:nth-child(2) { width: 12%; }
        th:nth-child(3), td:nth-child(3) { width: 12%; }
        th:nth-child(4), td:nth-child(4) { width: 15%; }
        th:nth-child(5), td:nth-child(5) { width: 21%; text-align: right; }

        .api-name { font-weight: 700; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .val-current { font-weight: 800; color: var(--primary); }
        
        .chip { font-size: 0.75rem; padding: 4px 12px; border-radius: 6px; font-weight: 800; display: inline-flex; align-items: center; gap: 6px; }
        .chip-success { background: #d1fae5; color: #065f46; }
        .chip-danger { background: #fee2e2; color: #991b1b; }
        .chip-neutral { background: #f1f5f9; color: #475569; }

        .floating-home {
            position: fixed; bottom: 2rem; right: 2rem; width: 56px; height: 56px; 
            background: var(--primary); color: white; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 8px 25px rgba(255, 107, 0, 0.35); cursor: pointer;
            z-index: 9999; border: none; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            text-decoration: none; font-size: 1.2rem;
        }
        .floating-home:hover { transform: scale(1.1) translateY(-5px); box-shadow: 0 12px 30px rgba(255, 107, 0, 0.45); }

        footer { 
            margin-top: 8rem; padding: 2rem 0; border-top: 1px solid #D9D7D7; 
            display: flex; justify-content: space-between; align-items: center; 
            color: #64748b; font-size: 0.85rem; font-weight: 500; 
        }
        .commit-badge { 
            background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 6px; 
            font-family: monospace; font-weight: 700; color: #000; 
            border: 1px solid var(--border); font-size: 0.75rem; 
        }
        .floating-home {
            position: fixed; bottom: 30px; right: 30px; z-index: 9999;
            width: 56px; height: 56px; border-radius: 20px;
            background: rgba(255,107,0,0.9); backdrop-filter: blur(8px);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 1.4rem; text-decoration: none;
            box-shadow: 0 10px 30px rgba(255,107,0,0.3);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .floating-home:hover { transform: scale(1.1) translateY(-5px); box-shadow: 0 15px 40px rgba(255,107,0,0.45); background: #ff6b00; }
        .floating-home i { transition: transform 0.3s ease; }
        .floating-home:hover i { transform: rotate(-10deg); }

        @media (max-width: 768px) {
            header { padding: 25px 0; margin-bottom: 10px; }
            .header-container { grid-template-columns: 1fr; gap: 15px; text-align: center; }
            .logo-img { height: 35px; }
            .nav-section { justify-content: center; }
            .audit-section { justify-content: center; }
            .audit-time { justify-content: center; margin-top: 2px; font-size: 0.7rem; }
            
            .main-nav { scale: 1; margin: 0 auto 2rem auto; width: 96%; padding: 0.3rem; }
            .nav-btn { padding: 0.6rem 0.4rem; font-size: 0.65rem; flex: 1; min-width: 0; }
            .nav-indicator { height: calc(100% - 0.6rem); top: 0.3rem; left: 0.3rem; }
            
            .chart-card { padding: 1rem; border-radius: 16px; margin-bottom: 1.5rem; border-width: 1px; }
            .chart-container { height: 260px !important; }
            .section-title { font-size: 1rem; justify-content: center; margin-bottom: 1.25rem; text-align: center; }

            summary { padding: 1.25rem; align-items: center; border-radius: 16px !important; }
            .sprint-label { align-items: flex-start; width: 100%; gap: 10px; }
            .sprint-meta { flex-direction: column; gap: 4px; }
            .sprint-id { font-size: 0.95rem; }
            .meta-item { font-size: 0.75rem; }
            summary::after { width: 32px; height: 32px; top: 1.25rem; right: 1.25rem; }

            .api-row td { padding: 0.8rem 1rem !important; }
            .stat-value { font-size: 0.8rem; }
            
            /* Compact Mobile Adjustments */
            .custom-legend { padding: 1rem; gap: 8px; border-radius: 20px; }
            .legend-item { padding: 4px 10px; border-radius: 12px; }
            .legend-dot { width: 8px; height: 8px; }
            .legend-text { font-size: 0.65rem; }
            
            .legend-header { flex-direction: column; align-items: flex-start; gap: 12px; }
            .legend-controls { width: 100%; justify-content: space-between; }
            .legend-btn { flex: 1; justify-content: center; padding: 0.6rem; font-size: 0.6rem; }
            .floating-home { width: 48px; height: 48px; bottom: 20px; right: 20px; font-size: 1.2rem; }

            footer { 
                flex-direction: column; gap: 1.5rem; margin-top: 4rem; 
                text-align: center; padding: 2rem 1rem; 
            }
        }

        @media (max-width: 480px) {
            .chart-container { height: 240px !important; }
            .title-section h1 { font-size: 1.2rem; }
            .subtitle { font-size: 0.75rem; }
            .main-nav { margin: 0 auto 1.5rem auto; }
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
            <div class="nav-section">
                <img src="https://hirepro.in/wp-content/uploads/2025/05/HirePro-logo.svg" alt="HirePro Logo" class="logo-img">
            </div>
            <div class="title-section">
                <h1>Performance Analytics</h1>
                <div class="subtitle">API Response Time Trends & Historical Audit</div>
            </div>
            <div class="audit-section" style="text-align: right;">
                <div style="font-size: 0.8rem; color: #64748b; font-weight: 600; margin-bottom: 0.25rem;">LATEST AUDIT</div>
                <div style="font-weight: 800; font-size: 1rem;"><i class="fas fa-sync-alt" style="color:var(--success); margin-right: 0.5rem;"></i> __LATEST_DATE__</div>
            </div>
        </div>
    </header>

    <main>
        <a href="dashboard.html" class="floating-home" title="Return to Dashboard">
        <i class="fas fa-home"></i>
    </a>

    <div class="main-nav">
            <div class="nav-indicator"></div>
            <button class="nav-btn active" onclick="showReport('get-report', this)">
                <i class="fas fa-chart-line"></i> GET Operations
            </button>
            <button class="nav-btn" onclick="showReport('set-report', this)">
                <i class="fas fa-upload"></i> SET Operations
            </button>
        </div>

        <section id="get-report" class="report-section active">
            <div class="section-title"><i class="fas fa-wave-square"></i> GET APIs Performance Trend</div>
            
            <div class="chart-card">
                <div class="legend-header">
                    <div class="legend-title">API Visibility Control</div>
                    <div class="legend-controls">
                        <button class="legend-btn" onclick="toggleAll('getChart', true)">
                            <i class="fas fa-check-double"></i> Select All
                        </button>
                        <button class="legend-btn unselect" onclick="toggleAll('getChart', false)">
                            <i class="fas fa-times-circle"></i> Clear All
                        </button>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="getChart"></canvas>
                </div>
                <div id="getChart-legend" class="custom-legend"></div>
            </div>

            <div class="section-title"><i class="fas fa-history"></i> Historical Data Audit</div>
            <div id="get-history-list"></div>
        </section>

        <section id="set-report" class="report-section">
            <div class="section-title"><i class="fas fa-wave-square"></i> SET APIs Performance Trend</div>
            
            <div class="chart-card">
                <div class="legend-header">
                    <div class="legend-title">API Visibility Control</div>
                    <div class="legend-controls">
                        <button class="legend-btn" onclick="toggleAll('setChart', true)">
                            <i class="fas fa-check-double"></i> Select All
                        </button>
                        <button class="legend-btn unselect" onclick="toggleAll('setChart', false)">
                            <i class="fas fa-times-circle"></i> Clear All
                        </button>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="setChart"></canvas>
                </div>
                <div id="setChart-legend" class="custom-legend"></div>
            </div>

            <div class="section-title"><i class="fas fa-history"></i> Historical Data Audit</div>
            <div id="set-history-list"></div>
        </section>
    </main>

    <div style="max-width: 1400px; margin: 0 auto; padding: 0 20px;">
        <footer>
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; font-weight: 700;">Build ID:</span>
                <span class="commit-badge"><i class="fas fa-code-branch" style="margin-right:0.4rem; opacity:0.5;"></i>__BUILD_ID__</span>
            </div>
            <div>&copy; 2026 HirePro . All rights reserved.</div>
        </footer>
    </div>

    <script>
        const data = __DATA_JSON__;

        function updateIndicator(btn) {
            const indicator = document.querySelector('.nav-indicator');
            const activeBtn = btn || document.querySelector('.nav-btn.active');
            if (activeBtn && indicator) {
                indicator.style.width = activeBtn.offsetWidth + 'px';
                indicator.style.left = activeBtn.offsetLeft + 'px';
            }
        }

        function showReport(id, btn) {
            document.querySelectorAll('.report-section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            btn.classList.add('active');
            updateIndicator(btn);
        }

        function populateGroups(listId, reportData) {
            const list = document.getElementById(listId);
            reportData.forEach((sprint, idx) => {
                const details = document.createElement('details');
                
                details.innerHTML = `
                    <summary>
                        <div class="sprint-label">
                            <span class="sprint-id">${sprint.sprint}</span>
                            <div class="sprint-meta">
                                <div class="meta-item"><i class="fas fa-calendar-alt"></i> ${sprint.run_date}</div>
                                <div class="meta-item"><i class="fas fa-mouse-pointer"></i> ${sprint.hits} Hits</div>
                            </div>
                        </div>
                        <div class="meta-item" style="color: var(--primary);"><i class="fas fa-microchip"></i> ${sprint.apis.length} Endpoints</div>
                    </summary>
                    <div class="content-wrapper">
                        <div class="content-inner">
                            <div class="table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Endpoint Identity</th>
                                            <th>Limit</th>
                                            <th>Actual Time</th>
                                            <th style="text-align: right">Drift Analysis</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${sprint.apis.map(api => {
                                            const diff = api.threshold - api.current;
                                            const varClass = api.variation > 0 ? 'var-up' : 'var-down';
                                            const varIcon = api.variation > 0 ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down';
                                            
                                            return `
                                                <tr class="api-row">
                                                    <td>
                                                        <div class="api-info">
                                                            <div class="api-icon"><i class="fas fa-bolt"></i></div>
                                                            <div class="api-details">
                                                                <h4>${api.name}</h4>
                                                                <p>Operation Endpoint</p>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <div class="stat-value">${api.threshold}s</div>
                                                        <div class="stat-label">Baseline</div>
                                                    </td>
                                                    <td>
                                                        <div class="stat-value" style="color: var(--primary)">${api.current}s</div>
                                                        <div class="stat-label">Execution</div>
                                                    </td>
                                                    <td style="text-align: right">
                                                        <div class="variation-badge ${varClass}">
                                                            <i class="fas ${varIcon}"></i>
                                                            ${api.variation > 0 ? '+' : ''}${api.variation}%
                                                        </div>
                                                    </td>
                                                </tr>
                                            `;
                                        }).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                `;
                list.appendChild(details);
            });
        }

        const charts = {};

        function toggleAll(chartId, show) {
            const chart = charts[chartId];
            if (!chart) return;
            chart.data.datasets.forEach((ds, i) => {
                chart.setDatasetVisibility(i, show);
            });
            chart.update();
            renderLegend(chartId, chart);
        }

        function renderLegend(chartId, chart) {
            const legendContainer = document.getElementById(chartId + '-legend');
            if (!legendContainer) return;
            legendContainer.innerHTML = '';
            
            chart.data.datasets.forEach((dataset, i) => {
                const isVisible = chart.isDatasetVisible(i);
                const item = document.createElement('div');
                item.classList.add('legend-item');
                if (!isVisible) item.classList.add('hidden');
                
                item.innerHTML = `
                    <div class="legend-dot" style="border-color: ${dataset.borderColor}; background: ${dataset.backgroundColor}"></div>
                    <span class="legend-text">${dataset.label}</span>
                `;
                
                item.onclick = () => {
                    chart.setDatasetVisibility(i, !chart.isDatasetVisible(i));
                    chart.update();
                    renderLegend(chartId, chart);
                };
                
                legendContainer.appendChild(item);
            });
        }

        function initCharts() {
            const config = (type) => ({
                type: 'line',
                data: {
                    labels: data[`${type}_report`].map(s => s.sprint).reverse(),
                    datasets: data[`${type}_report`][0].apis.map((api, idx) => ({
                        label: api.name,
                        data: data[`${type}_report`].map(s => {
                            const match = s.apis.find(a => a.name === api.name);
                            return match ? match.current : 0;
                        }).reverse(),
                        borderColor: `hsl(${(idx * 137) % 360}, 75%, 60%)`,
                        backgroundColor: `hsl(${(idx * 137) % 360}, 75%, 60%, 0.1)`,
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: 'white',
                        fill: true
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { 
                        legend: { display: false },
                        tooltip: { mode: 'index', intersect: false }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true, 
                            grid: { color: 'rgba(0,0,0,0.04)' }, 
                            ticks: { 
                                color: '#64748b', 
                                font: { size: 10, weight: 600 },
                                callback: v => v + 's'
                            } 
                        },
                        x: { grid: { display: false }, ticks: { color: '#64748b', font: { size: 10, weight: 600 } } }
                    }
                }
            });

            charts['getChart'] = new Chart(document.getElementById('getChart'), config('get'));
            charts['setChart'] = new Chart(document.getElementById('setChart'), config('set'));
            
            renderLegend('getChart', charts['getChart']);
            renderLegend('setChart', charts['setChart']);
        }

        window.onload = () => {
            populateGroups('get-history-list', data.get_report);
            populateGroups('set-history-list', data.set_report);
            initCharts();
            updateIndicator();
            const loader = document.getElementById('loader');
            setTimeout(() => {
                loader.style.opacity = '0';
                setTimeout(() => { 
                    loader.style.display = 'none'; 
                }, 500);
            }, 800);
        };

        window.onresize = () => updateIndicator();
    </script>
</body>
</html>
"""

# Get Build ID
try:
    build_id = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
except:
    build_id = "LOCAL_BUILD"

latest_display = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

full_html = html_template.replace("__DATA_JSON__", json.dumps(final_data))
full_html = full_html.replace("__BUILD_ID__", build_id)
full_html = full_html.replace("__LATEST_DATE__", latest_display)

output_file = configfile.PERFORMANCE_HTML
with open(output_file, "w") as f:
    f.write(full_html)

print("Performance HTML generated successfully.")
