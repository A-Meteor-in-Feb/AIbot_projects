import serial 
import time
import re

qr_value = serial.Serial("/dev/ttyACM0", baudrate=115200, timeout=10)
qr_value.reset_input_buffer()
TARGET = "8888002225100"

while True:
    raw = qr_value.read_until(b"\x1b[B")
    print("raw:", raw)
    
    if raw.endswith(b"\x1b[B"):
        raw = raw[:-3]

    text = raw.decode()
    digits = re.sub(r"\D+", "", text)
    print("TEXT:", repr(text), "DIGITS:", digits)

    if TARGET in digits:
        print(True)
