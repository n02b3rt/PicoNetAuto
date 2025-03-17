# Struktura branchy w repozytorium

## Branch: `main`
Zawiera **uniwersalną wersję serwera**, która:
- Wczytuje konfigurację urządzeń z `config.json`
- Odbiera dane z urządzeń i zapisuje je do plików w folderze `data/`
- Umożliwia pobieranie konfiguracji urządzeń
- Zawiera system logowania błędów

## Branch: `moisture-sensors`
Zawiera **wersję serwera z obsługą czujników wilgotności**, która:
- Zawiera całą logikę odbierania i przetwarzania danych z czujników wilgotności gleby
- Automatycznie generuje podsumowania wilgotności na podstawie zapisanych danych
- Umożliwia pobieranie podsumowań za pomocą dedykowanych endpointów API

---

# Instrukcja uruchomienia serwera czujników Pico W

## Przed uruchomieniem:

### 1️. Sprawdzenie adresu MAC urządzenia Pico W
Najpierw uruchom na swoim Pico skrypt:
```bash
checkMAC.py
```

### 2️. Utworzenie pliku `config.json`
Usuń komentarze po skopiowaniu z pliku JSON:
```json
{
    "devices": {
        "11:22:33:44:55:66": {  
            "pins": {
                "26": "analog",
                "1": "digital"
            },
            "interval": 5
        }
    }
}
```
- **Wpisz swój adres MAC**, który wypisał skrypt `checkMAC.py` na Pico.  
- **Dostosuj piny i interwał**, jeśli chcesz.

---

## Instalacja i uruchomienie serwera

### 1️. **Stworzenie i aktywowanie wirtualnego środowiska**
W katalogu projektu uruchom:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate    # Windows
```

### 2️. **Instalacja zależności**
Upewnij się, że masz zainstalowane wymagane pakiety:
```bash
pip install -r requirements.txt
```

### 3. **Uruchomienie serwera**
```bash
python server.py
```
Serwer powinien być teraz dostępny pod adresem:
```
http://127.0.0.1:5000
http://192.168.X.X:5000  # Adres lokalny
```

---

## Dostępne API

###  **Pobranie konfiguracji urządzenia**
```bash
GET /device_config/<mac_address>
```

###  **Odbiór danych z Pico**
```bash
POST /data
```

### **Pobranie pełnego podsumowania** - (dostępne tylko w `moisture-sensors`)
```bash
GET /summary_data
```

### **Pobranie ostatniego wpisu z podsumowania**- (dostępne tylko w `moisture-sensors`)
```bash
GET /latest_summary
```

---

