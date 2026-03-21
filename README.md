# ROS2 6DOF Robotic Arm

A ROS2 Humble workspace for controlling a 6DOF robotic arm with MG996R servos via a PCA9685 PWM driver, running on an NVIDIA Jetson Orin Nano Developer Kit.

## Hardware

- **Controller**: NVIDIA Jetson Orin Nano 8GB (JetPack 6.2, Ubuntu 22.04)
- **Servo Driver**: PCA9685 16-channel PWM board (I2C, address 0x40)
- **Servos**: 6x MG996R (180-degree, metal gear)
- **Power Supply**: 5.2V 10A (external, via PCA9685 screw terminal)
- **Arm Kit**: Generic 6DOF aluminium bracket kit

## Joint Configuration

| Channel | Joint           | Range         |
|---------|-----------------|---------------|
| 0       | Base rotation   | 0 - 180 deg   |
| 1       | Shoulder        | 0 - 180 deg   |
| 2       | Elbow           | 0 - 180 deg   |
| 3       | Wrist pitch     | 0 - 180 deg   |
| 4       | Wrist roll      | 0 - 180 deg   |
| 5       | Gripper         | 80 - 150 deg  |

## Arm Dimensions

| Segment          | Length  |
|------------------|---------|
| Base plate       | 90x88mm |
| Base height      | 84mm    |
| Upper arm        | 130mm   |
| Forearm          | 83mm    |
| Wrist to gripper | 107mm   |

## Packages

### arm_driver

ROS2 Python package containing three nodes:

- **arm_driver** — Hardware interface node. Subscribes to `/arm/joint_commands` and drives the PCA9685 servos. Publishes current joint states on `/arm/joint_states` at 10Hz.
- **teleop** — Keyboard teleoperation node. Select joints with 1-6, move with a/d, toggle step size with s, center all with c.
- **bridge** — Sim-to-real bridge. Converts `/joint_states` (radians, from RViz sliders) to `/arm/joint_commands` (degrees, for the servo driver). Includes a 1-degree deadband to prevent servo jitter.

### arm_description

URDF description package for the arm:

- **urdf/arm.urdf.xacro** — Full URDF with accurate dimensions, joint limits, inertial properties, and collision geometry.
- **launch/display.launch.py** — Launches RViz with Joint State Publisher GUI for simulation.
- **rviz/arm_display.rviz** — Pre-configured RViz view.

## Wiring (PCA9685 to Jetson Orin Nano)

| PCA9685 Header | Jetson 40-pin |
|----------------|---------------|
| SDA            | Pin 3         |
| SCL            | Pin 5         |
| VCC            | Pin 1 (3.3V)  |
| GND            | Pin 6         |
| OE             | unconnected   |
| V+             | unconnected   |

Servo power goes through the PCA9685 screw terminal from the external 5V supply. Do not power servos from the Jetson.

## Setup

### Prerequisites

```bash
# ROS2 Humble (already installed on Jetson)
sudo apt install -y ros-humble-xacro ros-humble-joint-state-publisher-gui ros-humble-robot-state-publisher python3-colcon-common-extensions

# Servo libraries (system-wide for ROS2 access)
sudo pip3 install adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit Jetson.GPIO
```

### Build

```bash
cd ~/ros2_arm_ws
colcon build
source install/setup.bash
```

### Verify I2C

```bash
sudo i2cdetect -y -r 7
# Should show 0x40
```

## Usage

### Simulation only (no hardware needed)

```bash
ros2 launch arm_description display.launch.py
```

Move the sliders in the Joint State Publisher GUI to control the arm in RViz.

### Keyboard teleoperation (hardware)

```bash
# Terminal 1
ros2 run arm_driver arm_driver

# Terminal 2
ros2 run arm_driver teleop
```

### Sim-to-real (RViz controls real arm)

```bash
# Terminal 1: Hardware driver
ros2 run arm_driver arm_driver

# Terminal 2: RViz with sliders
ros2 launch arm_description display.launch.py

# Terminal 3: Bridge
ros2 run arm_driver bridge
```

Move sliders in RViz and the real arm follows.

## ROS2 Topics

| Topic                | Type        | Description                    |
|----------------------|-------------|--------------------------------|
| /joint_states        | JointState  | From GUI sliders (radians)     |
| /arm/joint_commands  | JointState  | Servo commands (degrees)       |
| /arm/joint_states    | JointState  | Current servo positions        |

## License

MIT
