import RPi.GPIO as GPIO
import time

# Connect switch to 3.3v and GPIO pin 4
# Put a 1k ohm resistor in series from 3.3v to switch
PIN = 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    while True:
        if GPIO.input(PIN) == GPIO.HIGH:
            print("Switch pressed")
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Interrupted")

GPIO.cleanup(PIN)
