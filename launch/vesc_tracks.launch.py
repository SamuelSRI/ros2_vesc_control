from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_name = "rover_vesc_control"

    default_config_file = os.path.join(
        get_package_share_directory(package_name),
        "config",
        "vesc_tracks.yaml"
    )

    config_file_arg = DeclareLaunchArgument(
        "config_file",
        default_value=default_config_file,
        description="Path to the VESC tracks YAML configuration file"
    )

    vesc_node = Node(
        package=package_name,
        executable="vesc_tracks_node",
        name="vesc_tracks_node",
        output="screen",
        parameters=[
            LaunchConfiguration("config_file")
        ]
    )

    return LaunchDescription([
        config_file_arg,
        vesc_node,
    ])