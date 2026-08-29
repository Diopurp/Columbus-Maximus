#!/usr/bin/env python3

import serial

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import String


class HardwareInterface(Node):
    """
    Serial I/O only. Mirrors the role of articubot's diffdrive_arduino
    hardware interface: talks to the board, does nothing else.

    Subscribes:  /cmd_vel      (geometry_msgs/Twist)
    Publishes:   /raw_odom_line (std_msgs/String) - one raw "ODOM,..."
                 line per message, unparsed, for the odometry node to
                 consume.
    """

    def __init__(self):
        super().__init__('hardware_interface')

        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)

        port = self.get_parameter('port').value
        baud_rate = self.get_parameter('baud_rate').value

        # Plain open, no DTR/RTS handling - identical to the version
        # that worked before last night's reset-pulse changes.
        self.serial_port = serial.Serial(
            port,
            baud_rate,
            timeout=0.01
        )

        self.get_logger().info(
            f'Serial connection opened: {port} @ {baud_rate} baud'
        )

        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.raw_odom_pub = self.create_publisher(
            String,
            '/raw_odom_line',
            10
        )

        self.rx_timer = self.create_timer(
            0.01,
            self.read_serial
        )

    def cmd_vel_callback(self, msg):

        linear = msg.linear.x
        angular = msg.angular.z

        message = f'VEL,{linear:.3f},{angular:.3f}\n'
        data = message.encode('ascii')

        try:
            self.serial_port.write(data)
        except serial.SerialException as e:
            self.get_logger().error(
                f'Failed to send serial data: {e}'
            )

    def read_serial(self):

        try:
            while self.serial_port.in_waiting:

                line = self.serial_port.readline().decode(
                    'ascii', errors='ignore'
                ).strip()

                if not line:
                    continue

                msg = String()
                msg.data = line
                self.raw_odom_pub.publish(msg)

        except serial.SerialException as e:
            self.get_logger().error(
                f'Failed to read serial data: {e}'
            )

    def destroy_node(self):

        try:
            self.serial_port.write(b'VEL,0.000,0.000\n')
            self.serial_port.close()
        except serial.SerialException:
            pass

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)
    node = HardwareInterface()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()