import network
import ubinascii

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

mac = ubinascii.hexlify(wlan.config('mac'), ':').decode()
print("📡 MAC Pico W:", mac)
