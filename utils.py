import csv
import os
from datetime import datetime

LOG_FILE = "log.csv"

def log_error(error_message):
    """Zapisuje błędy do pliku log.csv oraz wypisuje je na konsolę"""
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{error_time}] ERROR: {error_message}"
    print(log_entry)
    with open(LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([error_time, error_message])

def log_temperature_reading(timestamp, device, gpio_data, log_file="temperature_log.csv"):
    """
    Rejestruje odczyt temperatury i wilgotności, jeśli w gpio_data znajduje się klucz 'pin_21'.

    Parametry:
      timestamp (str): Aktualny czas, np. "2025-03-19 01:00:48".
      device (str): Adres MAC urządzenia.
      gpio_data (dict): Dane GPIO, np. {'pin_27': 43722, 'pin_26': 38745, 'pin_21': {"temperature": 21, "humidity": 50}}.
      log_file (str): Ścieżka do pliku logów (domyślnie "temperature_log.csv").

    Zwraca:
      True, jeśli dokonano zapisu (czyli znaleziono klucz 'pin_21'), w przeciwnym razie False.
    """
    if "pin_21" in gpio_data:
        reading = gpio_data["pin_21"]
        # Sprawdzamy, czy odczyt jest słownikiem zawierającym temperaturę i wilgotność
        if isinstance(reading, dict):
            temperature = reading.get("temperature")
            humidity = reading.get("humidity")
        else:
            temperature = reading
            humidity = None

        # Format: timestamp,device,temperature,humidity
        humidity_str = str(humidity) if humidity is not None else ""
        line = f"{timestamp},{device},{temperature},{humidity_str}\n"
        with open(log_file, "a") as f:
            f.write(line)
        return True
    return False

