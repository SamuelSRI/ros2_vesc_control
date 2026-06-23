# rover_vesc_control

ROS 2 package to control two VESC motor controllers over UART.

This package does not use `pyvesc`.
The VESC UART packets are implemented directly in Python.

## Features

- Control left and right tracks using speed commands in m/s
- Convert m/s to VESC eRPM
- Read VESC values using `COMM_GET_VALUES`
- Publish measured eRPM, speed, current, voltage, duty cycle, temperature and fault code
- Fully configurable using ROS 2 parameters or YAML files
- Includes non-ROS test tools for VESC UART communication

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
data[3]  = motor current A
data[4]  = input current A
data[5]  = input voltage V
data[6]  = MOSFET temperature °C
data[7]  = motor temperature °C
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

## Parameters

| Parameter | Description | Default |
|---|---|---|
| `left_port` | Serial port of left VESC | `/dev/ttyACM0` |
| `right_port` | Serial port of right VESC | `/dev/ttyACM1` |
| `baudrate` | UART baudrate | `115200` |
| `wheel_diameter` | Wheel diameter in meters | `0.165` |
| `gear_ratio` | Reduction ratio | `20.0` |
| `motor_poles` | Number of motor poles | `14.0` |
| `max_erpm` | Maximum allowed eRPM command | `35000` |
| `left_sign` | Left motor direction sign | `1.0` |
| `right_sign` | Right motor direction sign | `1.0` |
| `command_topic` | Speed command topic | `/vesc/track_speed_cmd` |
| `left_state_topic` | Left ESC feedback topic | `/vesc/left/state` |
| `right_state_topic` | Right ESC feedback topic | `/vesc/right/state` |
| `feedback_topic` | Track speed feedback topic | `/vesc/track_speed_feedback` |
| `control_rate_hz` | Motor command rate | `20.0` |
| `read_rate_hz` | VESC feedback read rate | `10.0` |
| `cmd_timeout` | Stop motors after command timeout | `0.5` |
| `print_debug` | Enable debug logs | `false` |

## Installation with uv

```bash
cd ~/ros2_ws
uv venv --system-site-packages .venv
source .venv/bin/activate
uv pip install -r src/rover_vesc_control/requirements.txt
```

## Build

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
colcon build --symlink-install --packages-select rover_vesc_control
source install/setup.bash
```

## Run

```bash
ros2 launch rover_vesc_control vesc_tracks.launch.py
```

With custom config:

```bash
ros2 launch rover_vesc_control vesc_tracks.launch.py \
  config_file:=/path/to/my_config.yaml
```

## Test command

```bash
ros2 topic pub /vesc/track_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.1, 0.1]}"
```

Stop:

```bash
ros2 topic pub /vesc/track_speed_cmd std_msgs/msg/Float32MultiArray "{data: [0.0, 0.0]}"
```

## Non-ROS tests

Read VESC values:

```bash
python3 tools/test_read_vesc.py /dev/ttyACM0
```

Send eRPM command:

```bash
python3 tools/test_set_rpm.py /dev/ttyACM0 5000
```