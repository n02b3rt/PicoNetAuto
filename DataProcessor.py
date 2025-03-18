import os
import csv
from utils import log_error  # Upewnij się, że funkcja log_error jest dostępna

# Domyślne wartości, gdyby w konfiguracji czujnika brakowało DRY/WET
DEFAULT_DRY_VALUE = 49900
DEFAULT_WET_VALUE = 18324

# Folder, w którym zapisywane będą pliki CSV
DATA_FOLDER = "data"


class DataProcessor:
    def __init__(self, mac_address, device_config, timestamp, pico_number):
        self.mac_address = mac_address
        self.device_config = device_config
        self.timestamp = timestamp
        self.pico_number = pico_number

    def calculate_moisture(self, value, dry_value, wet_value):
        try:
            # Przyjmujemy, że wartość równa dry_value oznacza wilgotność 0,
            # a wartość równa wet_value – wilgotność 1.
            moisture = (dry_value - value) / (dry_value - wet_value)
            return max(0, min(1, moisture))
        except Exception as e:
            log_error(f"Error in calculate_moisture: {str(e)}")
            return 0

    def process_gpio_data(self, gpio_data):
        responses = {}
        # Dla każdego pinu (klucz w słowniku gpio odpowiada kluczowi w config.json)
        for pin, value in gpio_data.items():
            # Pobieramy konfigurację dla danego pinu
            pin_config = self.device_config.get("pins", {}).get(pin)
            if (pin_config and isinstance(pin_config, dict) and pin_config.get("type") == "analog"):
                # Jeśli konfiguracja zawiera wartości DRY/WET – używamy ich
                dry_value = pin_config.get("DRY_VALUE", DEFAULT_DRY_VALUE)
                wet_value = pin_config.get("WET_VALUE", DEFAULT_WET_VALUE)
                sensor_name = pin_config.get("name", f"pin{pin}")
                moisture = round(self.calculate_moisture(value, dry_value, wet_value), 2)
            else:
                # Jeśli pin nie jest analogowy lub nie ma konfiguracji, stosujemy domyślne wartości
                sensor_name = f"pin{pin}"
                moisture = round(self.calculate_moisture(value, DEFAULT_DRY_VALUE, DEFAULT_WET_VALUE), 2)

            sensor_data = {
                "timestamp": self.timestamp,
                "device": self.mac_address,
                "raw": value,
                "moisture": moisture
            }
            # Nazwa pliku: pico_<numer>_<nazwa_czujnika>.csv
            filename = f"pico_{self.pico_number}_{sensor_name}.csv"
            file_path = os.path.join(DATA_FOLDER, filename)
            file_exists = os.path.isfile(file_path)
            try:
                with open(file_path, mode="a", newline="") as file:
                    writer = csv.DictWriter(file, fieldnames=sensor_data.keys())
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(sensor_data)
            except Exception as e:
                log_error(f"Error writing CSV file {file_path}: {str(e)}")

            responses[sensor_name] = sensor_data
        return responses
