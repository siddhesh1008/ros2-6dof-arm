import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from adafruit_servokit import ServoKit
import board
import busio


class ArmDriverNode(Node):
    def __init__(self):
        super().__init__('arm_driver')

        self.joint_names = [
            'base_rotation',
            'shoulder',
            'elbow',
            'wrist_pitch',
            'wrist_roll',
            'gripper'
        ]

        self.channels = {
            'base_rotation': 0,
            'shoulder': 1,
            'elbow': 2,
            'wrist_pitch': 3,
            'wrist_roll': 4,
            'gripper': 5
        }

        # Per-joint angle limits [min, max]
        self.limits = {
            'base_rotation': [0.0, 180.0],
            'shoulder': [0.0, 180.0],
            'elbow': [0.0, 180.0],
            'wrist_pitch': [0.0, 180.0],
            'wrist_roll': [0.0, 180.0],
            'gripper': [80.0, 150.0]
        }

        # Initialize PCA9685
        i2c = busio.I2C(board.SCL, board.SDA)
        self.kit = ServoKit(channels=16, i2c=i2c)

        for ch in self.channels.values():
            self.kit.servo[ch].set_pulse_width_range(500, 2500)

        # Default to center of each joint's range
        self.current_angles = {}
        for name in self.joint_names:
            mid = (self.limits[name][0] + self.limits[name][1]) / 2.0
            self.current_angles[name] = mid

        self.cmd_sub = self.create_subscription(
            JointState,
            '/arm/joint_commands',
            self.joint_command_callback,
            10
        )

        self.state_pub = self.create_publisher(
            JointState,
            '/arm/joint_states',
            10
        )

        self.timer = self.create_timer(0.1, self.publish_joint_states)

        self.get_logger().info('Arm driver node started')
        self.get_logger().info('Listening on /arm/joint_commands')
        self.get_logger().info('Publishing on /arm/joint_states')

    def joint_command_callback(self, msg):
        for i, name in enumerate(msg.name):
            if name in self.channels:
                angle = msg.position[i]
                lo, hi = self.limits[name]
                angle = max(lo, min(hi, angle))
                ch = self.channels[name]
                self.kit.servo[ch].angle = angle
                self.current_angles[name] = angle
                self.get_logger().info(f'{name} -> {angle:.1f} degrees')

    def publish_joint_states(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = [self.current_angles[name] for name in self.joint_names]
        self.state_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ArmDriverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
