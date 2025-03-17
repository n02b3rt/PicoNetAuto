from flask import Flask, request, jsonify
import json
import csv
import os
from datetime import datetime
from utils import log_error

# Wczytanie konfiguracji urządzeń
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    log_error(f"Error loading config.json: {str(e)}")
    config = {"devices": {}}

app = Flask(__name__)

DATA_FOLDER = "data"

os.makedirs(DATA_FOLDER, exist_ok=True)

@app.route('/device_config/<mac_address>', methods=['GET'])
def get_device_config(mac_address):
    """Zwraca konfigurację dla danego urządzenia"""
    try:
        if mac_address in config["devices"]:
            return jsonify(config["devices"][mac_address])
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        log_error(f"Error in /device_config: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/data', methods=['POST'])
def receive_data():
    """Odbiera dane z urządzenia i zapisuje je do plików CSV"""
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
            sensor_data = {"timestamp": timestamp, "device": mac_address, "raw": value}
            file_path = os.path.join(DATA_FOLDER, f"pico_{pico_number}_pin{pin}.csv")
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
