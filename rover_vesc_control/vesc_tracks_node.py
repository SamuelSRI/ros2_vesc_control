#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray

from rover_vesc_control.vesc_uart import VescUart


class VescTracksNode(Node):
    def __init__(self):
        super().__init__("vesc_tracks_node")

        self.declare_parameter("left_port", "/dev/ttyACM0")
        self.declare_parameter("right_port", "/dev/ttyACM1")
        self.declare_parameter("baudrate", 115200)

        self.declare_parameter("wheel_diameter", 0.165)
        self.declare_parameter("gear_ratio", 20.0)
        self.declare_parameter("motor_poles", 14.0)
        self.declare_parameter("max_erpm", 35000)

        self.declare_parameter("left_sign", 1.0)
        self.declare_parameter("right_sign", 1.0)

        self.declare_parameter("command_topic", "/vesc/track_speed_cmd")
        self.declare_parameter("left_state_topic", "/vesc/left/state")
        self.declare_parameter("right_state_topic", "/vesc/right/state")
        self.declare_parameter("feedback_topic", "/vesc/track_speed_feedback")

        self.declare_parameter("control_rate_hz", 20.0)
        self.declare_parameter("read_rate_hz", 10.0)
        self.declare_parameter("cmd_timeout", 0.5)

        self.declare_parameter("print_debug", False)

        self.left_port = str(self.get_parameter("left_port").value)
        self.right_port = str(self.get_parameter("right_port").value)
        self.baudrate = int(self.get_parameter("baudrate").value)

        self.wheel_diameter = float(self.get_parameter("wheel_diameter").value)
        self.gear_ratio = float(self.get_parameter("gear_ratio").value)
        self.motor_poles = float(self.get_parameter("motor_poles").value)
        self.pole_pairs = self.motor_poles / 2.0

        self.max_erpm = int(self.get_parameter("max_erpm").value)

        self.left_sign = float(self.get_parameter("left_sign").value)
        self.right_sign = float(self.get_parameter("right_sign").value)

        self.command_topic = str(self.get_parameter("command_topic").value)
        self.left_state_topic = str(self.get_parameter("left_state_topic").value)
        self.right_state_topic = str(self.get_parameter("right_state_topic").value)
        self.feedback_topic = str(self.get_parameter("feedback_topic").value)

        self.control_rate_hz = float(self.get_parameter("control_rate_hz").value)
        self.read_rate_hz = float(self.get_parameter("read_rate_hz").value)
        self.cmd_timeout = float(self.get_parameter("cmd_timeout").value)

        self.print_debug = bool(self.get_parameter("print_debug").value)

        self.validate_parameters()

        try:
            self.left_vesc = VescUart(self.left_port, self.baudrate)
            self.right_vesc = VescUart(self.right_port, self.baudrate)

        except Exception as error:
            self.get_logger().fatal(f"Failed to open VESC serial ports: {error}")
            raise

        self.left_cmd_m_s = 0.0
        self.right_cmd_m_s = 0.0
        self.last_cmd_time = time.time()
        self.last_read_time = 0.0

        self.cmd_sub = self.create_subscription(
            Float32MultiArray,
            self.command_topic,
            self.cmd_callback,
            10
        )

        self.left_state_pub = self.create_publisher(
            Float32MultiArray,
            self.left_state_topic,
            10
        )

        self.right_state_pub = self.create_publisher(
            Float32MultiArray,
            self.right_state_topic,
            10
        )

        self.speed_feedback_pub = self.create_publisher(
            Float32MultiArray,
            self.feedback_topic,
            10
        )

        self.timer = self.create_timer(
            1.0 / self.control_rate_hz,
            self.main_loop
        )

        self.print_startup_summary()

    def validate_parameters(self):
        if self.wheel_diameter <= 0.0:
            raise ValueError("wheel_diameter must be > 0")

        if self.gear_ratio <= 0.0:
            raise ValueError("gear_ratio must be > 0")

        if self.motor_poles <= 0.0:
            raise ValueError("motor_poles must be > 0")

        if self.max_erpm <= 0:
            raise ValueError("max_erpm must be > 0")

        if self.control_rate_hz <= 0.0:
            raise ValueError("control_rate_hz must be > 0")

        if self.read_rate_hz <= 0.0:
            raise ValueError("read_rate_hz must be > 0")

        if self.cmd_timeout <= 0.0:
            raise ValueError("cmd_timeout must be > 0")

        if self.left_sign not in (-1.0, 1.0):
            raise ValueError("left_sign must be 1.0 or -1.0")

        if self.right_sign not in (-1.0, 1.0):
            raise ValueError("right_sign must be 1.0 or -1.0")

    def print_startup_summary(self):
        self.get_logger().info("VESC tracks node started.")
        self.get_logger().info(f"Left VESC: {self.left_port}")
        self.get_logger().info(f"Right VESC: {self.right_port}")
        self.get_logger().info(f"Baudrate: {self.baudrate}")
        self.get_logger().info(f"Command topic: {self.command_topic}")
        self.get_logger().info(f"Left state topic: {self.left_state_topic}")
        self.get_logger().info(f"Right state topic: {self.right_state_topic}")
        self.get_logger().info(f"Feedback topic: {self.feedback_topic}")
        self.get_logger().info(f"Wheel diameter: {self.wheel_diameter} m")
        self.get_logger().info(f"Gear ratio: {self.gear_ratio}")
        self.get_logger().info(f"Motor poles: {self.motor_poles}")
        self.get_logger().info(f"Max eRPM: {self.max_erpm}")

    def cmd_callback(self, msg: Float32MultiArray):
        if len(msg.data) < 2:
            self.get_logger().warn("Command must contain [left_m_s, right_m_s]")
            return

        self.left_cmd_m_s = float(msg.data[0])
        self.right_cmd_m_s = float(msg.data[1])
        self.last_cmd_time = time.time()

        if self.print_debug:
            self.get_logger().info(
                f"Command received: left={self.left_cmd_m_s:.3f} m/s, "
                f"right={self.right_cmd_m_s:.3f} m/s"
            )

    def speed_to_erpm(self, speed_m_s: float) -> int:
        wheel_circumference = math.pi * self.wheel_diameter

        wheel_rps = speed_m_s / wheel_circumference
        wheel_rpm = wheel_rps * 60.0

        motor_rpm = wheel_rpm * self.gear_ratio
        erpm = motor_rpm * self.pole_pairs

        erpm = int(erpm)

        if erpm > self.max_erpm:
            erpm = self.max_erpm

        if erpm < -self.max_erpm:
            erpm = -self.max_erpm

        return erpm

    def erpm_to_speed(self, erpm: float) -> float:
        motor_rpm = erpm / self.pole_pairs
        wheel_rpm = motor_rpm / self.gear_ratio
        wheel_rps = wheel_rpm / 60.0

        return wheel_rps * math.pi * self.wheel_diameter

    def main_loop(self):
        self.send_motor_commands()

        now = time.time()

        if now - self.last_read_time >= 1.0 / self.read_rate_hz:
            self.last_read_time = now
            self.read_and_publish_values()

    def send_motor_commands(self):
        now = time.time()

        if now - self.last_cmd_time > self.cmd_timeout:
            left_erpm = 0
            right_erpm = 0
        else:
            left_erpm = self.speed_to_erpm(self.left_cmd_m_s)
            right_erpm = self.speed_to_erpm(self.right_cmd_m_s)

            left_erpm = int(left_erpm * self.left_sign)
            right_erpm = int(right_erpm * self.right_sign)

        try:
            self.left_vesc.send_erpm(left_erpm)
            self.right_vesc.send_erpm(right_erpm)

            if self.print_debug:
                self.get_logger().info(
                    f"Sent eRPM: left={left_erpm}, right={right_erpm}"
                )

        except Exception as error:
            self.get_logger().error(f"Command error: {error}")

    def read_and_publish_values(self):
        left_values = self.left_vesc.read_values()
        right_values = self.right_vesc.read_values()

        left_speed_m_s = 0.0
        right_speed_m_s = 0.0

        if left_values is not None:
            left_speed_m_s = self.publish_state(
                values=left_values,
                publisher=self.left_state_pub,
                sign=self.left_sign,
                side_name="left"
            )
        else:
            self.get_logger().warn("No values received from left VESC")

        if right_values is not None:
            right_speed_m_s = self.publish_state(
                values=right_values,
                publisher=self.right_state_pub,
                sign=self.right_sign,
                side_name="right"
            )
        else:
            self.get_logger().warn("No values received from right VESC")

        feedback_msg = Float32MultiArray()
        feedback_msg.data = [
            float(left_speed_m_s),
            float(right_speed_m_s),
        ]

        self.speed_feedback_pub.publish(feedback_msg)

    def publish_state(self, values: dict, publisher, sign: float, side_name: str) -> float:
        measured_erpm = float(values["rpm"]) * sign
        measured_speed_m_s = self.erpm_to_speed(measured_erpm)

        msg = Float32MultiArray()

        msg.data = [
            float(measured_erpm),
            float(measured_speed_m_s),
            float(values["duty"]),
            float(values["current_motor"]),
            float(values["current_in"]),
            float(values["v_in"]),
            float(values["temp_mos"]),
            float(values["temp_motor"]),
            float(values["tachometer"]),
            float(values["tachometer_abs"]),
            float(values["fault_code"]),
        ]

        publisher.publish(msg)

        if self.print_debug:
            self.get_logger().info(
                f"{side_name}: erpm={measured_erpm:.1f}, "
                f"speed={measured_speed_m_s:.3f} m/s, "
                f"vin={values['v_in']:.1f} V, "
                f"fault={values['fault_code']}"
            )

        return measured_speed_m_s

    def stop_motors(self):
        self.get_logger().info("Stopping motors...")

        for _ in range(20):
            try:
                self.left_vesc.send_erpm(0)
                self.right_vesc.send_erpm(0)
                time.sleep(0.05)
            except Exception:
                pass

    def destroy_node(self):
        self.stop_motors()

        try:
            self.left_vesc.close()
            self.right_vesc.close()
        except Exception:
            pass

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    node = VescTracksNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()