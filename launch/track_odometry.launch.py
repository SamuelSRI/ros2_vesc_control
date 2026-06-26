from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_dir = get_package_share_directory("ros2_vesc_control")

    default_config = os.path.join(
        package_dir,
        "config",
        "track_odometry.yaml",
    )

    config_file_arg = DeclareLaunchArgument(
        "config_file",
        default_value=default_config,
        description="Path to the track odometry configuration file",
    )

    odom_node = Node(
        package="ros2_vesc_control",
        executable="track_odometry_node",
        name="track_odometry_node",
        output="screen",
        parameters=[LaunchConfiguration("config_file")],
    )

    return LaunchDescription([
        config_file_arg,
        odom_node,
    ])
