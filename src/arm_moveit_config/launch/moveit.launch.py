import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node


def load_yaml(package, filename):
    path = os.path.join(get_package_share_directory(package), 'config', filename)
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def generate_launch_description():
    desc_dir = get_package_share_directory('arm_description')
    moveit_dir = get_package_share_directory('arm_moveit_config')

    xacro_file = os.path.join(desc_dir, 'urdf', 'arm.urdf.xacro')
    robot_description = Command(['xacro ', xacro_file])

    srdf_file = os.path.join(moveit_dir, 'config', 'arm.srdf')
    with open(srdf_file, 'r') as f:
        robot_description_semantic = f.read()

    kinematics = load_yaml('arm_moveit_config', 'kinematics.yaml')
    joint_limits = load_yaml('arm_moveit_config', 'joint_limits.yaml')
    ompl_planning = load_yaml('arm_moveit_config', 'ompl_planning.yaml')
    controllers = load_yaml('arm_moveit_config', 'moveit_controllers.yaml')

    move_group_params = {
        'robot_description': robot_description,
        'robot_description_semantic': robot_description_semantic,
        'robot_description_kinematics': kinematics,
        'robot_description_planning': ompl_planning,
        'planning_pipelines': ['ompl'],
        'ompl': ompl_planning,
        'robot_description_joint_limits': joint_limits,
        'use_sim_time': False,
        'publish_robot_description_semantic': True,
        'allow_trajectory_execution': True,
        'execution_duration_monitoring': False,
        'moveit_controller_manager': controllers['moveit_controller_manager'],
        'moveit_simple_controller_manager': controllers['moveit_simple_controller_manager'],
    }

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen'
        ),
        Node(
            package='moveit_ros_move_group',
            executable='move_group',
            parameters=[move_group_params],
            output='screen'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', os.path.join(moveit_dir, 'config', 'moveit.rviz')],
            output='screen'
        ),
    ])
