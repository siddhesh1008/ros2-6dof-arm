"""
Fake trajectory controller for MoveIt2 simulation.

What this does:
MoveIt2 plans a trajectory (a list of joint angles at specific timestamps).
It sends this trajectory to an action server at arm_controller/follow_joint_trajectory.
This node IS that action server. It receives the trajectory, steps through
each waypoint, and publishes the joint positions on /joint_states so RViz
and robot_state_publisher can update the visualization.

Without this node, MoveIt2 can plan but can't "execute" because nobody is
listening for the trajectory.

The reason it's called "fake" is because it's not controlling real hardware.
It just publishes joint states to make the sim move. When you connect the
real arm later, you'd replace this with a controller that sends actual
servo commands.
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState
import time


class FakeTrajectoryController(Node):
    def __init__(self):
        super().__init__('fake_trajectory_controller')

        self.cb_group = ReentrantCallbackGroup()

        # The joint state publisher - this is how we tell RViz where the arm is
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)

        # All joints and their current positions
        self.joint_names = [
            'base_rotation_joint',
            'shoulder_joint',
            'elbow_joint',
            'wrist_pitch_joint',
            'wrist_roll_joint',
            'finger_left_joint',
            'finger_right_joint'
        ]
        self.joint_positions = {name: 0.0 for name in self.joint_names}

        # Action server for the arm controller
        # MoveIt2 sends FollowJointTrajectory goals here
        self.arm_action = ActionServer(
            self,
            FollowJointTrajectory,
            'arm_controller/follow_joint_trajectory',
            self.execute_trajectory,
            callback_group=self.cb_group
        )

        # Action server for the gripper controller
        self.gripper_action = ActionServer(
            self,
            FollowJointTrajectory,
            'gripper_controller/follow_joint_trajectory',
            self.execute_trajectory,
            callback_group=self.cb_group
        )

        # Publish joint states at 50Hz so RViz updates smoothly
        self.timer = self.create_timer(0.02, self.publish_joint_states)

        self.get_logger().info('Fake trajectory controller started')
        self.get_logger().info('  arm_controller/follow_joint_trajectory')
        self.get_logger().info('  gripper_controller/follow_joint_trajectory')

    def publish_joint_states(self):
        """Publish current joint positions on /joint_states at 50Hz"""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = [self.joint_positions[n] for n in self.joint_names]
        self.joint_pub.publish(msg)

    def execute_trajectory(self, goal_handle):
        """
        Called when MoveIt2 sends a trajectory to execute.

        A trajectory is a list of TrajectoryPoints. Each point has:
        - positions: the joint angles at this waypoint
        - time_from_start: when this waypoint should be reached

        We step through each point, update joint positions, and sleep
        for the correct duration between points. This makes the arm
        move smoothly in RViz.
        """
        trajectory = goal_handle.request.trajectory
        joint_names = trajectory.joint_names
        points = trajectory.points

        self.get_logger().info(
            f'Executing trajectory with {len(points)} points '
            f'for joints: {joint_names}'
        )

        prev_time = 0.0

        for point in points:
            # Calculate how long to wait before this waypoint
            current_time = point.time_from_start.sec + point.time_from_start.nanosec * 1e-9
            sleep_duration = current_time - prev_time
            prev_time = current_time

            if sleep_duration > 0:
                time.sleep(sleep_duration)

            # Update joint positions
            for i, name in enumerate(joint_names):
                if name in self.joint_positions:
                    self.joint_positions[name] = point.positions[i]

        goal_handle.succeed()

        result = FollowJointTrajectory.Result()
        self.get_logger().info('Trajectory execution complete')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = FakeTrajectoryController()
    # Use MultiThreadedExecutor so the action server can process
    # goals while the timer keeps publishing joint states
    from rclpy.executors import MultiThreadedExecutor
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
