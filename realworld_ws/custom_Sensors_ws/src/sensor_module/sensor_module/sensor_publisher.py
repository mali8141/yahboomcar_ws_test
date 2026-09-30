#!/usr/bin/env python3
import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

try:
    import serial
except ImportError:
    serial = None


DEFAULT_DATA = {'temp_c': 0.0, 'humidity': 0.0, 'pressure_pa': 0.0}


def _parse_response(line: str):
    # Expects lines like: >key:val,key:val,...
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


class SensorPublisher(Node):
    def __init__(self):
        super().__init__('sensor_publisher')

        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud', 9600)
        self.declare_parameter('topic', '/sensor_module/data')
        self.declare_parameter('rate_hz', 10.0)

        port = self.get_parameter('port').get_parameter_value().string_value
        baud = self.get_parameter('baud').get_parameter_value().integer_value
        topic = self.get_parameter('topic').get_parameter_value().string_value
        rate_hz = self.get_parameter('rate_hz').get_parameter_value().double_value

        self.pub = self.create_publisher(String, topic, 10)

        self.ser = None
        if serial is None:
            self.get_logger().warning('pyserial not installed; publishing default values')
        else:
            try:
                self.ser = serial.Serial(port, baud, timeout=1)
                time.sleep(0.1)
                self.get_logger().info(f'Connected to {port} at {baud} baud')
            except Exception as e:
                self.get_logger().warning(f'Cannot open {port}: {e}; publishing default values')

        self.create_timer(1.0 / rate_hz, self._tick)

    def _publish(self, data: dict):
        msg = String()
        msg.data = json.dumps(data)
        self.pub.publish(msg)

    def _tick(self):
        if self.ser is None:
            self._publish(DEFAULT_DATA)
            return
        try:
            self.ser.write(b'read\n')
            deadline = time.time() + 0.8
            while time.time() < deadline:
                raw = self.ser.readline()
                if not raw:
                    continue
                line = raw.decode('utf-8', errors='ignore').strip()
                if line.startswith('>'):
                    data = _parse_response(line)
                    if data:
                        self._publish(data)
                    else:
                        self.get_logger().warning(f'Unparseable line: {line}')
                        self._publish(DEFAULT_DATA)
                    return
            self.get_logger().warning('No response from sensor within timeout')
            self._publish(DEFAULT_DATA)
        except Exception as e:
            self.get_logger().error(f'Serial error: {e}')
            self._publish(DEFAULT_DATA)


def main(args=None):
    rclpy.init(args=args)
    node = SensorPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
