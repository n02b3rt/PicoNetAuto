from flask import Flask, request, jsonify
import json
import csv
import os
import threading
import pandas as pd
from datetime import datetime
from utils import log_error, calculate_moisture
from summary_generator import generate_summary

# Wczytanie konfiguracji urządzeń
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    log_error(f"Error loading config.json: {str(e)}")
    config = {"devices": {}}

app = Flask(__name__)

DATA_FOLDER = "data"
SUMMARY_FOLDER = "summary"
SUMMARY_FILE = os.path.join(SUMMARY_FOLDER, "summary_data.csv")

# Tworzenie folderów jeśli nie istnieją
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

@app.route('/device_config/<mac_address>', methods=['GET'])
def get_device_config(mac_address):
    """Zwraca konfigurację dla danego Pico W"""
    try:
        if mac_address in config["devices"]:
            device_config = config["devices"][mac_address]
            return jsonify(device_config)
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        log_error(f"Error in /device_config: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/summary_data', methods=['GET'])
def get_summary_data():
    try:
        if not os.path.exists(SUMMARY_FILE):
            return jsonify({"error": "No summary data available"}), 404
        df = pd.read_csv(SUMMARY_FILE)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        log_error(f"Error in /summary_data: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/latest_summary', methods=['GET'])
def get_latest_summary():
    try:
        if not os.path.exists(SUMMARY_FILE):
            return jsonify({"error": "No summary data available"}), 404
        df = pd.read_csv(SUMMARY_FILE)
        latest_entry = df.iloc[-1].to_dict()
        return jsonify(latest_entry)
    except Exception as e:
        log_error(f"Error in /latest_summary: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/data', methods=['POST'])
def receive_data():
    """Odbiera dane GPIO i ADC z Pico W, oblicza wilgotność i zapisuje do CSV"""
    try:
        data = request.json
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mac_address = data.get("device", "unknown")
        gpio_data = data.get("gpio", {})

        if not isinstance(gpio_data, dict):
            log_error(f"Invalid GPIO format from {mac_address}")
            return jsonify({"error": "Invalid gpio format"}), 400

        if mac_address not in config["devices"]:
            log_error(f"Unknown device: {mac_address}")
            return jsonify({"error": "Unknown device"}), 400

        pico_number = list(config["devices"].keys()).index(mac_address) + 1

        for pin, value in gpio_data.items():
            moisture = round(calculate_moisture(value), 2)
            sensor_data = {"timestamp": timestamp, "device": mac_address, "raw": value, "moisture": moisture}
            file_path = os.path.join(DATA_FOLDER, f"pico_{pico_number}_czujnik_pin{pin}.csv")
            file_exists = os.path.isfile(file_path)

            with open(file_path, mode="a", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=sensor_data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(sensor_data)

        return jsonify({"status": "ok", "timestamp": timestamp, "device": mac_address})
    except Exception as e:
        log_error(f"Error in /data: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

# Uruchomienie wątku dla generowania podsumowań
t = threading.Thread(target=generate_summary, daemon=True)
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
