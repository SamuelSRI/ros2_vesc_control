# ros2_vesc_control

ROS 2 package for controlling two VESC-based motor controllers over UART and publishing differential-drive odometry for tracked rover platforms.

This package is designed for differential drive or tracked rover robots using one VESC per side.
It sends eRPM commands to the motor controllers, reads feedback values directly through the VESC UART protocol, and can generate ROS 2 odometry from the measured left and right track speeds.

## Features

* Control two VESC motor controllers over UART
* Designed for differential drive or tracked rover robots
* Subscribe to target track speeds in m/s
* Convert linear track speed commands to VESC eRPM
* Send eRPM commands to left and right VESCs
* Read VESC feedback using `COMM_GET_VALUES`
* Publish measured eRPM, estimated speed, voltage, current, duty cycle, temperatures and fault code
* Publish measured left and right track speed feedback
* Optional odometry node using differential-drive kinematics
* Publish `/odom` as `nav_msgs/msg/Odometry`
* Publish TF transform `odom -> base_link`
* Configurable through ROS 2 parameters and YAML files
* Automatic reconnection if VESC serial ports are not available at startup
* Includes non-ROS test scripts for direct UART testing

## Package structure

```text
ros2_vesc_control
├── config
│   ├── vesc_tracks.yaml
│   └── track_odometry.yaml
├── launch
│   ├── vesc_tracks.launch.py
│   └── track_odometry.launch.py
├── ros2_vesc_control
│   ├── __init__.py
│   ├── track_odometry_node.py
│   ├── vesc_protocol.py
│   ├── vesc_tracks_node.py
│   └── vesc_uart.py
├── tools
│   ├── test_read_vesc.py
│   └── test_set_rpm.py
├── package.xml
├── setup.py
├── setup.cfg
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Requirements

* ROS 2
* Python 3
* `pyserial`
* Two VESC-compatible ESCs with UART enabled

Required ROS 2 dependencies:

* `rclpy`
* `std_msgs`
* `nav_msgs`
* `geometry_msgs`
* `tf2_ros`

Tested with ROS 2 Python nodes.
The package should work on recent ROS 2 distributions as long as `rclpy` and `ament_python` are available.

## Installation

Clone the repository into your ROS 2 workspace:

```bash
cd ~/ros2_ws/src
git clone git@github.com:SamuelSRI/ros2_vesc_control.git
```

Install Python dependencies:

```bash
cd ~/ros2_ws
pip install -r src/ros2_vesc_control/requirements.txt
```

If you use `uv`:

```bash
cd ~/ros2_ws
uv venv --system-site-packages .venv
source .venv/bin/activate
uv pip install -r src/ros2_vesc_control/requirements.txt
```

Source your ROS 2 installation:

```bash
source /opt/ros/<your_ros_distro>/setup.bash
```

Example:

```bash
source /opt/ros/jazzy/setup.bash
```

Build the package:

```bash
cd ~/ros2_ws
colcon build --packages-select ros2_vesc_control
source install/setup.bash
```

## Configuration

The motor controller configuration file is:

```text
config/vesc_tracks.yaml
```

The odometry configuration file is:

```text
config/track_odometry.yaml
```

### Motor controller configuration

Example `vesc_tracks.yaml`:

```yaml
vesc_tracks_node:
  ros__parameters:
    left_port: "/dev/ttyACM0"
    right_port: "/dev/ttyACM1"
    baudrate: 115200

    wheel_diameter: 0.165
    gear_ratio: 20.0
    motor_poles: 14.0
    max_erpm: 35000

    left_sign: 1.0
    right_sign: 1.0

    command_topic: "/vesc/track_speed_cmd"
    left_state_topic: "/vesc/left/state"
    right_state_topic: "/vesc/right/state"
    feedback_topic: "/vesc/track_speed_feedback"

    control_rate_hz: 20.0
    read_rate_hz: 10.0
    cmd_timeout: 0.5

    print_debug: false
```

### Odometry configuration

Example `track_odometry.yaml`:

```yaml
track_odometry_node:
  ros__parameters:
    feedback_topic: "/vesc/track_speed_feedback"
    odom_topic: "/odom"

    odom_frame: "odom"
    base_frame: "base_link"

    track_width: 0.50

    publish_tf: true
    print_debug: false
