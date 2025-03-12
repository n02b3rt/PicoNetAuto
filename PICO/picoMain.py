import network
import urequests
import machine
import time
import ubinascii

# KONFIGURACJA WiFi (ZAPISANA NA STAŁE)
SSID = "{SSID}" #WPISZ
PASSWORD = "{HASŁO}" #WPISZ

SERVER_IP = "{Adres Serwera}"  #WPISZ
DEVICE_CONFIG_URL = f"http://{SERVER_IP}:5000/device_config/"
DATA_URL = f"http://{SERVER_IP}:5000/data"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
mac = ubinascii.hexlify(wlan.config('mac'), ':').decode()

monitored_pins = {}  # Słownik: { "pin": "analog" / "digital" }
interval = 5
last_config = None


def connect_to_wifi():
    """ Łączy Pico W do WiFi """
    print(f"Łączę się z {SSID}...")
    wlan.connect(SSID, PASSWORD)

    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print(f"Połączono z {SSID}!", wlan.ifconfig())
    else:
        print(f"Nie udało się połączyć z {SSID}")


def get_device_config():
    """ Pobiera konfigurację dla danego urządzenia z serwera """
    global monitored_pins, interval, last_config
    try:
        print("Pobieram konfigurację urządzenia...")
        response = urequests.get(DEVICE_CONFIG_URL + mac)
        config = response.json()

        if "error" in config:
            print("Serwer nie zna tego urządzenia.")
            return False

        # Sprawdzenie, czy konfiguracja się zmieniła
        if config != last_config:
            print("Nowa konfiguracja wykryta! Aktualizacja...")
            monitored_pins = config["pins"]
            interval = config["interval"]
            last_config = config
            print(f"Nowe ustawienia: Piny {monitored_pins}, Interwał {interval}s")
            return True

        return False

    except Exception as e:
        print("Błąd pobierania konfiguracji:", e)
        return False


def read_gpio():
    """ Odczytuje stan GPIO i ADC """
    gpio_states = {}

    for pin, pin_type in monitored_pins.items():
        pin = int(pin)  # JSON przechowuje piny jako stringi, konwertujemy na int

        if pin_type == "digital":
            gpio_states[f"pin_{pin}"] = machine.Pin(pin, machine.Pin.IN).value()
        elif pin_type == "analog":
            gpio_states[f"pin_{pin}"] = machine.ADC(pin).read_u16()

    return gpio_states


def send_data():
    """ Wysyła dane GPIO do serwera """
    data = {
        "device": mac,
        "gpio": read_gpio()
    }

    try:
        response = urequests.post(DATA_URL, json=data)
        print("📡 Wysłano dane:", response.text)
    except Exception as e:
        print("Błąd podczas wysyłania:", e)


connect_to_wifi()

get_device_config()

# wysyłanie danych i sprawdzanie zmian co 60s**
last_check = time.time()

while True:
    if wlan.isconnected():
        send_data()

        # Sprawdzamy nowe ustawienia co 60 sekund
        if time.time() - last_check >= 60:
            if get_device_config():
                print("Konfiguracja zaktualizowana, stosuję nowe ustawienia!")
            last_check = time.time()

    else:
        print("Brak połączenia z WiFi, próbuję ponownie...")
        connect_to_wifi()

    time.sleep(interval)
