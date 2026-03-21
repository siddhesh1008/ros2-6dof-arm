import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import sys
import termios
import tty


class TeleopNode(Node):
    def __init__(self):
        super().__init__('arm_teleop')

        self.pub = self.create_publisher(JointState, '/arm/joint_commands', 10)

        self.joint_names = [
            'base_rotation',
            'shoulder',
            'elbow',
            'wrist_pitch',
            'wrist_roll',
            'gripper'
        ]

        self.limits = {
            'base_rotation': [0.0, 180.0],
            'shoulder': [0.0, 180.0],
            'elbow': [0.0, 180.0],
            'wrist_pitch': [0.0, 180.0],
            'wrist_roll': [0.0, 180.0],
            'gripper': [80.0, 150.0]
        }

        # Start at center of each joint's range
        self.angles = {}
        for name in self.joint_names:
            self.angles[name] = (self.limits[name][0] + self.limits[name][1]) / 2.0

        self.active_joint = 0
        self.step = 5.0

        self.print_controls()

    def print_controls(self):
        print('\n--- Arm Teleop Controls ---')
        print('1-6  : Select joint')
        print('a/d  : Decrease/Increase angle')
        print('s    : Step size toggle (5 / 15)')
        print('c    : Center all joints')
        print('q    : Quit')
        print('--------------------------')
        self.print_status()

    def print_status(self):
        print(f'\nActive: {self.joint_names[self.active_joint]} | Step: {self.step}')
        for i, name in enumerate(self.joint_names):
            marker = ' >> ' if i == self.active_joint else '    '
            lo, hi = self.limits[name]
            print(f'{marker}{i+1}. {name}: {self.angles[name]:.1f}  [{lo}-{hi}]')

    def send_command(self):
        msg = JointState()
        msg.name = [self.joint_names[self.active_joint]]
        msg.position = [self.angles[self.joint_names[self.active_joint]]]
        self.pub.publish(msg)

    def run(self):
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            while True:
                ch = sys.stdin.read(1)

                if ch == 'q':
                    print('\nQuitting...')
                    break
                elif ch in '123456':
                    self.active_joint = int(ch) - 1
                    self.print_status()
                elif ch == 'a':
                    name = self.joint_names[self.active_joint]
                    lo = self.limits[name][0]
                    self.angles[name] = max(lo, self.angles[name] - self.step)
                    self.send_command()
                    self.print_status()
                elif ch == 'd':
                    name = self.joint_names[self.active_joint]
                    hi = self.limits[name][1]
                    self.angles[name] = min(hi, self.angles[name] + self.step)
                    self.send_command()
                    self.print_status()
                elif ch == 's':
                    self.step = 15.0 if self.step == 5.0 else 5.0
                    self.print_status()
                elif ch == 'c':
                    msg = JointState()
                    msg.name = self.joint_names
                    positions = []
                    for name in self.joint_names:
                        mid = (self.limits[name][0] + self.limits[name][1]) / 2.0
                        self.angles[name] = mid
                        positions.append(mid)
                    msg.position = positions
                    self.pub.publish(msg)
                    print('\nCentered all joints')
                    self.print_status()
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def main(args=None):
    rclpy.init(args=args)
    node = TeleopNode()
    node.run()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
