from flask import Flask, request, jsonify
import json

with open("config.json", "r") as f:
    config = json.load(f)

app = Flask(__name__)

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
    """Odbiera dane GPIO i ADC z Pico W"""
    data = request.json
    print(f"Odebrane dane od {data.get('device', 'unknown')}: {data['gpio']}")
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
