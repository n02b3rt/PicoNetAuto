import csv
import os
from datetime import datetime

LOG_FILE = "log.csv"

def log_error(error_message):
    """Zapisuje błędy do pliku log.csv oraz wypisuje je na konsolę"""
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{error_time}] ERROR: {error_message}"
    print(log_entry)
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([error_time, error_message])

DRY_VALUE = 49900
WET_VALUE = 18324

def calculate_moisture(value):
    try:
        moisture = (DRY_VALUE - value) / (DRY_VALUE - WET_VALUE)
        return max(0, min(1, moisture))
    except Exception as e:
        log_error(f"Error in calculate_moisture: {str(e)}")
        return 0
