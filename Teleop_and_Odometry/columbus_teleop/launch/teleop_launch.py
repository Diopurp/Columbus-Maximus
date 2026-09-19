"""Launch file for columbus_teleop.

Launches the teleop node with output routed to the screen so keyboard
help text and speed/status messages are visible in the terminal that
started the launch.

Note: because this node reads raw keyboard input, it must be run in a
terminal with an interactive stdin (a normal `ros2 launch` invocation
works fine; running it under a process manager without a TTY will not).
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    teleop_node = Node(
        package='columbus_teleop',
        executable='teleop_node',
        name='columbus_teleop_node',
        output='screen',
        emulate_tty=True,
    )

    return LaunchDescription([teleop_node])
