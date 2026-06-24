# ros2_vesc_control

ROS 2 package for controlling two VESC-based motor controllers over UART.

This package is designed for differential drive or tracked rover platforms using one VESC per side.
It sends eRPM commands to the motor controllers and reads feedback values directly through the VESC UART protocol.

## Features

* Control two VESC motor controllers over UART
* Designed for differential drive or tracked rover robots
* Subscribe to target track speeds in m/s
* Convert linear speed commands to VESC eRPM
* Send eRPM commands to left and right VESCs
* Read VESC feedback using `COMM_GET_VALUES`
* Publish measured eRPM, estimated speed, voltage, current, duty cycle, temperatures and fault code
* Configurable through ROS 2 parameters and YAML files
* Automatic reconnection if VESC serial ports are not available at startup
* Includes non-ROS test scripts for direct UART testing

## Package structure

```text
ros2_vesc_control
├── config
│   └── vesc_tracks.yaml
├── launch
│   └── vesc_tracks.launch.py
├── ros2_vesc_control
│   ├── __init__.py
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

The default configuration file is:

```text
config/vesc_tracks.yaml
```

Example configuration:

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

### Important parameters

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

## Serial ports

Before running the node, check which serial ports are assigned to your VESCs:

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

## Running the node

Launch with the default configuration:

```bash
ros2 launch ros2_vesc_control vesc_tracks.launch.py
```

Launch with a custom configuration file:

```bash
ros2 launch ros2_vesc_control vesc_tracks.launch.py config_file:=/path/to/my_config.yaml
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

## Safety

Before running this package on a real robot:

* Lift the robot so the tracks or wheels cannot touch the ground
* Start with very low speed commands
* Check motor direction using `left_sign` and `right_sign`
* Verify that the emergency stop system works
* Verify that `cmd_timeout` stops the motors when commands are lost
* Check that the serial ports match the correct left and right VESCs

## Automatic reconnection

The node can be started even if the VESCs are not connected yet.

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

## License

This project is licensed under the MIT License.

## Author

Samuel Gendre

