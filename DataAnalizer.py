import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt

# 📥 Wczytanie danych z pliku CSV, dodanie nagłówków ręcznie
df = pd.read_csv("data_log_2_50k.csv", names=["timestamp", "device", "gpio"], header=None)

# 📌 Konwersja czasu na format datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])

# 📌 Rozpakowanie JSON z kolumny "gpio" i wyciągnięcie wartości z czujnika wilgotności (pin_26)
def extract_moisture(value):
    try:
        data = json.loads(value.replace("'", "\""))  # Zamiana ' na " jeśli potrzeba
        return data.get("pin_26", np.nan)  # Pobranie wartości wilgotności z ADC na GP26
    except:
        return np.nan  # Jeśli błąd, zwróć NaN

df["Wilgotność Analog"] = df["gpio"].apply(extract_moisture)

# 📉 Grupowanie danych co 10 minut
df_resampled = df.resample("1min", on="timestamp").agg({
    "Wilgotność Analog": ["mean", "median", "min", "max", "std"]
})

# 🔄 Reset indeksu, żeby było czytelnie
df_resampled.columns = ["Średnia", "Mediana", "Min", "Max", "Odchylenie Std"]
df_resampled = df_resampled.reset_index()

# 📁 Zapis do pliku CSV
df_resampled.to_csv("sensor_data_analysis.csv", index=False)
print("📁 Dane zapisane do sensor_data_analysis.csv")

# 📈 Wykres przedstawiający średnią, min, max i odchylenie standardowe
plt.figure(figsize=(12, 6))

# Średnia wilgotność gleby
plt.plot(df_resampled["timestamp"], df_resampled["Średnia"], marker="o", linestyle="-", label="Średnia Wilgotność", color="blue")

# Zakres Min-Max
plt.fill_between(df_resampled["timestamp"], df_resampled["Min"], df_resampled["Max"], color="gray", alpha=0.3, label="Zakres (Min-Max)")

# Linie błędu pomiarowego (odchylenie standardowe)
plt.plot(df_resampled["timestamp"], df_resampled["Średnia"] + df_resampled["Odchylenie Std"], linestyle="dashed", color="red", alpha=0.7, label="Średnia + Błąd")
plt.plot(df_resampled["timestamp"], df_resampled["Średnia"] - df_resampled["Odchylenie Std"], linestyle="dashed", color="red", alpha=0.7, label="Średnia - Błąd")

# Opisy osi i tytuł
plt.xlabel("Czas")
plt.ylabel("Wilgotność Gleby")
plt.title("Analiza wilgotności gleby co 10 minut")

# Legenda i układ osi
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)

# Wyświetlenie wykresu
plt.show()
