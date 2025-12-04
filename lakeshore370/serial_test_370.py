"""Testing serial communication with lakeshore 370
"""

import serial
import time

# Connect to the Lake Shore 370 via serial
ser = serial.Serial(port='/dev/ttyUSB4', baudrate=9600, bytesize=8, parity='O', stopbits=1, timeout=2)

# Query current baud rate
print("Querying current baud rate...")
ser.write(b'BAUD?\n')
time.sleep(0.2)
current_baud = ser.readline().decode('ascii', errors='ignore').strip()
print(f"Current BAUD setting: {current_baud}")
print("BAUD codes: 0=300, 1=1200, 2=9600")

# Set baud rate to 9600 (code 2) - this is what we're currently using
# print("\nSetting baud rate to 9600 (code 2)...")
# ser.write(b'BAUD 2\n')
# time.sleep(0.2)
# print("Executed: BAUD 2")

# Query baud rate again to confirm
# print("\nVerifying baud rate setting...")
# ser.write(b'BAUD?\n')
# time.sleep(0.2)
# verify_baud = ser.readline().decode('ascii', errors='ignore').strip()
# print(f"Verified BAUD setting: {verify_baud}")

# Test basic communication with a simple query
print("\nTesting basic communication...")
ser.write(b'*IDN?\n')  # Standard identification query
time.sleep(0.2)
idn_response = ser.readline().decode('ascii', errors='ignore').strip()
print(f"Device identification: {idn_response}")

ser.close()
print("\nSerial connection closed.")
