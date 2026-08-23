#!/usr/bin/env python3

import math
import serial

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from geometry_msgs.msg import TransformStamped

from nav_msgs.msg import Odometry

from tf2_ros import TransformBroadcaster


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
                timeout=0.01
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

        self.odom_publisher = self.create_publisher(
            Odometry,
            '/odom',
            10
        )

        self.tf_broadcaster = TransformBroadcaster(self)

        self.rx_timer = self.create_timer(
            0.01,
            self.read_serial
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

    def read_serial(self):

        if self.serial_port is None:
            return

        try:

            while self.serial_port.in_waiting:

                line = self.serial_port.readline().decode(
                    'ascii',
                    errors='ignore'
                ).strip()

                if not line:
                    continue

                data = self.parse_odom(line)

                if data is None:
                    continue

                self.publish_odometry(data)

        except serial.SerialException as e:

            self.get_logger().error(
                f'Failed to read serial data: {e}'
            )

    def parse_odom(self, line):

        parts = line.split(',')

        if len(parts) != 6:
            return None

        if parts[0] != 'ODOM':
            return None

        try:

            x = float(parts[1])
            y = float(parts[2])
            theta = float(parts[3])
            linear_velocity = float(parts[4])
            angular_velocity = float(parts[5])

        except ValueError:

            return None

        values = [
            x,
            y,
            theta,
            linear_velocity,
            angular_velocity
        ]

        if not all(math.isfinite(value) for value in values):
            return None

        return (
            x,
            y,
            theta,
            linear_velocity,
            angular_velocity
        )

    def publish_odometry(self, data):

        (
            x,
            y,
            theta,
            linear_velocity,
            angular_velocity
        ) = data

        now = self.get_clock().now().to_msg()

        half_theta = theta / 2.0

        quaternion_z = math.sin(half_theta)
        quaternion_w = math.cos(half_theta)

        odom = Odometry()

        odom.header.stamp = now
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'

        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.position.z = 0.0

        odom.pose.pose.orientation.x = 0.0
        odom.pose.pose.orientation.y = 0.0
        odom.pose.pose.orientation.z = quaternion_z
        odom.pose.pose.orientation.w = quaternion_w

        odom.twist.twist.linear.x = linear_velocity
        odom.twist.twist.linear.y = 0.0
        odom.twist.twist.linear.z = 0.0

        odom.twist.twist.angular.x = 0.0
        odom.twist.twist.angular.y = 0.0
        odom.twist.twist.angular.z = angular_velocity

        self.odom_publisher.publish(odom)

        transform = TransformStamped()

        transform.header.stamp = now
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_link'

        transform.transform.translation.x = x
        transform.transform.translation.y = y
        transform.transform.translation.z = 0.0

        transform.transform.rotation.x = 0.0
        transform.transform.rotation.y = 0.0
        transform.transform.rotation.z = quaternion_z
        transform.transform.rotation.w = quaternion_w

        self.tf_broadcaster.sendTransform(transform)

    def destroy_node(self):

        if self.serial_port is not None:

            try:

                self.serial_port.write(
                    b'VEL,0.000,0.000\n'
                )

                self.serial_port.close()

                self.get_logger().info(
                    'Serial connection closed.'
                )

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
