import os
import csv
from io import StringIO

class LatestDataAggregator:
    """
    Klasa przeszukuje folder DATA_FOLDER i dla każdego pliku CSV pobiera ostatni wiersz.
    Do zwracanego wiersza dodaje pole 'sensor_name', wyciągając nazwę czujnika z nazwy pliku.
    """
    def __init__(self, data_folder):
        self.data_folder = data_folder

    def get_latest_data(self):
        aggregated_data = []
        # Iterujemy po wszystkich plikach w folderze
        for filename in os.listdir(self.data_folder):
            if filename.endswith(".csv"):
                file_path = os.path.join(self.data_folder, filename)
                try:
                    with open(file_path, "r", newline="") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if not rows:
                            continue  # brak danych w pliku
                        latest_row = rows[-1]
                except Exception as e:
                    # Opcjonalnie: można dodać logowanie błędu
                    continue

                # Wyciągamy nazwę czujnika z nazwy pliku.
                # Zakładamy, że schemat to: pico_<pico_number>_<sensor_name>.csv
                parts = filename.split("_")
                if len(parts) >= 3:
                    sensor_name_with_ext = parts[2]
                    sensor_name = sensor_name_with_ext.replace(".csv", "")
                else:
                    sensor_name = filename.replace(".csv", "")
                # Dodajemy sensor_name do danych
                latest_row["sensor_name"] = sensor_name
                aggregated_data.append(latest_row)
        return aggregated_data

    def to_csv_string(self, data):
        """Konwertuje listę słowników do łańcucha CSV."""
        if not data:
            return ""
        # Ustalamy nagłówki na podstawie kluczy z pierwszego wiersza
        headers = list(data[0].keys())
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        return output.getvalue()
