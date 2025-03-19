import csv
import os
from datetime import datetime

LOG_FILE = "log.csv"
DATA_FOLDER = "data"

def log_error(error_message):
    """Zapisuje błędy do pliku log.csv oraz wypisuje je na konsolę"""
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{error_time}] ERROR: {error_message}"
    print(log_entry)
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([error_time, error_message])

def log_dht_data(timestamp, mac_address, pico_number, dht_data, data_folder=DATA_FOLDER):
    """
    Zapisuje dane z czujnika DHT11 (temperatura i wilgotność powietrza) do pliku CSV.

    Nazwa pliku: pico_<pico_number>_dht11.csv.
    Wiersz zawiera: timestamp, device, temperature, humidity.

    Parametry:
      timestamp (str): np. "2025-03-19 01:00:48"
      mac_address (str): Adres MAC urządzenia.
      pico_number (int): Numer Pico (ustalany na podstawie konfiguracji).
      dht_data (dict): Dane z czujnika, np. {"temperature": 21, "humidity": 50}.
      data_folder (str): Folder, w którym zapisywane są pliki CSV.

    Zwraca:
      sensor_data (dict): Słownik z zapisanymi danymi.
    """

    print("\n\n DZIAŁA ZAPISYWANIE TEMPERATURY\n\n")
    filename = f"pico_{pico_number}_dht11.csv"
    file_path = os.path.join(data_folder, filename)
    file_exists = os.path.isfile(file_path)

    sensor_data = {
        "timestamp": timestamp,
        "device": mac_address,
        "temperature": dht_data.get("temperature"),
        "humidity": dht_data.get("humidity")
    }

    try:
        with open(file_path, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=sensor_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(sensor_data)
    except Exception as e:
        log_error(f"Error writing CSV file {file_path}: {str(e)}")

    return sensor_data


def log_bh1750_data(timestamp, mac_address, pico_number, lux_value, data_folder=DATA_FOLDER):
    """
    Zapisuje dane z czujnika BH1750 do pliku CSV.

    Plik CSV nazywa się: pico_<pico_number>_bh1750.csv.
    Wiersz zawiera: timestamp, device, lux.
    """
    filename = f"pico_{pico_number}_bh1750.csv"
    file_path = os.path.join(data_folder, filename)
    file_exists = os.path.isfile(file_path)

    sensor_data = {
        "timestamp": timestamp,
        "device": mac_address,
        "lux": lux_value
    }

    try:
        with open(file_path, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=sensor_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(sensor_data)
    except Exception as e:
        print(f"Error writing CSV file {file_path}: {str(e)}")

    return sensor_data