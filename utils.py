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
