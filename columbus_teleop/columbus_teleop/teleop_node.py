
#!/usr/bin/env python3
"""Custom keyboard teleoperation node for the Columbus Maximus robot.

Publishes geometry_msgs/msg/Twist messages on /cmd_vel.
Keyboard input is handled by a background thread.
"""

import threading
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

from columbus_teleop.keyboard_reader import KeyboardReader
from columbus_teleop.routines import SpecialRoutines

# /cmd_vel publishing frequency.
PUBLISH_RATE_HZ = 20.0

# Speed adjustment settings.
SPEED_SCALE_STEP = 1.10
LINEAR_STEP = 0.05
ANGULAR_STEP = 0.1

# Initial linear and angular speeds.
INITIAL_LINEAR_SPEED = 0.5
INITIAL_ANGULAR_SPEED = 1.0

HELP_TEXT = """
Columbus Maximus Teleop
------------------------
Movement (latched - keep moving until changed):
  w : forward        s : backward
  a : rotate left     d : rotate right
  SPACE : stop immediately

Speed adjustment:
  q : +10% both speeds     z : -10% both speeds
  e : +linear speed        c : -linear speed
  r : +angular speed       f : -angular speed

Special routines (return to manual control when finished):
  o : drive in a circle
  p : drive in a square
  m : dance routine

CTRL+C : stop the robot and exit safely
------------------------
"""


class ColumbusTeleopNode(Node):
    """ROS2 node that converts keyboard input into /cmd_vel commands."""

    def __init__(self) -> None:
        super().__init__('columbus_teleop_node')

        # Create the /cmd_vel publisher and its 20 Hz timer.
        self._publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self._timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._publish_velocity)

        # Store the current velocity command and speed settings.
        self._lock = threading.Lock()
        self._linear_x = 0.0
        self._angular_z = 0.0
        self.linear_speed = INITIAL_LINEAR_SPEED
        self.angular_speed = INITIAL_ANGULAR_SPEED

        # Connect the predefined motion routines to this node.
        self._routines = SpecialRoutines(
            set_twist=self.set_twist,
            get_linear_speed=lambda: self.linear_speed,
            get_angular_speed=lambda: self.angular_speed,
            logger=self.get_logger(),
            is_active=lambda: self._running and rclpy.ok(),
        )

        # Keyboard input runs in a separate thread.
        self._running = True
        self._keyboard_thread: Optional[threading.Thread] = None

        self.get_logger().info(HELP_TEXT)
        self.get_logger().info(
            f'Initial speeds -> linear: {self.linear_speed:.2f} m/s, '
            f'angular: {self.angular_speed:.2f} rad/s'
        )

    def set_twist(self, linear_x: float, angular_z: float) -> None:
        """Update the current velocity command."""
        with self._lock:
            self._linear_x = linear_x
            self._angular_z = angular_z

    def _get_twist_copy(self) -> Twist:
        """Create a Twist message using the current velocity command."""
        msg = Twist()
        with self._lock:
            msg.linear.x = self._linear_x
            msg.angular.z = self._angular_z
        return msg

    # Timer callback that publishes the current velocity command.
    def _publish_velocity(self) -> None:
        self._publisher.publish(self._get_twist_copy())

    def publish_zero_and_stop(self) -> None:
        """Publish a zero velocity command before shutting down."""
        self.set_twist(0.0, 0.0)
        self._publisher.publish(self._get_twist_copy())
        self.get_logger().info('Published final zero velocity. Robot stopped.')

    def start_keyboard_thread(self) -> None:
        """Start the thread responsible for reading keyboard input."""
        self._keyboard_thread = threading.Thread(
            target=self._keyboard_loop, daemon=True
        )
        self._keyboard_thread.start()

    def stop_keyboard_thread(self) -> None:
        """Stop the keyboard input thread."""
        self._running = False
        if self._keyboard_thread is not None:
            self._keyboard_thread.join(timeout=1.0)

    def _keyboard_loop(self) -> None:
        """Read keyboard input and process each key."""
        with KeyboardReader() as keyboard:
            while self._running and rclpy.ok():
                key = keyboard.get_key(timeout=0.1)
                if key is None:
                    continue
                self._process_key(key)

    def _process_key(self, key: str) -> None:
        # Movement keys set the current velocity until another command is given.
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

        # Increase or decrease both linear and angular speeds by 10%.
        elif key == 'q':
            self.linear_speed *= SPEED_SCALE_STEP
            self.angular_speed *= SPEED_SCALE_STEP
            self._log_speeds()
        elif key == 'z':
            self.linear_speed /= SPEED_SCALE_STEP
            self.angular_speed /= SPEED_SCALE_STEP
            self._log_speeds()

        # Increase or decrease only the linear speed.
        elif key == 'e':
            self.linear_speed += LINEAR_STEP
            self._log_speeds()
        elif key == 'c':
            self.linear_speed = max(0.0, self.linear_speed - LINEAR_STEP)
            self._log_speeds()

        # Increase or decrease only the angular speed.
        elif key == 'r':
            self.angular_speed += ANGULAR_STEP
            self._log_speeds()
        elif key == 'f':
            self.angular_speed = max(0.0, self.angular_speed - ANGULAR_STEP)
            self._log_speeds()

        # Run a predefined circle, square, or dance routine.
        elif self._routines.run(key):
            pass

        else:
            # Ignore keys that are not assigned to a command.
            pass

    def _log_speeds(self) -> None:
        """Display the current linear and angular speed settings."""
        self.get_logger().info(
            f'Speeds updated -> linear: {self.linear_speed:.3f} m/s, '
            f'angular: {self.angular_speed:.3f} rad/s'
        )


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = ColumbusTeleopNode()
    node.start_keyboard_thread()

    try:
        # Spin the node so its timer callback continues running.
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
