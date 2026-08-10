#!/usr/bin/env python3

import serial

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class SerialBridge(Node):

    def __init__(self):
        super().__init__('serial_bridge')

        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)

        port = self.get_parameter('port').value
        baud_rate = self.get_parameter('baud_rate').value

        try:
            self.serial_port = serial.Serial(
                port,
                baud_rate,
                timeout=0.1
            )
            self.get_logger().info(
                f'Serial connection opened: {port} @ {baud_rate} baud'
            )
        except serial.SerialException as e:
            self.serial_port = None
            self.get_logger().error(
                f'Failed to open serial port {port}: {e}'
            )

        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

    def cmd_vel_callback(self, msg):
        linear = msg.linear.x
        angular = msg.angular.z

        self.get_logger().info(
            f'Received: linear={linear:.2f}, angular={angular:.2f}'
        )

        message = f'VEL,{linear:.3f},{angular:.3f}\n'
        data = message.encode('ascii')

        if self.serial_port is not None:
            try:
                self.serial_port.write(data)
            except serial.SerialException as e:
                self.get_logger().error(
                    f'Failed to send serial data: {e}'
                )

    def destroy_node(self):
        if self.serial_port is not None:
            try:
                self.serial_port.write(b'VEL,0.000,0.000\n')
                self.serial_port.close()
                self.get_logger().info('Serial connection closed.')
            except serial.SerialException:
                pass

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = SerialBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
