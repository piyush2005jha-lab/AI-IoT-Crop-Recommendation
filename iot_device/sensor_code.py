import serial
import time

#------------------- Serial Setup --------------------
# Change 'COM3' to your Arduino port
ser = serial.Serial('COM7', 9600, timeout=1)
time.sleep(2)  # wait for Arduino to initialize

def parse_line(line):
    """Extract value after colon and strip whitespace."""
    try:
        return line.split(":")[1].strip()
    except IndexError:
        return None

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line.startswith("DHT11 - Temperature"):
            temp = parse_line(line)
        elif line.startswith("DHT11 - Humidity"):
            humidity = parse_line(line)
        elif line.startswith("Soil Moisture"):
            soil = parse_line(line)
        elif line.startswith("LDR (Analog)"):
            ldr = parse_line(line)
        elif line.startswith("MPL3115A2 - Pressure"):
            pressure = parse_line(line)
        elif line.startswith("MPL3115A2 - Altitude"):
            altitude = parse_line(line)
            # After altitude, print all values
            print(f"Temperature: {temp} °C | Humidity: {humidity} % | Soil Moisture: {soil} | "
                  f"LDR: {ldr} | Pressure: {pressure} hPa | Altitude: {altitude} m")
    except KeyboardInterrupt:
        print("Exiting...")
        break
    except:
        continue