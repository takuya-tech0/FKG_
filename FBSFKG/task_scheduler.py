import schedule 
import time
import subprocess

def run_script(script_name):
    result = subprocess.run(['python', script_name], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Successfully executed {script_name}")
    else:
        print(f"Error executing {script_name}: {result.stderr}")

def run_all_scripts():
    scripts = [
        r"C:\Users\takuya.oshima\OneDrive - SAPPORO\アプリ開発\FBSFKG\irisearch-selenium_ver1.5.py",
        r"C:\Users\takuya.oshima\OneDrive - SAPPORO\アプリ開発\FBSFKG\tenpo-innovation-selenium_ver1.5.py",
        r"C:\Users\takuya.oshima\OneDrive - SAPPORO\アプリ開発\FBSFKG\tenpo-smart-selenium_ver2.4.py",
        r"C:\Users\takuya.oshima\OneDrive - SAPPORO\アプリ開発\FBSFKG\combine_db_ver1.1.py",
        r"C:\Users\takuya.oshima\OneDrive - SAPPORO\アプリ開発\FBSFKG\run_VBA.py"
    ]

    for script in scripts:
        run_script(script)

# スクリプトを毎日12:26に実行
schedule.every().day.at("12:28").do(run_all_scripts)

while True:
    schedule.run_pending()
    time.sleep(1)
