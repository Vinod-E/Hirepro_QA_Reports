import pandas as pd
import json
import os
import subprocess
from datetime import datetime
from Config import configfile

def process_all_sheets(file_path):
    if not os.path.exists(file_path):
        return {}
    
    xl = pd.ExcelFile(file_path)
    sheets_data = {}
    
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name)
        # Take last 5 results
        df_last_5 = df.tail(5).copy()
        
        report_data = []
        
        for _, row in df_last_5.iterrows():
            row_entry = {
                "sprint": str(row.get("Sprint", "")),
                "run_date": str(row.get("Run Date", "")),
                "hits": int(row.get("Number of hits", 0)) if pd.notnull(row.get("Number of hits")) else 0,
                "apis": []
            }
            
            cols = [c for c in df.columns if not str(c).startswith("Unnamed")]
            
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

get_data = process_all_sheets(configfile.GET_PERFORMANCE_REPORT)
set_data = process_all_sheets(configfile.SET_PERFORMANCE_REPORT)

# Get list of all unique environments across both files
raw_envs = list(set(list(get_data.keys()) + list(set_data.keys())))

def custom_env_sort(env):
    # Sort by group first (AMSIN, BETA, AMS), then ensure EU is second in each pair
    group_order = {"AMSIN": 0, "BETA": 1, "AMS": 2}
    if "_" in env:
        base = env.rsplit("_", 1)[0]
        suffix = env.rsplit("_", 1)[1]
    else:
        base = env
        suffix = ""
    
    g_weight = group_order.get(base, 99)
    is_eu = 1 if suffix == "EU" else 0
    return (g_weight, base, is_eu, env)

environments = sorted(raw_envs, key=custom_env_sort)

