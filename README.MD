# Przed uruchomieniem:
Uruchom na pico skrypt
```bash
checkMAC.py
```

Następnie utwórz plik config.json:
usuń komentarze po skopiowaniu z pliku json
```bash
{
    "devices": {
        "11:22:33:44:55:66": { # wpisz swój adres MAC który wypisał ci skrypt checkMAC.py na pico
            "pins": {
                "26": "analog",
                "1": "digital" # tutaj możesz dodać inne piny
            },
            "interval": 5 # co ile sekund chcesz otrzymywac informacje z pico (czujników)
        }
    }
}
```


