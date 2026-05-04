import subprocess
import os
import sys

def run_reports():
    # Get the directory of the current script
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to the report generation scripts
    perf_script = os.path.join(scripts_dir, "generate_performance.py")
    dash_script = os.path.join(scripts_dir, "generate_dashboard.py")
    landing_script = os.path.join(scripts_dir, "generate_landing.py")
    
    # Root directory for correctly importing modules like Config
    root_dir = os.path.dirname(scripts_dir)
    
    # Set up environment to include root_dir in PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")

    print("\n" + "="*50)
    print("     HIREPRO REPORT GENERATION PIPELINE")
    print("="*50 + "\n")

    # 1. Run Performance Report Generator
    print("📈 Step 1: Generating Performance Metrics...")
    try:
        subprocess.run([sys.executable, perf_script], cwd=root_dir, env=env, check=True)
        print("✅ Performance Report Updated.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in Performance Report: {e}\n")

    # 1.5 Run Daily Performance Report Generator
    print("📅 Step 1.5: Generating Daily Performance Report (Multi-Env)...")
    try:
        daily_perf_script = os.path.join(scripts_dir, "generate_performance_daily.py")
        subprocess.run([sys.executable, daily_perf_script], cwd=root_dir, env=env, check=True)
        print("✅ Daily Performance Report Updated.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in Daily Performance Report: {e}\n")

    # 2. Run Main Dashboard Generator
    print("🖥️  Step 2: Generating Main Automation Dashboard...")
    try:
        subprocess.run([sys.executable, dash_script], cwd=root_dir, env=env, check=True)
        print("✅ Main Dashboard Updated.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in Dashboard Report: {e}\n")

    # 3. Run Landing Page Generator
    print("🏠 Step 3: Generating Main Landing Hub (dashboard.html)...")
    try:
        subprocess.run([sys.executable, landing_script], cwd=root_dir, env=env, check=True)
        print("✅ Landing Hub Updated.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in Landing Hub: {e}\n")

    print("="*50)
    print("✨ ALL REPORTS ARE NOW UP TO DATE!")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_reports()
