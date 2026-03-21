import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class SimToRealBridge(Node):
    def __init__(self):
        super().__init__('sim_to_real_bridge')

        self.joint_map = {
            'base_rotation_joint': ('base_rotation',  -3.14159, 3.14159,   0.0, 180.0),
            'shoulder_joint':      ('shoulder',        -1.5708,  1.5708,  180.0,   0.0),
            'elbow_joint':         ('elbow',           -1.5708,  1.5708,    0.0, 180.0),
            'wrist_pitch_joint':   ('wrist_pitch',     -1.5708,  1.5708,    0.0, 180.0),
            'wrist_roll_joint':    ('wrist_roll',      -3.14159, 3.14159,   0.0, 180.0),
            'finger_left_joint':   ('gripper',          0.0,     0.015,    80.0, 150.0),
        }

        # Track last sent angles to avoid spamming unchanged values
        self.last_sent = {}
        self.deadband = 1.0  # Only send if servo angle changed by more than 1 degree

        self.sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_states_callback,
            10
        )

        self.pub = self.create_publisher(
            JointState,
            '/arm/joint_commands',
            10
        )

        self.get_logger().info('Bridge started: /joint_states -> /arm/joint_commands')

    def radian_to_servo(self, value, rad_min, rad_max, servo_min, servo_max):
        ratio = (value - rad_min) / (rad_max - rad_min)
        ratio = max(0.0, min(1.0, ratio))
        return servo_min + ratio * (servo_max - servo_min)

    def joint_states_callback(self, msg):
        cmd = JointState()
        cmd.header.stamp = self.get_clock().now().to_msg()

        for i, urdf_name in enumerate(msg.name):
            if urdf_name in self.joint_map:
                driver_name, rad_min, rad_max, servo_min, servo_max = self.joint_map[urdf_name]
                rad_value = msg.position[i]
                servo_angle = self.radian_to_servo(rad_value, rad_min, rad_max, servo_min, servo_max)

                # Only send if angle changed significantly
                last = self.last_sent.get(driver_name, None)
                if last is None or abs(servo_angle - last) > self.deadband:
                    cmd.name.append(driver_name)
                    cmd.position.append(servo_angle)
                    self.last_sent[driver_name] = servo_angle

        if cmd.name:
            self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = SimToRealBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
