from datetime import datetime

from flask import Flask, request, jsonify, render_template
import json
import csv
import os
import threading
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

from DataProcessor import DataProcessor
from utils import log_error, log_dht_data, log_bh1750_data
from summary_generator import generate_summary
from latest_data_aggregator import LatestDataAggregator

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

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

aggregator = LatestDataAggregator(DATA_FOLDER)

### **🌍 STRONY WWW**
@app.route('/')
def index():
    """ Strona główna - pokazuje najnowsze odczyty z czujników, w tym wartości RAW """
    latest_readings = aggregator.get_latest_data()

    # Sprawdź, czy `latest_readings` to lista i przekonwertuj na słownik
    if isinstance(latest_readings, list):
        latest_readings = {f"sensor_{i}": reading for i, reading in enumerate(latest_readings)}

    return render_template("index.html", readings=latest_readings)

@app.route('/chart/<sensor_name>')
def chart(sensor_name):
    """ Strona generująca wykres dla danego czujnika """
    file_path = os.path.join(DATA_FOLDER, f"{sensor_name}.csv")

    if not os.path.exists(file_path):
        return f"Brak danych dla czujnika: {sensor_name}", 404

    try:
        df = pd.read_csv(file_path)

        # Sprawdzenie, czy plik ma dane
        if df.empty or "timestamp" not in df.columns:
            print(f"❌ Plik {sensor_name}.csv jest pusty lub nie ma kolumny timestamp!")
            return f"Brak danych w pliku {sensor_name}.csv", 404

        timestamps = df["timestamp"]
        values, raw_values = None, None

        if "moisture" in df and "raw" in df:
            values = df["moisture"]
            raw_values = df["raw"]
        elif "temperature" in df and "humidity" in df:
            values = df["temperature"]
            raw_values = df["humidity"]
        elif "lux" in df:
            values = df["lux"]

        # Jeśli brak poprawnych danych
        if values is None or values.empty:
            print(f"❌ Brak poprawnych wartości do wyświetlenia dla {sensor_name}!")
            return f"Brak danych dla czujnika: {sensor_name}", 404

        # Tworzenie wykresu
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, values, marker='o', linestyle='-', label="Przetworzona wartość")

        if raw_values is not None and not raw_values.empty:
            plt.plot(timestamps, raw_values, marker='x', linestyle='--', label="Wartość RAW", alpha=0.6)

        plt.xticks(rotation=45)
        plt.xlabel("Czas")
        plt.ylabel("Wartość")
        plt.title(f"Wykres czujnika: {sensor_name}")
        plt.legend()
        plt.grid()

        # Zapis wykresu do pamięci
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        img_base64 = base64.b64encode(img.getvalue()).decode()

        return render_template("chart.html", sensor_name=sensor_name, img_base64=img_base64)

    except Exception as e:
        print(f"❌ Błąd generowania wykresu dla {sensor_name}: {str(e)}")
        return f"Błąd generowania wykresu dla {sensor_name}: {str(e)}", 500


### **📡 API**
@app.route('/device_config/<mac_address>', methods=['GET'])
def get_device_config(mac_address):
    """Zwraca konfigurację pinów i interwał dla danego Pico W"""
    try:
        if mac_address in config["devices"]:
            device_config = config["devices"][mac_address]
            pins_config = {pin: pin_data["type"] for pin, pin_data in device_config.get("pins", {}).items()}
            interval = device_config.get("interval", 5)

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
        results = {}

        if "pin_21" in gpio_data:
            dht_data = gpio_data["pin_21"]
            if isinstance(dht_data, dict) and "temperature" in dht_data and "humidity" in dht_data:
                results["dht11"] = log_dht_data(timestamp, mac_address, pico_number, dht_data)
            del gpio_data["pin_21"]

        if "bh1750" in gpio_data:
            lux_value = gpio_data["bh1750"]
            if isinstance(lux_value, (int, float)):
                results["bh1750"] = log_bh1750_data(timestamp, mac_address, pico_number, lux_value)
            del gpio_data["bh1750"]

        device_config = config["devices"][mac_address]
        processor = DataProcessor(mac_address, device_config, timestamp, pico_number)
        responses = processor.process_gpio_data(gpio_data)
        results.update(responses)

        return jsonify({
            "status": "ok",
            "timestamp": timestamp,
            "device": mac_address,
            "data": results
        })

    except Exception as e:
        log_error(f"Error in /data: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

# **Uruchomienie wątku dla generowania podsumowań**
t = threading.Thread(target=generate_summary, daemon=True)
t.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
