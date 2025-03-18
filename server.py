from flask import Flask, request, jsonify
import json
import os
import threading
import pandas as pd
from datetime import datetime
from utils import log_error
from summary_generator import generate_summary
from DataProcessor import DataProcessor

app = Flask(__name__)

# Wczytanie konfiguracji z pliku config.json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    log_error(f"Error loading config.json: {str(e)}")
    config = {"devices": {}}

DATA_FOLDER = "data"
SUMMARY_FOLDER = "summary"
SUMMARY_FILE = os.path.join(SUMMARY_FOLDER, "summary_data.csv")

# Tworzymy foldery, jeśli nie istnieją
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

@app.route('/device_config/<mac_address>', methods=['GET'])
def get_device_config(mac_address):
    """Zwraca uproszczoną konfigurację dla danego urządzenia Pico W."""
    try:
        if mac_address in config["devices"]:
            device_config = config["devices"][mac_address]
            # Tworzymy uproszczony obiekt konfiguracji
            simplified_config = {
                "interval": device_config.get("interval", 5),
                "pins": {}
            }
            # Dla każdego pinu zwracamy tylko typ, np. "analog" lub "digital"
            for pin, details in device_config.get("pins", {}).items():
                if isinstance(details, dict):
                    simplified_config["pins"][pin] = details.get("type", details)
                else:
                    simplified_config["pins"][pin] = details
            return jsonify(simplified_config)
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
    try:
        data = request.json
        print("Otrzymane dane:", data)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mac_address = data.get("device", "unknown")
        gpio_data = data.get("gpio", {})

        print("MAC Address:", mac_address)
        print("GPIO data:", gpio_data)

        if not isinstance(gpio_data, dict):
            log_error(f"Invalid GPIO format from {mac_address}")
            return jsonify({"error": "Invalid gpio format"}), 400

        if mac_address not in config["devices"]:
            log_error(f"Unknown device: {mac_address}")
            return jsonify({"error": "Unknown device"}), 400

        device_config = config["devices"][mac_address]
        # Numer Pico ustalamy na podstawie kolejności urządzeń w configu
        pico_number = list(config["devices"].keys()).index(mac_address) + 1

        processor = DataProcessor(mac_address, device_config, timestamp, pico_number)
        responses = processor.process_gpio_data(gpio_data)

        print("Przetworzone odpowiedzi:", responses)

        return jsonify({
            "status": "ok",
            "timestamp": timestamp,
            "device": mac_address,
            "data": responses
        })
    except Exception as e:
        log_error(f"Error in /data: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

# Uruchomienie wątku do generowania podsumowań (jeśli masz taką funkcję)
t = threading.Thread(target=generate_summary, daemon=True)
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
