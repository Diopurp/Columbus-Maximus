import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    serial_port = LaunchConfiguration('serial_port')

    declare_serial_port = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for the ESP32 motor controller'
    )

    rsp_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('columbusmaximus'),
                'launch',
                'rsp.launch.py'
            ])
        )
    )

    serial_bridge_node = Node(
        package='columbus_serial_bridge',
        executable='serial_bridge',
        name='serial_bridge',
        output='screen',
        parameters=[{'port': serial_port, 'baud_rate': 115200}]
    )

    ld08_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ld08_driver'),
                'launch',
                'ld08.launch.py'
            ])
        ),
        launch_arguments={'frame_id': 'laser_frame'}.items()
        # ld08_driver has no port argument — main.cpp auto-detects the
        # LiDAR by scanning USB tty devices for a CP2102 product string.
        # frame_id set to 'laser_frame' to match lidar.xacro's link name.
    )

    return LaunchDescription([
        declare_serial_port,
        rsp_launch,
        serial_bridge_node,
        ld08_launch,
    ])
