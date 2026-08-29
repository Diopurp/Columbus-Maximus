#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped

from tf2_ros import TransformBroadcaster


class OdometryPublisher(Node):
    """
    Turns raw "ODOM,x,y,theta,linear_vel,angular_vel" lines from the
    hardware interface into nav_msgs/Odometry + the odom->base_link TF.
    Mirrors the role articubot's odometry/robot_localization layer
    plays on top of the raw hardware interface.

    Subscribes:  /raw_odom_line (std_msgs/String)
    Publishes:   /odom          (nav_msgs/Odometry)
                 odom -> base_link transform
    """

    def __init__(self):
        super().__init__('odometry_publisher')

        self.raw_odom_sub = self.create_subscription(
            String,
            '/raw_odom_line',
            self.raw_odom_callback,
            10
        )

        self.odom_publisher = self.create_publisher(
            Odometry,
            '/odom',
            10
        )

        self.tf_broadcaster = TransformBroadcaster(self)

    def raw_odom_callback(self, msg):

        data = self.parse_odom(msg.data)

        if data is None:
            return

        self.publish_odometry(data)

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

        values = [x, y, theta, linear_velocity, angular_velocity]

        if not all(math.isfinite(value) for value in values):
            return None

        return (x, y, theta, linear_velocity, angular_velocity)

    def publish_odometry(self, data):

        (x, y, theta, linear_velocity, angular_velocity) = data

        now_msg = self.get_clock().now().to_msg()

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

        odom.pose.covariance[0] = 0.05    # x
        odom.pose.covariance[7] = 0.05    # y
        odom.pose.covariance[35] = 0.1    # yaw
        odom.twist.covariance[0] = 0.02   # vx
        odom.twist.covariance[35] = 0.05  # vyaw - looser given left-motor stiffness bias

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


def main(args=None):

    rclpy.init(args=args)
    node = OdometryPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()