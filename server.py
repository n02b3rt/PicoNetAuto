from flask import Flask, request, jsonify
import json
import csv
import os
import threading
import pandas as pd
from datetime import datetime

from DataProcessor import DataProcessor
from utils import log_error, log_dht_data, log_bh1750_data
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
    """Zwraca konfigurację pinów i interwał dla danego Pico W"""
    try:
        if mac_address in config["devices"]:
            device_config = config["devices"][mac_address]
            pins_config = {pin: pin_data["type"] for pin, pin_data in device_config.get("pins", {}).items()}
            interval = device_config.get("interval", 5)  # Domyślna wartość 5s

            return jsonify({"pins": pins_config, "interval": interval})
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
        print("\n\nOtrzymane dane:", data)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mac_address = data.get("device", "unknown")
        gpio_data = data.get("gpio", {})

        print("MAC Address:", mac_address)
        print("GPIO data:", gpio_data)

        if not isinstance(gpio_data, dict):
            log_error(f"Invalid GPIO format from {mac_address}")
            return jsonify({"error": "Invalid gpio format"}), 400

        # Sprawdzenie, czy urządzenie jest w konfiguracji
        if mac_address not in config["devices"]:
            log_error(f"Unknown device: {mac_address}")
            return jsonify({"error": "Unknown device"}), 400

        pico_number = list(config["devices"].keys()).index(mac_address) + 1
        results = {}

        # Obsługa czujnika DHT11 (wilgotność i temperatura)
        if "pin_21" in gpio_data:
            dht_data = gpio_data["pin_21"]  # Spodziewamy się formatu: {"temperature": X, "humidity": Y}
            if isinstance(dht_data, dict) and "temperature" in dht_data and "humidity" in dht_data:
                dht_result = log_dht_data(timestamp, mac_address, pico_number, dht_data)
                results["dht11"] = dht_result
                print(f"Odczyt z DHT11 zapisany: {dht_result}")
            else:
                print("Błąd formatu danych DHT11:", dht_data)

            # Usuwamy pin_21, żeby DataProcessor nie traktował go jako analogowy czujnik
            del gpio_data["pin_21"]

        # Obsługa czujnika BH1750 (natężenie światła)
        if "bh1750" in gpio_data:
            lux_value = gpio_data["bh1750"]
            if isinstance(lux_value, (int, float)):
                bh1750_result = log_bh1750_data(timestamp, mac_address, pico_number, lux_value)
                results["bh1750"] = bh1750_result
                print(f"Odczyt z BH1750 zapisany: {bh1750_result}")
            else:
                print("Błąd formatu danych BH1750:", lux_value)

            del gpio_data["bh1750"]  # Usuwamy, żeby DataProcessor nie przetwarzał go jako inny czujnik

        # Obsługa pozostałych czujników (analogowych i cyfrowych)
        device_config = config["devices"][mac_address]
        processor = DataProcessor(mac_address, device_config, timestamp, pico_number)
        responses = processor.process_gpio_data(gpio_data)
        results.update(responses)

        print("Przetworzone odpowiedzi:", results)

        return jsonify({
            "status": "ok",
            "timestamp": timestamp,
            "device": mac_address,
            "data": results
        })

    except Exception as e:
        log_error(f"Error in /data: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


# Uruchomienie wątku dla generowania podsumowań
t = threading.Thread(target=generate_summary, daemon=True)
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