```

### Important motor parameters

| Parameter         | Description                                     |
| ----------------- | ----------------------------------------------- |
| `left_port`       | Serial port of the left VESC                    |
| `right_port`      | Serial port of the right VESC                   |
| `baudrate`        | UART baudrate                                   |
| `wheel_diameter`  | Wheel or sprocket diameter in meters            |
| `gear_ratio`      | Gear reduction ratio between motor and wheel    |
| `motor_poles`     | Number of motor poles                           |
| `max_erpm`        | Maximum allowed eRPM command                    |
| `left_sign`       | Direction multiplier for the left side          |
| `right_sign`      | Direction multiplier for the right side         |
| `cmd_timeout`     | Time without command before stopping the motors |
| `control_rate_hz` | Motor command update rate                       |
| `read_rate_hz`    | VESC feedback reading rate                      |

### Important odometry parameters

| Parameter        | Description                                                        |
| ---------------- | ------------------------------------------------------------------ |
| `feedback_topic` | Topic containing measured left and right track speeds              |
| `odom_topic`     | Output odometry topic                                              |
| `odom_frame`     | Parent odometry frame, usually `odom`                              |
| `base_frame`     | Robot base frame, usually `base_link`                              |
| `track_width`    | Distance in meters between the center of the left and right tracks |
| `publish_tf`     | Publish the TF transform `odom -> base_link`                       |
| `print_debug`    | Print odometry debug values                                        |

## Serial ports

Before running the motor node, check which serial ports are assigned to your VESCs:

```bash
ls /dev/ttyACM*
ls /dev/ttyUSB*
```

You can also use:

```bash
dmesg | grep tty
```

If the ports are different from the default values, update `config/vesc_tracks.yaml`.

Example:

```yaml
left_port: "/dev/ttyUSB0"
right_port: "/dev/ttyUSB1"
```

If you do not have permission to access the serial ports, add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and log back in.

## Running the motor node

Launch with the default configuration:

```bash
ros2 launch ros2_vesc_control vesc_tracks.launch.py
```

Launch with a custom configuration file:

```bash
ros2 launch ros2_vesc_control vesc_tracks.launch.py config_file:=/path/to/my_config.yaml
```

## Running the odometry node

The odometry node subscribes to `/vesc/track_speed_feedback` and publishes `/odom` and the TF transform `odom -> base_link`.

Launch with the default configuration:

```bash
ros2 launch ros2_vesc_control track_odometry.launch.py
```

Launch with a custom configuration file:

```bash
ros2 launch ros2_vesc_control track_odometry.launch.py config_file:=/path/to/my_odom_config.yaml
```

You can also run it directly:

```bash
ros2 run ros2_vesc_control track_odometry_node --ros-args -p track_width:=0.50
```

Replace `0.50` with the real distance between the left and right tracks.

## Running the full system

Terminal 1:

```bash
ros2 launch ros2_vesc_control vesc_tracks.launch.py
```

Terminal 2:

```bash
ros2 launch ros2_vesc_control track_odometry.launch.py
```

After both nodes are running, check the topics:

```bash
ros2 topic list
```

Expected main topics:

```text
/vesc/track_speed_cmd
/vesc/left/state
/vesc/right/state
/vesc/track_speed_feedback
/odom
/tf
```

## Subscribed topics

### `/vesc/track_speed_cmd`

Type:

```text
std_msgs/msg/Float32MultiArray
```

Format:

```text
data[0] = left track speed in m/s
data[1] = right track speed in m/s
```

Example command:

```bash
ros2 topic pub /vesc/track_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.1, 0.1]}"
```

Stop command:

```bash
ros2 topic pub /vesc/track_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0]}"
```

### `/vesc/track_speed_feedback`

Used by `track_odometry_node`.

Type:

```text
std_msgs/msg/Float32MultiArray
```

Format:

```text
data[0] = measured left track speed in m/s
data[1] = measured right track speed in m/s
```

## Published topics

### `/vesc/left/state`

Type:

```text
std_msgs/msg/Float32MultiArray
```

Format:

```text
data[0]  = measured eRPM
data[1]  = measured speed in m/s
data[2]  = duty cycle
data[3]  = motor current in A
data[4]  = input current in A
data[5]  = input voltage in V
data[6]  = MOSFET temperature in °C
data[7]  = motor temperature in °C
data[8]  = tachometer
data[9]  = tachometer absolute
data[10] = fault code
```

### `/vesc/right/state`

Same format as `/vesc/left/state`.

### `/vesc/track_speed_feedback`

Type:

```text
std_msgs/msg/Float32MultiArray
```

Format:

```text
data[0] = measured left speed in m/s
data[1] = measured right speed in m/s
```

### `/odom`

Published by `track_odometry_node`.

Type:

```text
nav_msgs/msg/Odometry
```

Frames:

```text
header.frame_id = odom
child_frame_id = base_link
```

This topic contains the estimated robot pose and velocity computed from the measured left and right track speeds.

### `/tf`

Published by `track_odometry_node` when `publish_tf` is enabled.

Transform:

```text
odom -> base_link
```

This transform is required for RViz, SLAM, and navigation stacks such as Nav2.

## Odometry model

The odometry node uses differential-drive kinematics.

Given:

```text
left_speed  = measured left track speed in m/s
right_speed = measured right track speed in m/s
track_width = distance between left and right tracks in m
```

The robot linear and angular velocities are computed as:

```text
linear_speed = (right_speed + left_speed) / 2
angular_speed = (right_speed - left_speed) / track_width
```

The node integrates these velocities over time to estimate:

```text
x
y
theta
```

This odometry is based only on the VESC feedback and does not correct for wheel slip, track slip, IMU drift, GPS, or external localization.

## TF tree

After starting the odometry node, the minimum TF tree is:

```text
odom
└── base_link
```

If a LiDAR or other sensor is used, add a static transform from `base_link` to the sensor frame.

Example:

```bash
ros2 run tf2_ros static_transform_publisher \
  0.25 0.0 0.35 \
  0 0 0 \
  base_link lidar_link