final_data = {
    "environments": environments,
    "reports": {
        env: {
            "get": get_data.get(env, []),
            "set": set_data.get(env, [])
        } for env in environments
    }
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
            --primary: #2563eb;
            --primary-gradient: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
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
            background: #ffffff;
            background-image: 
                radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(99, 102, 241, 0.05) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(37, 99, 235, 0.05) 0px, transparent 50%),
                radial-gradient(at 0% 100%, rgba(99, 102, 241, 0.05) 0px, transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
            padding-bottom: 40px;
            overflow-y: auto;
            width: 100vw;
            font-family: 'Outfit', sans-serif;
            position: relative;
        }

        /* Liquid Glass Background */
        .bg-blobs {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: -1; overflow: hidden; pointer-events: none;
        }
        .blob {
            position: absolute; width: 600px; height: 600px;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.07) 0%, transparent 70%);
            border-radius: 50%; filter: blur(80px);
            animation: move 25s infinite alternate;
        }
        .blob-1 { top: -200px; left: -100px; animation-duration: 30s; }
        .blob-2 { bottom: -200px; right: -100px; background: radial-gradient(circle, rgba(99, 102, 241, 0.07) 0%, transparent 70%); animation-duration: 35s; }
        @keyframes move {
            from { transform: translate(0, 0) rotate(0deg) scale(1); }
            to { transform: translate(150px, 100px) rotate(30deg) scale(1.2); }
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

        .header-home-btn { display: none; text-decoration: none; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: rgba(37, 99, 235, 0.1); color: var(--primary); transition: all 0.2s; margin: 0 auto 0.25rem auto; border: 1px solid rgba(37, 99, 235, 0.2); }
        .header-home-btn:active { background: rgba(37, 99, 235, 0.2); transform: scale(0.95); }

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

        .nav-group {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
            margin-bottom: 2rem;
        }

        .nav-label {
            font-size: 0.7rem;
            font-weight: 800;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 12px;
            text-align: center;
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
            margin-bottom: 1.5rem; background: rgba(241, 245, 249, 0.7); 
            backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            padding: 0.5rem; border-radius: 99px; width: fit-content; margin: 0 auto 2rem auto;
            border: 1px solid rgba(255,255,255,0.8); box-shadow: 0 12px 40px rgba(0,0,0,0.06);
            overflow: hidden;
        }
        
        .env-nav {
            display: flex; position: relative; justify-content: center; gap: 0; 
            margin-bottom: 2.5rem; background: rgba(241, 245, 249, 0.4); 
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            padding: 0.4rem; border-radius: 99px; width: fit-content; margin: 0 auto;
            border: 1px solid rgba(255,255,255,0.6); box-shadow: 0 8px 30px rgba(0,0,0,0.04);
            overflow: hidden;
        }

        .nav-btn { 
            position: relative; z-index: 2; padding: 0.8rem 2.5rem; border-radius: 99px; 
            border: none; background: transparent; color: #64748b; 
            font-weight: 800; cursor: pointer; transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); 
            display: flex; align-items: center; gap: 0.85rem; font-size: 0.85rem; 
            text-transform: uppercase; letter-spacing: 0.08em;
            user-select: none; -webkit-user-select: none; white-space: nowrap;
        }
        .nav-btn:active { transform: scale(0.96); transition: 0.1s; }
        
        .env-btn {
            position: relative; z-index: 2;
            padding: 10px 24px; font-size: 0.75rem; 
            background: transparent;
            color: #64748b; border-radius: 99px; 
            border: none;
            font-weight: 700; cursor: pointer; 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        .env-btn:active { transform: scale(0.95); }
        .env-btn:hover { color: var(--primary); }
        .env-btn.active { color: white; }

        .env-indicator {
            position: absolute; height: calc(100% - 0.8rem); top: 0.4rem; left: 0.4rem;
            background: var(--primary); border-radius: 99px; z-index: 1;
            transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
            width: 0; pointer-events: none;
        }

        .nav-btn:hover { color: var(--text-main); }
        .nav-btn.active { color: var(--primary); }
        .nav-btn i { font-size: 1.1rem; transition: transform 0.3s; }
        .nav-btn.active i { transform: scale(1.15); }
        .nav-indicator {
            position: absolute; height: calc(100% - 1rem); top: 0.5rem; left: 0.5rem;
            background: white; border-radius: 99px; z-index: 1;
            transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.12);
            width: 0; pointer-events: none;
        }

        main { max-width: 1400px; margin: 0 auto; padding: 0 20px; }

        .chart-card { 
            background: transparent;
            border: none;
            box-shadow: none;
            padding: 0;
            margin-bottom: 0; 
        }
        
        /* Glass Legend System */
        .legend-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px; padding: 0 0.5rem;
        }
        .legend-title { font-size: 0.75rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; }
        .legend-controls { display: flex; gap: 8px; }
        
        .legend-btn {
            padding: 0.5rem 1.25rem; border-radius: 12px; border: 1px solid rgba(37, 99, 235, 0.2);
            background: rgba(37, 99, 235, 0.05); color: var(--primary); font-size: 0.7rem; font-weight: 800;
            cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex; align-items: center; gap: 8px; text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        .legend-btn i { font-size: 0.8rem; }
        .legend-btn:hover { 
            background: var(--primary); color: white; 
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
        }
        .legend-btn:active { transform: translateY(0); }
        .legend-btn.unselect { background: #f1f5f9; color: #64748b; border-color: #e2e8f0; }
        .legend-btn.unselect:hover { background: #e2e8f0; color: #1e293b; }

        .custom-legend {
            display: flex; flex-wrap: wrap; gap: 10px; padding: 1.5rem;
            background: rgba(248, 250, 252, 0.5); border-radius: 24px;
            margin-top: 20px; border: 1px solid rgba(37, 99, 235, 0.05);
            backdrop-filter: blur(8px);
        }
        .legend-item {
            display: flex; align-items: center; gap: 8px;
            padding: 6px 14px; border-radius: 99px; cursor: pointer;
            background: white; border: 1px solid var(--border);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none; -webkit-tap-highlight-color: transparent;
        }
        .legend-item:hover { transform: translateY(-2px); border-color: var(--primary); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1); }
        .legend-item.hidden { opacity: 0.4; background: #f8fafc; filter: grayscale(1); }
        .legend-item.hidden i { border-color: #94a3b8 !important; background: transparent !important; }
        
        .legend-dot { 
            width: 12px; 
            height: 12px; 
            border-radius: 50%; 
            border: 2.5px solid;
            background: transparent;
        }
        .legend-text { font-size: 0.75rem; font-weight: 600; color: #334155; }
        
        .search-box {
            position: relative;
            flex: 1;
            margin-bottom: 1.5rem;
        }
        .search-box i.search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #94a3b8;
            font-size: 0.9rem;
            pointer-events: none;
            z-index: 10;
        }

        .chart-loader {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255,255,255,0.9); backdrop-filter: blur(4px);
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            z-index: 100; gap: 15px; border-radius: 32px;
        }
        .chart-spinner {
            width: 40px; height: 40px; border: 3px solid rgba(37, 99, 235, 0.1);
            border-top: 3px solid var(--primary); border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .clear-search-btn {
            background: white;
            border: 1px solid #cbd5e1;
            color: #475569;
            padding: 0.8rem 1.5rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .clear-search-btn:active { transform: scale(0.96); }
        .clear-search-btn.active {
            background: #fef2f2;
            border-color: #fecaca;
            color: #ef4444;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
        }
        .clear-search-btn.active:hover {
            background: #fee2e2;
            transform: translateY(-1px);
        }
        .clear-search-btn i { font-size: 0.9rem; }

        .search-controls-group {
            display: flex;
            gap: 0.75rem;
            align-items: center;
            flex: 1;
            max-width: 600px;
        }

        .history-section-card {
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.7);
            border-radius: 32px;
            padding: 2rem;
            margin-top: 1.5rem;
            box-shadow: 0 15px 45px rgba(0,0,0,0.02);
        }

        .history-header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: transparent;
            padding: 1rem 0 2rem 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 2rem;
            flex-wrap: wrap;
            transition: all 0.4s ease;
        }
        .history-header.stuck {
            padding: 1.25rem 2rem;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(15px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.06);
            border-bottom: 1px solid #e2e8f0;
            border-radius: 20px;
            margin: 0 -1rem;
        }

        .history-header .search-box {
            margin-bottom: 0;
            flex: 1;
            min-width: 300px;
            max-width: 500px;
        }

        .section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            font-size: 1.85rem;
            font-weight: 800;
            color: #494444;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
            padding-left: 0;
        }
        .toggle-btn {
            background: rgba(37, 99, 235, 0.05);
            border: 1px solid rgba(37, 99, 235, 0.1);
            color: var(--primary);
            padding: 0.5rem 1rem;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .toggle-btn:hover { background: rgba(37, 99, 235, 0.1); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1); }
        .toggle-btn:active { transform: scale(0.95); }
        
        summary.search-active { 
            background: #f5f7ff !important; 
            border-left: 6px solid #4f46e5 !important;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.1) !important;
        }
        summary.search-active .sprint-id { color: #4338ca !important; }
        summary.search-active .meta-item i { color: #4f46e5 !important; }
        
        .search-box input {
            width: 100%;
            padding: 0.8rem 1rem 0.8rem 2.8rem;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            background: #ffffff;
            color: #1e293b;
            font-size: 0.95rem;
            font-weight: 600;
            transition: all 0.3s ease;
            outline: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .search-box input:focus {
            background: #ffffff;
            border-color: #94a3b8;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .search-box input::placeholder { color: #94a3b8; font-weight: 500; }
        .search-box i {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: #64748b;
            font-size: 1rem;
            pointer-events: none;
            z-index: 10;
        }
        
        .nav-btn {
            padding: 1rem 2rem;
            border-radius: 99px;
            border: none;
            background: transparent;
            color: #64748b;
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
            z-index: 2;
        }
        .nav-btn:active { transform: scale(0.95); }

        .section-title {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.5rem;
            font-weight: 700;
            color: #494444;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
            padding-left: 0;
        }
        .title-highlight { color: var(--primary); }

        .section-title i {
            color: var(--primary);
            font-size: 1.1rem;
        }
        


        .chart-container { height: 450px; }

        /* Collapse Section Branding */
        details { 
            background: #f0f9ff; 
            backdrop-filter: blur(12px);
            border: 1px solid #e0f2fe; 
            border-radius: 24px; 
            margin-bottom: 1.5rem; 
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.03); 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
            overflow: hidden;
        }
        details:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 12px 25px rgba(37, 99, 235, 0.08);
            border-color: #bae6fd;
        }
        
        summary { 
            padding: 1.75rem 2rem; 
            cursor: pointer; 
            background: #f0f9ff; 
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
            background: #f8fafc;
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
        details[open] summary::after { transform: rotate(180deg); background: rgba(37, 99, 235, 0.1); color: var(--primary); }
        details[open] summary { background: #f8fafc; border-bottom: 1px solid var(--border); }
        
        .sprint-header-left { display: flex; align-items: center; gap: 3.5rem; flex: 1; }
        .sprint-id { font-size: 1.1rem; font-weight: 800; color: var(--text-main); white-space: nowrap; }
        .sprint-meta { display: flex; gap: 2.5rem; align-items: center; }
        .meta-item { display: flex; align-items: center; gap: 8px; font-size: 0.90rem; font-weight: 800; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
        .sprint-stats-right { text-align: right; color: var(--primary); font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .meta-item i { color: var(--primary); }

        /* Beautiful Rows for Table */
        .table-wrapper { padding: 0 0.75rem 0.75rem 0.75rem; }
        table { width: 100%; border-collapse: separate; border-spacing: 0 12px; }
        th { 
            padding: 1rem 1.25rem; font-size: 0.7rem; font-weight: 900; 
            color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; 
            border: none; text-align: left; background: #f8fafc;
        }
        th:first-child { border-radius: 12px 0 0 12px; }
        th:last-child { border-radius: 0 12px 12px 0; }
        
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
            border-color: rgba(37, 99, 235, 0.1); 
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
        .api-details p { font-size: 0.7rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; }

        .stat-value { font-size: 1.1rem; font-weight: 900; color: var(--text-main); }
        .stat-label { font-size: 0.65rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-top: 4px; }
        
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
            .container { padding: 0 15px; }
            header { margin: 5px 3% 20px 3%; }
            .header-container { grid-template-columns: 1fr; gap: 1rem; text-align: center; }
            .nav-section { justify-content: center; flex-direction: column; align-items: center; }
            .audit-section { text-align: center; }
            .audit-time { justify-content: center; }
            .header-home-btn { display: flex !important; }

            .main-nav { 
                width: 94%; padding: 0.35rem; margin: 0 auto 2.5rem auto; 
                flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch;
            }
            .nav-btn { padding: 0.6rem 1.25rem; font-size: 0.75rem; flex-shrink: 0; }

            .chart-card { padding: 1rem; border-radius: 20px; margin-bottom: 1.5rem; }
            .chart-container { height: 260px !important; }

            .section-title { font-size: 1.3rem; padding-left: 0; border: none; margin-bottom: 1.25rem; }

            /* Refined Table to Card Transformation */
            .table-wrapper { 
                padding: 0; 
                overflow-x: auto !important; 
                scrollbar-width: thin; 
                -ms-overflow-style: auto;
                -webkit-overflow-scrolling: touch;
                margin: 0 -3%;
                padding: 0 3%;
            }
            .table-wrapper::-webkit-scrollbar {
                height: 4px;
                display: block;
            }
            .table-wrapper::-webkit-scrollbar-thumb {
                background: rgba(37, 99, 235, 0.2);
                border-radius: 10px;
            }
            
            table, thead, tbody, th, td, tr { display: block; width: 100%; }
            thead { display: none; }
            
            .api-row { 
                margin-bottom: 1rem; border: 1px solid var(--border); 
                border-radius: 18px !important; background: white;
                box-shadow: 0 4px 12px rgba(0,0,0,0.03); 
                display: flex !important; flex-direction: row !important;
                width: max-content !important;
                min-width: 100% !important;
            }
            
            .api-row td { 
                border: none !important; padding: 1.15rem 1rem !important; 
                display: flex !important; flex-direction: column !important; 
                align-items: center !important; justify-content: center !important;
                background: transparent !important; text-align: center !important;
                flex-shrink: 0 !important; scroll-snap-align: start;
            }
            
            /* Identity Column */
            .api-row td:nth-child(1) { 
                width: 190px !important; background: #f8fafc !important; 
                align-items: flex-start !important; text-align: left !important;
                border-right: 1px solid #f1f5f9 !important;
                position: sticky; left: 0; z-index: 5;
                padding-left: 1.25rem !important;
            }
            
            /* Stats Columns */
            .api-row td:nth-child(2) { width: 95px !important; border-right: 1px dashed #f1f5f9 !important; }
            .api-row td:nth-child(3) { width: 105px !important; border-right: 1px dashed #f1f5f9 !important; }
            .api-row td:nth-child(4) { width: 115px !important; padding-right: 1.25rem !important; }
            
            .api-info { width: 100%; }
            .api-details h4 { font-size: 0.85rem; word-break: break-all; width: 100%; white-space: normal; line-height: 1.3; }
            .api-details p { font-size: 0.6rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-top: 2px; }
            
            .stat-value { font-size: 0.9rem; font-weight: 800; }
            .stat-label { font-size: 0.55rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-top: 2px; }
            
            .variation-badge { padding: 4px 10px; font-size: 0.7rem; border-radius: 8px; font-weight: 900; }
            
            summary { padding: 1.25rem 1rem; }
            .sprint-id { font-size: 1rem; }
            
            .api-info { width: 100%; }
            .api-details h4 { font-size: 0.85rem; word-break: break-all; width: 100%; white-space: normal; }
            .api-details p { font-size: 0.6rem; color: #94a3b8; }
            
            .stat-value { font-size: 0.85rem; }
            .stat-label { font-size: 0.5rem; color: #94a3b8; }
            
            .variation-badge { padding: 4px 8px; font-size: 0.7rem; border-radius: 8px; }
            
            summary { padding: 1.15rem 1rem; }
            .sprint-id { font-size: 1rem; }
            .sprint-label { gap: 0.75rem; }
            .sprint-meta { flex-direction: column; gap: 2px; }
            .meta-item { font-size: 0.6rem; }
            
            .api-icon { display: none !important; }
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
            position: fixed; top: 50%; right: 25px; z-index: 9999;
            margin-top: -21px;
            width: 42px; height: 42px; border-radius: 14px;
            background: rgba(37, 99, 235, 0.9); backdrop-filter: blur(8px);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 1.1rem; text-decoration: none;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.3);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .floating-home:hover { transform: scale(1.1) translateX(-5px); box-shadow: 0 15px 40px rgba(37, 99, 235, 0.45); background: var(--primary); }
        .floating-home i { transition: transform 0.3s ease; }
        .floating-home:hover i { transform: rotate(-10deg); }

        @media (max-width: 768px) {
            main { padding: 0 10px; }
            .history-section-card { padding: 1.25rem 0.75rem; border-radius: 24px; margin-top: 1rem; }
            .chart-card { padding: 0; }
            .chart-container { height: 350px !important; margin: 0 -0.25rem; }
            .history-header { padding: 0 0 1rem 0; }
            
            header { padding: 10px 0 20px 0; margin-bottom: 10px; }
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

            summary { 
                padding: 1.5rem !important; 
                display: flex !important; 
                flex-direction: column !important; 
                align-items: center !important; 
                gap: 0.75rem !important; 
                text-align: center !important;
                border-radius: 20px !important;
                position: relative;
            }
            .sprint-header-left { display: flex !important; flex-direction: column; align-items: center; width: 100%; gap: 8px !important; }
            .sprint-id { font-size: 1.1rem; font-weight: 800; color: #1e293b; margin: 0 0 2px 0 !important; text-align: center; }
            .sprint-meta { display: flex; gap: 1rem; flex-direction: row !important; align-items: center; justify-content: center !important; flex-wrap: wrap; width: 100%; }
            .meta-item { font-size: 0.7rem; gap: 6px; font-weight: 700; color: #475569; }
            .sprint-stats-right { display: flex; justify-content: center !important; width: 100%; margin-top: 2px; text-align: center; }
            summary::after { position: absolute; right: 1rem; top: 1.25rem; width: 28px; height: 28px; transform: none; }
            details[open] summary::after { transform: rotate(180deg); }

            .api-row td { padding: 0.8rem 1rem !important; }
            .stat-value { font-size: 0.8rem; }
            
            /* Compact Mobile Adjustments */
            .custom-legend { 
                padding: 0.75rem; gap: 8px; border-radius: 20px; 
                display: grid; grid-template-columns: 1fr 1fr; 
            }
            .legend-item { 
                width: 100%; 
                min-width: 0;
                justify-content: flex-start; 
                padding: 6px 10px;
                gap: 6px;
            }
            .legend-text { font-size: 0.65rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            
            .env-nav { 
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                gap: 8px;
                padding: 8px;
                width: 100%;
                border-radius: 16px;
                margin-bottom: 2rem;
                background: rgba(255, 255, 255, 0.5);
                backdrop-filter: blur(10px);
            }
            .env-btn { 
                padding: 10px 4px;
                font-size: 0.7rem;
                width: 100%;
                text-align: center;
                min-width: 0;
                border-radius: 10px;
                background: transparent;
                transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .env-btn.active {
                background: var(--primary) !important;
                color: white !important;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
            }
            .env-indicator { display: none !important; }
            
            .history-header { flex-direction: column; align-items: flex-start; gap: 1.5rem; padding: 1.5rem 0; }
            .history-header .section-title { width: 100%; text-align: center; }
            .search-controls-group { flex-direction: column; width: 100%; max-width: none !important; }
            .search-box { min-width: 0 !important; width: 100% !important; margin-bottom: 0; }
            .clear-search-btn { width: 100%; justify-content: center; }
            
            .legend-header { flex-direction: column; align-items: flex-start; gap: 12px; }
            .legend-controls { width: 100%; justify-content: space-between; }
            .legend-btn { flex: 1; justify-content: center; padding: 0.6rem; font-size: 0.6rem; }
            .floating-home { display: none !important; }

            footer { 
                flex-direction: column; gap: 1.5rem; margin-top: 4rem; 
                text-align: center; padding: 2rem 1rem; 
            }
            .mobile-home-btn { display: flex !important; margin: 0 auto 10px; }
        }
        .mobile-home-btn {
            display: none; align-items: center; justify-content: center; width: 44px; height: 44px;
            border-radius: 12px; background: #eff6ff; color: #2563eb;
            border: 1px solid #dbeafe; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.1);
            text-decoration: none; transition: all 0.2s; z-index: 100;
        }
        .mobile-home-btn:active { transform: scale(0.9); background: #dbeafe; }

        @media (max-width: 480px) {
            .chart-container { height: 320px !important; }
            .title-section h1 { font-size: 1.2rem; }
            .subtitle { font-size: 0.75rem; }
            .main-nav { margin: 0 auto 1.5rem auto; }
        }
    </style>
</head>
<body>
    <div class="bg-blobs">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
    </div>

    <div id="loader">
        <div class="loader-spinner"></div>
        <img src="https://hirepro.in/wp-content/uploads/2025/05/HirePro-logo.svg" alt="HirePro Logo" class="loader-logo">
    </div>

    <header>
        <div class="header-container">
            <a href="dashboard.html" class="mobile-home-btn">
                <i class="fas fa-home"></i>
            </a>
            <div class="nav-section">
                <a href="dashboard.html" style="text-decoration: none; display: flex; align-items: center;">
                    <img src="https://hirepro.in/wp-content/uploads/2025/05/HirePro-logo.svg" alt="HirePro Logo" class="logo-img">
                </a>
            </div>
            <div class="title-section">
                <h1>Performance Analytics</h1>
                <div class="subtitle">API Response Time Trends & Historical Audit</div>
            </div>
            <div class="audit-section">
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
            <button class="nav-btn active" onclick="switchOp('get', this)">
                <i class="fas fa-chart-line"></i> GET Operations
            </button>
            <button class="nav-btn" onclick="switchOp('set', this)">
                <i class="fas fa-upload"></i> SET Operations
            </button>
        </div>

        <div class="nav-group">
            <div class="nav-label">ENVIRONMENT SELECTION</div>
            <div class="env-nav">
                __ENV_BTNS__
            </div>
        </div>

        <section id="report-content">
            <div class="history-section-card" id="chart-section-wrapper" style="margin-bottom: 1.5rem;">
                <div class="history-header" style="position: static; background: transparent; box-shadow: none; padding-top: 0; display: flex; align-items: center; justify-content: space-between;">
                    <div class="section-title" style="margin: 0; font-family: auto;">
                        <span id="chart-title">GET APIs Performance Trend | <span class="title-highlight">__ENV__</span></span>
                    </div>
                    <button class="toggle-btn" onclick="toggleChart()">
                        <i class="fas fa-eye-slash"></i> Hide Graph
                    </button>
                </div>
                
                <div class="chart-card" style="position: relative;">
                    <div id="chart-loader" class="chart-loader" style="display: none;">
                        <div class="chart-spinner"></div>
                        <div style="font-weight: 700; color: var(--primary); font-size: 0.9rem; letter-spacing: 0.02em;">Synchronizing Trend Data...</div>
                    </div>
                    <div class="legend-header">
                        <div class="legend-title">API Visibility Control</div>
                        <div class="legend-controls">
                            <button class="legend-btn" onclick="toggleAll(true)">
                                <i class="fas fa-check-double"></i> Select All
                            </button>
                            <button class="legend-btn unselect" onclick="toggleAll(false)">
                                <i class="fas fa-times-circle"></i> Clear All
                            </button>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="mainChart"></canvas>
                    </div>
                    <div id="main-legend" class="custom-legend"></div>
                </div>
            </div>

            <div class="history-section-card">
                <div class="history-header">
                    <div class="section-title" style="margin: 0; font-family: auto;"><span id="history-title">GET Historical Data Audit | <span class="title-highlight">__ENV__</span></span></div>
                    <div class="search-controls-group">
                        <div class="search-box">
                            <i class="fas fa-search search-icon"></i>
                            <input type="text" id="apiSearch" placeholder="Search API endpoint..." oninput="handleSearch(this.value)">
                        </div>
                        <button class="clear-search-btn" id="clearBtn" onclick="clearSearch()">
                            <i class="fas fa-redo-alt"></i> Clear Search
                        </button>
                    </div>
                </div>
                <div id="history-list"></div>
            </div>
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
        let currentEnv = "__DEFAULT_ENV__";
        let currentOp = "get";
        let mainChart = null;

        function updateIndicator(btn) {
            const indicator = document.querySelector('.nav-indicator');
            const activeBtn = btn || document.querySelector('.main-nav .nav-btn.active');
            if (activeBtn && indicator) {
                indicator.style.width = activeBtn.offsetWidth + 'px';
                indicator.style.left = activeBtn.offsetLeft + 'px';
            }
        }

        function updateEnvIndicator(btn) {
            const indicator = document.querySelector('.env-indicator');
            const activeBtn = btn || document.querySelector('.env-nav .env-btn.active');
            if (activeBtn && indicator) {
                indicator.style.width = activeBtn.offsetWidth + 'px';
                indicator.style.left = activeBtn.offsetLeft + 'px';
            }
        }

        function switchOp(op, btn) {
            currentOp = op;
            document.querySelectorAll('.main-nav .nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateIndicator(btn);
            renderContent();
        }

        function switchEnv(env, btn) {
            currentEnv = env;
            document.querySelectorAll('.env-nav .env-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateEnvIndicator(btn);
            renderContent();
        }

        function renderContent() {
            // Reset search on content switch
            const searchInput = document.getElementById('apiSearch');
            if (searchInput) searchInput.value = '';

            const reportData = data.reports[currentEnv][currentOp];
            
            // Update Titles
            document.getElementById('chart-title').innerHTML = `${currentOp.toUpperCase()} APIs Performance Trend | <span class="title-highlight">${currentEnv}</span>`;
            document.getElementById('history-title').innerHTML = `${currentOp.toUpperCase()} Historical Data Audit | <span class="title-highlight">${currentEnv}</span>`;

            // Reset List
            const list = document.getElementById('history-list');
            list.innerHTML = '';
            populateGroups('history-list', reportData);

            // Re-init Chart
            if (mainChart) mainChart.destroy();
            initChart(reportData);
        }

        function populateGroups(listId, reportData) {
            const list = document.getElementById(listId);
            if (!reportData || reportData.length === 0) {
                list.innerHTML = '<div style="padding: 2rem; text-align: center; color: #64748b; font-weight: 700;">No data available for this environment</div>';
                return;
            }
            
            reportData.forEach((sprint, idx) => {
                const details = document.createElement('details');
                
                details.innerHTML = `
                    <summary>
                        <div class="sprint-header-left">
                            <div class="sprint-id">${sprint.sprint}</div>
                            <div class="sprint-meta">
                                <div class="meta-item"><i class="fas fa-calendar-alt"></i> ${sprint.run_date}</div>
                                <div class="meta-item"><i class="fas fa-mouse-pointer"></i> ${sprint.hits} Hits</div>
                            </div>
                        </div>
                        <div class="sprint-stats-right">
                            <i class="fas fa-microchip"></i> ${sprint.apis.length} Endpoints
                        </div>
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

        function handleSearch(query) {
            const q = query.toLowerCase();
            const clearBtn = document.getElementById('clearBtn');
            const chartCard = document.querySelector('.chart-card');
            const toggleBtn = document.querySelector('.toggle-btn');

            if (clearBtn) {
                if (q !== '') {
                    clearBtn.classList.add('active');
                    // Auto-hide graph on search to focus on results
                    if (chartCard && chartCard.style.display !== 'none') {
                        chartCard.style.display = 'none';
                        if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-chart-area"></i> Show Graph';
                    }
                } else {
                    clearBtn.classList.remove('active');
                }
            }

            // Visual feedback on headers
            document.querySelectorAll('summary').forEach(s => {
                if (q !== "") {
                    s.classList.add('search-active');
                    s.parentElement.classList.add('search-active');
                } else {
                    s.classList.remove('search-active');
                    s.parentElement.classList.remove('search-active');
                }
            });
            
            // Filter Chart Datasets
            if (mainChart) {
                mainChart.data.datasets.forEach((ds, i) => {
                    const matches = ds.label.toLowerCase().includes(q);
                    mainChart.setDatasetVisibility(i, matches);
                });
                mainChart.update();
            }
            
            // Filter Legend Items
            document.querySelectorAll('.legend-item').forEach(item => {
                const text = item.querySelector('.legend-text').innerText.toLowerCase();
                item.style.display = text.includes(q) ? 'flex' : 'none';
            });

            // Filter Audit Logs and Sprints (Across all 5 sprints)
            document.querySelectorAll('details').forEach(details => {
                let matchCount = 0;
                const rows = details.querySelectorAll('.api-row');
                rows.forEach(row => {
                    const apiName = row.querySelector('h4').innerText.toLowerCase();
                    const matches = apiName.includes(q);
                    row.style.display = matches ? 'table-row' : 'none';
                    if (matches) matchCount++;
                });

                if (q === "") {
                    details.style.display = 'block';
                    details.open = false;
                } else {
                    if (matchCount > 0) {
                        details.style.display = 'block';
                        details.open = true;
                    } else {
                        details.style.display = 'none';
                    }
                }
            });
        }

        function clearSearch() {
            const input = document.getElementById('apiSearch');
            input.value = '';
            handleSearch('');
        }

        function toggleChart() {
            const card = document.querySelector('.chart-card');
            const btn = document.querySelector('.toggle-btn');
            const loader = document.getElementById('chart-loader');
            
            if (card.style.display === 'none') {
                if (loader) loader.style.display = 'flex';
                card.style.display = 'block';
                btn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Graph';
                
                // Smooth transition for loader
                setTimeout(() => {
                    if (loader) {
                        loader.style.opacity = '0';
                        setTimeout(() => { 
                            loader.style.display = 'none'; 
                            loader.style.opacity = '1'; 
                        }, 400);
                    }
                }, 700);
            } else {
                card.style.display = 'none';
                btn.innerHTML = '<i class="fas fa-chart-area"></i> Show Graph';
            }
        }

        function toggleAll(show) {
            if (!mainChart) return;
            mainChart.data.datasets.forEach((ds, i) => {
                mainChart.setDatasetVisibility(i, show);
            });
            mainChart.update();
            renderLegend();
        }

        // Sticky Header Observer
        document.addEventListener('DOMContentLoaded', () => {
            const historyHeader = document.querySelector('.history-header');
            if (historyHeader) {
                const observer = new IntersectionObserver( 
                    ([e]) => e.target.classList.toggle('stuck', e.intersectionRatio < 1),
                    { threshold: [1] }
                );
                observer.observe(historyHeader);
            }
        });

        function renderLegend() {
            const legendContainer = document.getElementById('main-legend');
            if (!legendContainer || !mainChart) return;
            legendContainer.innerHTML = '';
            
            mainChart.data.datasets.forEach((dataset, i) => {
                const isVisible = mainChart.isDatasetVisible(i);
                const item = document.createElement('div');
                item.classList.add('legend-item');
                if (!isVisible) item.classList.add('hidden');
                
                item.innerHTML = `
                    <div class="legend-dot" style="border-color: ${dataset.borderColor}"></div>
                    <span class="legend-text">${dataset.label}</span>
                `;
                
                item.onclick = () => {
                    mainChart.setDatasetVisibility(i, !mainChart.isDatasetVisible(i));
                    mainChart.update();
                    renderLegend();
                };
                
                legendContainer.appendChild(item);
            });
        }

        function initChart(reportData) {
            if (!reportData || reportData.length === 0) return;
            
            const ctx = document.getElementById('mainChart').getContext('2d');
            const sprints = [...reportData].reverse();
            const labels = sprints.map(s => s.sprint);
            
            const datasets = sprints[0].apis.map((api, idx) => ({
                label: api.name,
                data: sprints.map(s => {
                    const match = s.apis.find(a => a.name === api.name);
                    return match ? match.current : 0;
                }),
                borderColor: `hsl(${(idx * 137) % 360}, 75%, 60%)`,
                backgroundColor: `hsl(${(idx * 137) % 360}, 75%, 60%, 0.05)`,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: 'white',
                fill: true
            }));

            mainChart = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { 
                        legend: { display: false },
                        tooltip: { 
                            enabled: window.innerWidth > 768,
                            mode: 'index', 
                            intersect: false 
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true, 
                            grid: { color: 'rgba(0,0,0,0.03)', drawBorder: false }, 
                            ticks: { 
                                callback: v => v + 's',
                                font: { size: 11, weight: '600' },
                                color: '#94a3b8'
                            } 
                        },
                        x: { 
                            grid: { display: false },
                            ticks: {
                                maxRotation: 0,
                                autoSkip: true,
                                font: { size: 11, weight: '600' },
                                color: '#94a3b8'
                            }
                        }
                    }
                }
            });
            
            renderLegend();
        }

        window.onload = () => {
            renderContent();
            updateIndicator();
            
            // Auto-hide graph on mobile on load for a cleaner start
            if (window.innerWidth <= 768) {
                const chartCard = document.querySelector('.chart-card');
                const toggleBtn = document.querySelector('.toggle-btn');
                if (chartCard && toggleBtn) {
                    chartCard.style.display = 'none';
                    toggleBtn.innerHTML = '<i class="fas fa-chart-area"></i> Show Graph';
                }
            }
            const loader = document.getElementById('loader');
            setTimeout(() => {
                loader.style.opacity = '0';
                updateIndicator();
                updateEnvIndicator();
                setTimeout(() => { loader.style.display = 'none'; }, 500);
            }, 800);
        };

        window.onresize = () => {
            updateIndicator();
            updateEnvIndicator();
        };
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

# Generate Env Buttons
env_btns_html = '<div class="env-indicator"></div>\n'
for i, env in enumerate(environments):
    active_class = "active" if i == 0 else ""
    env_btns_html += f'<button class="env-btn {active_class}" onclick="switchEnv(\'{env}\', this)">{env}</button>\n'

default_env = environments[0] if environments else ""

full_html = html_template.replace("__DATA_JSON__", json.dumps(final_data))
full_html = full_html.replace("__BUILD_ID__", build_id)
full_html = full_html.replace("__LATEST_DATE__", latest_display)
full_html = full_html.replace("__ENV_BTNS__", env_btns_html)
full_html = full_html.replace("__DEFAULT_ENV__", default_env)

output_file = configfile.PERFORMANCE_HTML
with open(output_file, "w") as f:
    f.write(full_html)

print(f"Performance HTML generated successfully for {len(environments)} environments.")
