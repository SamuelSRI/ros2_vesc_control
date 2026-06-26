#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


def yaw_to_quaternion(yaw: float):
    qz = math.sin(yaw * 0.5)
    qw = math.cos(yaw * 0.5)
    return qz, qw


class TrackOdometryNode(Node):
    def __init__(self):
        super().__init__("track_odometry_node")

        self.declare_parameter("feedback_topic", "/vesc/track_speed_feedback")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("track_width", 0.50)
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("print_debug", False)

        self.feedback_topic = str(self.get_parameter("feedback_topic").value)
        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.track_width = float(self.get_parameter("track_width").value)
        self.publish_tf = bool(self.get_parameter("publish_tf").value)
        self.print_debug = bool(self.get_parameter("print_debug").value)

        if self.track_width <= 0.0:
            raise ValueError("track_width must be greater than 0")

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.last_time = self.get_clock().now()

        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)

        self.tf_broadcaster = None
        if self.publish_tf:
            self.tf_broadcaster = TransformBroadcaster(self)

        self.sub = self.create_subscription(
            Float32MultiArray,
            self.feedback_topic,
            self.feedback_callback,
            10,
        )

        self.get_logger().info("Track odometry node started")
        self.get_logger().info(f"Subscribing to: {self.feedback_topic}")
        self.get_logger().info(f"Publishing odom to: {self.odom_topic}")
        self.get_logger().info(f"TF: {self.odom_frame} -> {self.base_frame}")
        self.get_logger().info(f"track_width: {self.track_width} m")

    def feedback_callback(self, msg: Float32MultiArray):
        if len(msg.data) < 2:
            self.get_logger().warn(
                "Feedback message must contain [left_speed, right_speed]"
            )
            return

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        if dt <= 0.0 or dt > 1.0:
            return

        left_speed = float(msg.data[0])
        right_speed = float(msg.data[1])

        linear_speed = 0.5 * (right_speed + left_speed)
        angular_speed = (right_speed - left_speed) / self.track_width

        self.x += linear_speed * math.cos(self.theta) * dt
        self.y += linear_speed * math.sin(self.theta) * dt
        self.theta += angular_speed * dt

        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        qz, qw = yaw_to_quaternion(self.theta)

        odom_msg = Odometry()
        odom_msg.header.stamp = now.to_msg()
        odom_msg.header.frame_id = self.odom_frame
        odom_msg.child_frame_id = self.base_frame

        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0

        odom_msg.pose.pose.orientation.x = 0.0
        odom_msg.pose.pose.orientation.y = 0.0
        odom_msg.pose.pose.orientation.z = qz
        odom_msg.pose.pose.orientation.w = qw

        odom_msg.twist.twist.linear.x = linear_speed
        odom_msg.twist.twist.linear.y = 0.0
        odom_msg.twist.twist.linear.z = 0.0

        odom_msg.twist.twist.angular.x = 0.0
        odom_msg.twist.twist.angular.y = 0.0
        odom_msg.twist.twist.angular.z = angular_speed

        self.odom_pub.publish(odom_msg)

        if self.publish_tf and self.tf_broadcaster is not None:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = now.to_msg()
            tf_msg.header.frame_id = self.odom_frame
            tf_msg.child_frame_id = self.base_frame

            tf_msg.transform.translation.x = self.x
            tf_msg.transform.translation.y = self.y
            tf_msg.transform.translation.z = 0.0

            tf_msg.transform.rotation.x = 0.0
            tf_msg.transform.rotation.y = 0.0
            tf_msg.transform.rotation.z = qz
            tf_msg.transform.rotation.w = qw

            self.tf_broadcaster.sendTransform(tf_msg)

        if self.print_debug:
            self.get_logger().info(
                f"x={self.x:.3f}, y={self.y:.3f}, "
                f"theta={self.theta:.3f}, "
                f"v={linear_speed:.3f}, w={angular_speed:.3f}"
            )


def main(args=None):
    rclpy.init(args=args)
    node = TrackOdometryNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
