"""Sensor parsing and read helper for SensorModule MCU.

This file contains the parsing logic so ROS wrappers can be thin.
"""
import time

try:
    import serial
except ImportError:
    serial = None


DEFAULT_DATA = {'temp_c': 0.0, 'humidity': 0.0, 'pressure_pa': 0.0}


def parse_response(line: str):
    if not line.startswith('>'):
        return None
    out = {}
    for part in line[1:].strip().split(','):
        if ':' not in part:
            continue
        k, v = part.split(':', 1)
        try:
            out[k] = float(v)
        except ValueError:
            out[k] = v
    return out or None


class SensorReader:
    def __init__(self, port='/dev/ttyUSB0', baud=9600):
        self.port = port
        self.baud = baud
        self.ser = None
        if serial is not None:
            try:
                self.ser = serial.Serial(self.port, self.baud, timeout=1)
                time.sleep(0.1)
            except Exception:
                self.ser = None

    def read(self):
        if self.ser is None:
            return DEFAULT_DATA
        try:
            self.ser.write(b'read\n')
            deadline = time.time() + 0.8
            while time.time() < deadline:
                raw = self.ser.readline()
                if not raw:
                    continue
                line = raw.decode('utf-8', errors='ignore').strip()
                if line.startswith('>'):
                    data = parse_response(line)
                    if data:
                        return data
            return DEFAULT_DATA
        except Exception:
            return DEFAULT_DATA
