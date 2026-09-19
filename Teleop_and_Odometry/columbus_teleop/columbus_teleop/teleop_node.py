#!/usr/bin/env python3

import threading
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

from columbus_teleop.keyboard_reader import KeyboardReader
from columbus_teleop.routines import SpecialRoutines


PUBLISH_RATE_HZ = 20.0

SPEED_SCALE_STEP = 1.10
LINEAR_STEP = 0.05
ANGULAR_STEP = 0.1

DEFAULT_LINEAR_SPEED = 0.5
DEFAULT_ANGULAR_SPEED = 1.0


HELP_TEXT = """
Movement (latched - keep moving until changed):
w : forward        s : backward
a : rotate left    d : rotate right
SPACE : stop immediately

Speed adjustment:
q : +10% both speeds     z : -10% both speeds
e : +linear speed        c : -linear speed
r : +angular speed       f : -angular speed

Special routines:
o : drive in a circle
p : drive in a square
m : dance routine

CTRL+C : stop the robot and exit safely
"""


class ColumbusTeleopNode(Node):

    def __init__(self) -> None:
        super().__init__('columbus_teleop_node')

        self._publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self._timer = self.create_timer(
            1.0 / PUBLISH_RATE_HZ,
            self._publish_velocity
        )

        self._lock = threading.Lock()

        self._linear_x = 0.0
        self._angular_z = 0.0

        self.linear_speed = DEFAULT_LINEAR_SPEED
        self.angular_speed = DEFAULT_ANGULAR_SPEED

        self._running = True
        self._keyboard_thread: Optional[threading.Thread] = None

        self._routines = SpecialRoutines(
            set_twist=self.set_twist,
            get_linear_speed=lambda: self.linear_speed,
            get_angular_speed=lambda: self.angular_speed,
            logger=self.get_logger(),
            is_active=lambda: self._running and rclpy.ok(),
        )

        self.get_logger().info(HELP_TEXT)
        self.get_logger().info(
            f'Default speeds -> linear: {self.linear_speed:.2f} m/s, '
            f'angular: {self.angular_speed:.2f} rad/s'
        )
        self.get_logger().info(
            'Initial velocity command -> linear: 0.00 m/s, angular: 0.00 rad/s'
        )

    def set_twist(self, linear_x: float, angular_z: float) -> None:
        with self._lock:
            self._linear_x = linear_x
            self._angular_z = angular_z

    def _get_twist_copy(self) -> Twist:
        msg = Twist()

        with self._lock:
            msg.linear.x = self._linear_x
            msg.angular.z = self._angular_z

        return msg

    def _publish_velocity(self) -> None:
        self._publisher.publish(self._get_twist_copy())

    def publish_zero_and_stop(self) -> None:
        self.set_twist(0.0, 0.0)
        self._publisher.publish(self._get_twist_copy())
        self.get_logger().info('Published final zero velocity. Robot stopped.')

    def start_keyboard_thread(self) -> None:
        self._keyboard_thread = threading.Thread(
            target=self._keyboard_loop,
            daemon=True
        )
        self._keyboard_thread.start()

    def stop_keyboard_thread(self) -> None:
        self._running = False

        if self._keyboard_thread is not None:
            self._keyboard_thread.join(timeout=1.0)

    def _keyboard_loop(self) -> None:
        with KeyboardReader() as keyboard:
            while self._running and rclpy.ok():
                key = keyboard.get_key(timeout=0.1)

                if key is not None:
                    self._process_key(key)

    def _process_key(self, key: str) -> None:

        if key == 'w':
            self.set_twist(self.linear_speed, 0.0)

        elif key == 's':
            self.set_twist(-self.linear_speed, 0.0)

        elif key == 'a':
            self.set_twist(0.0, self.angular_speed)

        elif key == 'd':
            self.set_twist(0.0, -self.angular_speed)

        elif key == ' ':
            self.set_twist(0.0, 0.0)
            self.get_logger().info('STOP')

        elif key == 'q':
            self.linear_speed *= SPEED_SCALE_STEP
            self.angular_speed *= SPEED_SCALE_STEP
            self._log_speeds()

        elif key == 'z':
            self.linear_speed /= SPEED_SCALE_STEP
            self.angular_speed /= SPEED_SCALE_STEP
            self._log_speeds()

        elif key == 'e':
            self.linear_speed += LINEAR_STEP
            self._log_speeds()

        elif key == 'c':
            self.linear_speed = max(
                0.0,
                self.linear_speed - LINEAR_STEP
            )
            self._log_speeds()

        elif key == 'r':
            self.angular_speed += ANGULAR_STEP
            self._log_speeds()

        elif key == 'f':
            self.angular_speed = max(
                0.0,
                self.angular_speed - ANGULAR_STEP
            )
            self._log_speeds()

        elif self._routines.run(key):
            pass

    def _log_speeds(self) -> None:
        self.get_logger().info(
            f'Speeds updated -> linear: {self.linear_speed:.3f} m/s, '
            f'angular: {self.angular_speed:.3f} rad/s'
        )


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)

    node = ColumbusTeleopNode()
    node.start_keyboard_thread()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.stop_keyboard_thread()
        node.publish_zero_and_stop()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

