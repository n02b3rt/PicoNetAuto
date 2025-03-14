from flask import Flask, request, jsonify
import json
import csv
import os
from datetime import datetime

# Skrajne wartości czujnika
DRY_VALUE = 49900  # Wartość dla suchego czujnika
WET_VALUE = 18324  # Wartość dla czujnika w wodzie


def calculate_moisture(value):
    """Oblicza wilgotność gleby w przedziale <0,1>"""
    moisture = (DRY_VALUE - value) / (DRY_VALUE - WET_VALUE)
    return max(0, min(1, moisture))  # Ograniczenie do przedziału <0,1>


# Wczytanie konfiguracji urządzeń z `config.json`
with open("config.json", "r") as f:
    config = json.load(f)

app = Flask(__name__)

CSV_FILE = "data_log.csv"

# Jeśli plik CSV nie istnieje, utwórz go i dodaj nagłówki
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "device", "gpio"])


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
    """Odbiera dane GPIO i ADC z Pico W, oblicza wilgotność i zapisuje do CSV"""
    data = request.json
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    gpio_data = data.get("gpio", {})  # Pobranie wartości GPIO jako słownik
    if not isinstance(gpio_data, dict):
        return jsonify({"error": "Invalid gpio format"}), 400

    # Oblicz wilgotność dla pin_26 jeśli istnieje
    if "pin_26" in gpio_data:
        original_value = gpio_data["pin_26"]
        moisture = round(calculate_moisture(original_value), 2)
        gpio_data["pin_26"] = {"raw": original_value, "moisture": moisture}

    device = data.get("device", "unknown")

    # Logowanie w konsoli
    print(f"[{timestamp}] Odebrane dane od {device}: {json.dumps(gpio_data)}")

    # Zapis do pliku CSV
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, device, json.dumps(gpio_data)])

    return jsonify({"status": "ok", "timestamp": timestamp, "device": device, "gpio": gpio_data})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
