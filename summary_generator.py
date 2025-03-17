import os
import time
import pandas as pd
from datetime import datetime
from utils import log_error

DATA_FOLDER = "data"
SUMMARY_FOLDER = "summary"
SUMMARY_FILE = os.path.join(SUMMARY_FOLDER, "summary_data.csv")

def generate_summary():
    while True:
        try:
            interval = 5
            if os.path.exists("config.json"):
                import json
                with open("config.json", "r") as f:
                    config = json.load(f)
                interval = config["devices"].get(next(iter(config["devices"])), {}).get("interval", 5)
            
            time.sleep(interval * 60)

            summary_data = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

            for filename in os.listdir(DATA_FOLDER):
                try:
                    file_path = os.path.join(DATA_FOLDER, filename)
                    df = pd.read_csv(file_path)
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df = df.sort_values("timestamp", ascending=False).head(15)
                    avg_moisture = df["moisture"].mean()
                    summary_data[filename.replace(".csv", "")] = round(avg_moisture, 2)
                except Exception as e:
                    log_error(f"Error processing file {filename}: {str(e)}")
            
            file_exists = os.path.isfile(SUMMARY_FILE)
            try:
                with open(SUMMARY_FILE, mode="a", newline="") as file:
                    writer = pd.DataFrame([summary_data])
                    writer.to_csv(file, header=not file_exists, index=False)
            except Exception as e:
                log_error(f"Error writing to summary file: {str(e)}")
        except Exception as e:
            log_error(f"Error in generate_summary: {str(e)}")
