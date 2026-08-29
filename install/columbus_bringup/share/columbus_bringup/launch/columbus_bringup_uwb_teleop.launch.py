from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    uwb_config_path = os.path.join(
        get_package_share_directory('uwb_tracker'),
        'config',
        'uwb_params.yaml'
    )
    ekf_config_path = os.path.join(
        get_package_share_directory('columbus_bringup'),
        'config',
        'ekf.yaml'
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
        parameters=[uwb_config_path],
        env={
            'ROS_DOMAIN_ID': '42',
            'ROS_LOCALHOST_ONLY': '0',
            'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp',
        }
    )

    hardware_interface = Node(
        package='columbus_serial_bridge',
        executable='hardware_interface_node',
        name='hardware_interface',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('serial_port'),
            'baud_rate': 115200
        }]
    )

    odometry = Node(
        package='columbus_serial_bridge',
        executable='odometry_node',
        name='odometry_publisher',
        output='screen'
    )

    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_path]
    )

    return LaunchDescription([
        port_arg,
        teleop,
        uwb,
        hardware_interface,
        odometry,
        ekf
    ])
