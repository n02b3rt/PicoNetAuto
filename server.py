from flask import Flask, request, jsonify
import json
import csv
import os
from datetime import datetime

# Wczytanie konfiguracji urządzeń z `config.json`
with open("config.json", "r") as f:
    config = json.load(f)

app = Flask(__name__)

CSV_FILE = "data_log.csv"

# Jeśli plik CSV nie istnieje, utwórz go i dodaj nagłówki
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "device", "gpio"])  # Nagłówki

@app.route('/device_config/<mac_address>', methods=['GET'])
def get_device_config(mac_address):
    """Zwraca konfigurację dla danego Pico W"""
    if mac_address in config["devices"]:
        device_config = config["devices"][mac_address]
        return jsonify(device_config)
    else:
        return jsonify({"error": "Device not found"}), 404

@app.route('/data', methods=['POST'])
def receive_data():
    """Odbiera dane GPIO i ADC z Pico W i zapisuje do CSV"""
    data = request.json
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Logowanie w konsoli
    print(f"[{timestamp}] Odebrane dane od {data.get('device', 'unknown')}: {data['gpio']}")

    # Zapis do pliku CSV
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, data.get("device", "unknown"), json.dumps(data["gpio"])])

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
