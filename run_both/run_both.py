import subprocess

# Chạy app1.py trên port 5000
subprocess.Popen(["python", r"F:\AI-Payment-Gateway\update_csv_app\app.py"])

# Chạy app2.py trên port 5001
subprocess.Popen(["python", "flashsale.py"])
