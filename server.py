from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 🔹 Wczytaj konfigurację z pliku `config.json`
with open("config.json", "r") as f:
    config = json.load(f)

WIFI_CONFIG = config["wifi"]
MQTT_BROKER = config["mqtt"]["broker"]
MQTT_PORT = config["mqtt"]["port"]
ENCRYPTION_KEY = config["encryption_key"].encode("utf-8")  # Klucz do szyfrowania (musi mieć 16, 24 lub 32 bajty)

# Inicjalizacja MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

app = Flask(__name__)

def encrypt_data(data):
    """
    Szyfruje dane AES-256 i koduje w Base64.
    """
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)  # Używamy CBC
    ciphertext = cipher.encrypt(pad(data.encode(), AES.block_size))
    return base64.b64encode(cipher.iv + ciphertext).decode()

@app.route('/wifi_config/<mac_address>', methods=['GET'])
def get_wifi_config(mac_address):
    """
    Endpoint zwracający zaszyfrowane dane WiFi dla Pico W.
    """
    wifi_data = json.dumps(WIFI_CONFIG)
    encrypted_wifi = encrypt_data(wifi_data)
    return jsonify({"config": encrypted_wifi})

@app.route('/data', methods=['POST'])
def receive_data():
    """
    Endpoint do odbierania danych GPIO i ADC z Pico W.
    """
    data = request.json
    print(f"Odebrane dane od {data.get('device', 'unknown')}: {data['gpio']}")

    # Opcjonalnie wysyłamy dane do MQTT
    topic = f"pico/{data['device']}/gpio"
    mqtt_client.publish(topic, str(data['gpio']))

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
