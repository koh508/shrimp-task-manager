import psutil
import time
import datetime
import os

LOG_DIR = "SYSTEM/logs"
LOG_FILE = os.path.join(LOG_DIR, "cpu_alert.log")

def check_cpu_usage():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if cpu_percent > 90:
            alert_message = f"[{timestamp}] WARNING: CPU usage is {cpu_percent}% which exceeds 90% threshold."
            print(alert_message)
            with open(LOG_FILE, "a") as f:
                f.write(alert_message + "\n")
        else:
            status_message = f"[{timestamp}] INFO: CPU usage is {cpu_percent}%."
            print(status_message)

        time.sleep(5) # 5초 간격으로 모니터링

if __name__ == "__main__":
    print("CPU usage monitoring started. Press Ctrl+C to stop.")
    try:
        check_cpu_usage()
    except KeyboardInterrupt:
        print("CPU usage monitoring stopped.")
