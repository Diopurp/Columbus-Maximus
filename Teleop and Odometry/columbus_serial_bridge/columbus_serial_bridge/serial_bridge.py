#!/usr/bin/env python3

import math
import time
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

        self.serial_port = None
        self.last_odom_time = self.get_clock().now()

        self.open_serial()

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

        # Watchdog: warns if no odom has been received in a while,
        # separate from serial-level errors, so silent stalls (e.g.
        # ESP32 mid-reboot) are visible in the logs.
        self.watchdog_timer = self.create_timer(
            1.0,
            self.check_staleness
        )

    def open_serial(self):
        """Open (or reopen) the serial connection to the ESP32."""

        port = self.get_parameter('port').value
        baud_rate = self.get_parameter('baud_rate').value

        try:
            # Build the Serial object WITHOUT opening it yet. Opening
            # via serial.Serial(port, baud, ...) directly asserts
            # pyserial's default DTR/RTS (both True) the instant the
            # port opens - before we ever get a chance to change them.
            # That default assertion is itself what resets/holds the
            # ESP32, so setting DTR/RTS after opening is too late.
            # Constructing unopened, setting the lines first, then
            # calling open() avoids ever asserting the default state.
            self.serial_port = serial.Serial()
            self.serial_port.port = port
            self.serial_port.baudrate = baud_rate
            self.serial_port.timeout = 0.01
            self.serial_port.dtr = False
            self.serial_port.rts = False
            self.serial_port.open()

            # Give the ESP32 a moment to finish booting cleanly before
            # we start expecting data from it.
            time.sleep(0.3)

            self.get_logger().info(
                f'Serial connection opened: {port} @ {baud_rate} baud'
            )

        except serial.SerialException as e:
            self.serial_port = None

            self.get_logger().error(
                f'Failed to open serial port {port}: {e}'
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

        # If the connection isn't open (either it never opened, or a
        # previous read/write error closed it), try to reopen it every
        # tick instead of silently doing nothing forever.
        if self.serial_port is None:
            self.open_serial()
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
                f'Serial read failed, will attempt to reconnect: {e}'
            )

            try:
                self.serial_port.close()
            except serial.SerialException:
                pass

            self.serial_port = None

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

        now = self.get_clock().now()
        self.last_odom_time = now
        now_msg = now.to_msg()

        half_theta = theta / 2.0

        quaternion_z = math.sin(half_theta)
        quaternion_w = math.cos(half_theta)

        odom = Odometry()

        odom.header.stamp = now_msg
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

        transform.header.stamp = now_msg
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

    def check_staleness(self):
        """Log a warning if no odom data has come in for a while.

        This catches the case where the serial connection is still
        technically open, but the ESP32 itself has gone quiet (e.g.
        mid-reboot after a brownout) - something the read_serial()
        exception handler alone can't detect.
        """

        elapsed = (
            self.get_clock().now() - self.last_odom_time
        ).nanoseconds / 1e9

        if elapsed > 2.0:
            self.get_logger().warn(
                f'No odom received for {elapsed:.1f}s'
            )

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