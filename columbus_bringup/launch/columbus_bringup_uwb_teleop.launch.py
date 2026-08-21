from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    config_path = os.path.join(
        get_package_share_directory('uwb_tracker'),
        'config',
        'uwb_params.yaml'
    )
    port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='USB port the ESP32 is connected to'
    )
    teleop = ExecuteProcess(
        cmd=['gnome-terminal', '--title=Teleop', '--', 'bash', '-c',
             'history -s "ros2 run columbus_teleop teleop_node"; ros2 run columbus_teleop teleop_node; exec bash'],
        output='screen'
    )
    uwb = Node(
        package='uwb_tracker',
        executable='uwb_node_rviz',
        name='uwb_trilateration_node',
        output='screen',
        parameters=[config_path],
        env={
            'ROS_DOMAIN_ID': '42',
            'ROS_LOCALHOST_ONLY': '0',
            'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp',
        }
    )
    serial_bridge = Node(
        package='columbus_serial_bridge',
        executable='serial_bridge',
        name='serial_bridge',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('serial_port'),
            'baud_rate': 115200
        }]
    )
    return LaunchDescription([
        port_arg,
        teleop,
        uwb,
        serial_bridge
    ])