```

This gives:

```text
odom
└── base_link
    └── lidar_link
```

Replace `lidar_link` with the actual `frame_id` published by your LiDAR driver.

## Testing

### Test reading VESC values without ROS 2

```bash
python3 tools/test_read_vesc.py /dev/ttyACM0
```

### Test sending an eRPM command without ROS 2

```bash
python3 tools/test_set_rpm.py /dev/ttyACM0 5000
```

Use a low eRPM value for the first tests and make sure the robot is safely lifted or the tracks are not touching the ground.

### Test motor command with ROS 2

```bash
ros2 topic pub /vesc/track_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.1, 0.1]}"
```

Stop:

```bash
ros2 topic pub /vesc/track_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0]}"
```

### Check feedback

```bash
ros2 topic echo /vesc/track_speed_feedback
```

Expected format:

```yaml
layout:
  dim: []
  data_offset: 0
data:
- 0.1
- 0.1
```

### Check odometry

```bash
ros2 topic echo /odom --once
```

### Check TF

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

### Generate TF tree

Install the TF tools if needed:

```bash
sudo apt install ros-$ROS_DISTRO-tf2-tools
```

Then run:

```bash
ros2 run tf2_tools view_frames
```

This generates a `frames.pdf` file showing the TF tree.

## Safety

Before running this package on a real robot:

* Lift the robot so the tracks or wheels cannot touch the ground
* Start with very low speed commands
* Check motor direction using `left_sign` and `right_sign`
* Verify that the emergency stop system works
* Verify that `cmd_timeout` stops the motors when commands are lost
* Check that the serial ports match the correct left and right VESCs
* Verify that the odometry direction is correct before using SLAM or navigation
* Verify the value of `track_width`
* Do not run autonomous navigation before validating `/odom` and `/tf`

## Automatic reconnection

The motor node can be started even if the VESCs are not connected yet.

If `/dev/ttyACM0` or `/dev/ttyACM1` are missing at startup, the node will keep running and retry the serial connection periodically.
This is useful when the ROS 2 system starts before the ESCs are powered or detected by Linux.

## Build after changes

After modifying the package:

```bash
cd ~/ros2_ws
rm -rf build install log
source /opt/ros/<your_ros_distro>/setup.bash
colcon build --packages-select ros2_vesc_control
source install/setup.bash
```

Example:

```bash
cd ~/ros2_ws
rm -rf build install log
source /opt/ros/jazzy/setup.bash
colcon build --packages-select ros2_vesc_control
source install/setup.bash
```

## Git commands after adding odometry

```bash
cd ~/ros2_ws/src/ros2_vesc_control

git add README.md
git add package.xml
git add setup.py
git add config/track_odometry.yaml
git add launch/track_odometry.launch.py
git add ros2_vesc_control/track_odometry_node.py

git commit -m "Add track odometry node"
git push
```

## License

This project is licensed under the MIT License.

## Author

Samuel Gendre
