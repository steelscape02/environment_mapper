import serial

#UART parameters
PORT = "COM9"
BAUD = 115200
ENCODING = "ASCII"

ser = serial.Serial(PORT, BAUD, timeout=1)

try:
  while True:
      line = ser.readline()
      if line:
          text = line.decode(ENCODING, errors='ignore').strip()
          if text:
              print(text)
except KeyboardInterrupt:
    print("Exiting serial")