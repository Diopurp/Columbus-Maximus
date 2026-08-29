import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    default_params = os.path.join(
        get_package_share_directory('columbusmaximus'),
        'config',
        'mapper_params_online_async.yaml'
    )

    slam_params_file = LaunchConfiguration('slam_params_file')

    declare_params = DeclareLaunchArgument(
        'slam_params_file',
        default_value=default_params,
        description='Full path to the SLAM Toolbox mapper params yaml'
    )

    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params_file, {'use_sim_time': False}]
    )

    return LaunchDescription([
        declare_params,
        slam_toolbox_node,
    ])
