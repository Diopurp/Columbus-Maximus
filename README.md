# COLUMBUS MAXIMUS

**ROS 2 Mobile Robot Platform for Indoor SLAM, Navigation, Odometry & UWB Localization**

![ROS 2 Humble](https://img.shields.io/badge/ROS_2-Humble-22314E?style=for-the-badge&logo=ros)

![ESP32](https://img.shields.io/badge/ESP32-ESP--IDF-0E83CD?style=for-the-badge&logo=espressif)

![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)

![C/C++](https://img.shields.io/badge/C%2FC%2B%2B-Firmware-00599C?style=for-the-badge&logo=cplusplus&logoColor=white)

![Gazebo](https://img.shields.io/badge/Gazebo-Simulation-orange?style=for-the-badge)

![RViz2](https://img.shields.io/badge/RViz2-Visualization-8A2BE2?style=for-the-badge)

![GitHub stars](https://img.shields.io/github/stars/Diopurp/Columbus-Maximus?style=flat-square)

![GitHub forks](https://img.shields.io/github/forks/Diopurp/Columbus-Maximus?style=flat-square)

![Last commit](https://img.shields.io/github/last-commit/Diopurp/Columbus-Maximus?style=flat-square)

![Repository size](https://img.shields.io/github/repo-size/Diopurp/Columbus-Maximus?style=flat-square)

---

## Project Description

**Columbus Maximus** is a ROS 2 mobile robot platform designed for indoor robotics, autonomous navigation, SLAM, sensor integration, embedded motor control, and localization.

GPS is unreliable or unavailable inside warehouses, factories, laboratories, and other indoor environments. Columbus Maximus explores an alternative approach by combining several sensing and localization technologies:

- **Wheel odometry** for short-term motion estimation.
- **LiDAR** for perception and SLAM.
- **UWB** for absolute indoor position estimation.
- **ROS 2** as the communication and robotics middleware.
- **ESP32 firmware** for low-level motor control, encoder acquisition, PID control, and serial communication.
- **RViz2** for visualization and debugging.
- **Gazebo** for simulation and algorithm development.
- **Nav2** for autonomous navigation experiments.

The system is intentionally modular so that the embedded hardware, ROS 2 drivers, robot description, SLAM, teleoperation, simulation, and UWB localization can be developed and tested independently.

---

## Table of Contents

- [System Overview](about:blank#system-overview)
- [Repository Structure](about:blank#repository-structure)
- [Hardware Architecture](about:blank#hardware-architecture)
- [Software Architecture](about:blank#software-architecture)
- [Physical Robot](about:blank#physical-robot)
- [ESP32 Firmware](about:blank#esp32-firmware)
- [Serial Communication Protocol](about:blank#serial-communication-protocol)
- [Wheel Odometry](about:blank#wheel-odometry)
- [LiDAR](about:blank#lidar)
- [SLAM](about:blank#slam)
- [Teleoperation](about:blank#teleoperation)
- [Gazebo Simulation](about:blank#gazebo-simulation)
- [Nav2](about:blank#nav2)
- [UWB Localization](about:blank#uwb-localization)
- [RViz Visualization](about:blank#rviz-visualization)
- [Installation](about:blank#installation)
- [Building the ROS 2 Workspace](about:blank#building-the-ros-2-workspace)
- [Running the Physical Robot](about:blank#running-the-physical-robot)
- [Running the Simulation](about:blank#running-the-simulation)
- [Running UWB Tracking](about:blank#running-uwb-tracking)
- [Saving a Map](about:blank#saving-a-map)
- [Diagnostics](about:blank#diagnostics)
- [Troubleshooting](about:blank#troubleshooting)
- [Hardware / Software Separation](about:blank#hardware--software-separation)
- [Current Status](about:blank#current-status)
- [Design Philosophy](about:blank#design-philosophy)
- [Future Work](about:blank#future-work)

---

## System Overview

Columbus Maximus is divided into two major environments:

```
                    COLUMBUS MAXIMUS
                           │
             ┌─────────────┴─────────────┐
             │                           │
        PHYSICAL ROBOT              SIMULATION
             │                           │
       ┌─────┴─────┐                ┌────┴────┐
       │           │                │         │
     ESP32       LiDAR            Gazebo     RViz2
       │           │                │         │
       └─────┬─────┘                └────┬────┘
             │                           │
             └────────── ROS 2 ──────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
            Teleop      SLAM       UWB
              │          │          │
              └──────────┼──────────┘
                         │
                        Nav2
                         │
                  Autonomous Robot
```

The physical robot uses an ESP32 as the low-level controller. The ROS 2 computer communicates with the ESP32 over USB serial while independently receiving LiDAR measurements.

The simulation replaces the physical hardware with Gazebo plugins while keeping the ROS 2 interfaces similar.

---

## Repository Structure

```
Columbus-Maximus/
│
├── columbus_firmware/
│   ├── main/
│   │   ├── main.c
│   │   ├── serial_comm.c
│   │   ├── serial_comm.h
│   │   ├── motor_control.c
│   │   ├── motor_control.h
│   │   ├── encoder.c
│   │   ├── encoder.h
│   │   ├── pid.c
│   │   └── pid.h
│   ├── CMakeLists.txt
│   ├── sdkconfig
│   └── COLCON_IGNORE
│
├── SLAM and NAV2/
│   ├── columbusmaximus/
│   │   ├── config/
│   │   ├── description/
│   │   ├── launch/
│   │   ├── maps/
│   │   ├── meshes/
│   │   ├── rviz/
│   │   ├── test/
│   │   └── worlds/
│   │
│   ├── lidar_driver/
│   │   └── ld08_driver/
│   │
│   └── SLAM&NAV2.md
│
├── Teleop and Odometry/
│   ├── columbus_serial_bridge/
│   └── columbus_teleop/
│
├── Chassis_Desgin/
│   ├── Base_plate_2nd_level.stl
│   ├── Base_plate_level1.stl
│   ├── Spacer_40mm.stl
│   ├── Spacer_55mm.stl
│   ├── Uppermost_plate.stl
│   └── upper_plate_1.stl
│
├── simulation/
│   ├── description/
│   ├── launch/
│   ├── meshes/
│   ├── rviz/
│   ├── worlds/
│   ├── model.config
│   ├── model.sdf
│   ├── package.xml
│   ├── setup.cfg
│   ├── setup.py
│   └── README.md
│
├── uwb/
│   ├── datasheets/
│   ├── uwb_tracker/
│   └── README.md
│
└── README.md
```

### Important Workspace Rule

`columbus_firmware/` is an ESP-IDF project, **not** a ROS 2 package.
Do not copy it into:

```
~/columbus_ws/src/
```

The ROS 2 workspace should contain only ROS packages:

```
~/columbus_ws/src/
├── columbusmaximus/
├── ld08_driver/
├── columbus_serial_bridge/
└── columbus_teleop/
```

The ESP32 firmware remains at:

```
~/Columbus-Maximus/columbus_firmware/
```

---

## Hardware Architecture

The physical robot is built around a differential-drive platform.

**Main Components**

- ESP32 microcontroller
- Two driven wheels
- Wheel encoders
- Motor drivers
- LD08 / LDS-02 2D LiDAR
- USB serial connection to ROS 2 computer
- Optional UWB tag and four UWB anchors

The core physical data path is:

```
Keyboard
   │
   ▼
/cmd_vel
   │
   ▼
ROS 2 Serial Bridge
   │
   │ USB Serial
   ▼
ESP32
   │
   ├── PID controller
   ├── Motor controller
   └── Encoders
        │
        ▼
      Odometry
        │
        ▼
      /odom
```

The LiDAR follows a separate path:

```
LD08 / LDS-02
      │
      ▼
 ld08_driver
      │
      ▼
    /scan
      │
      ▼
 SLAM Toolbox
      │
      ▼
    /map
```

---

## Software Architecture

The ROS 2 side consists of several independent components.

```
                         ROS 2 HUMBLE
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  Serial Bridge           LiDAR Driver          Teleop
        │                     │                     │
        ▼                     ▼                     ▼
      /odom                  /scan              /cmd_vel
        │                     │                     │
        └──────────────┬──────┴──────────────┬──────┘
                       │                     │
                       ▼                     │
                 SLAM Toolbox               │
                       │                     │
                       ▼                     │
                     /map                    │
                       │                     │
                       └──────────┬──────────┘
                                  ▼
                                Nav2
                                  │
                                  ▼
                              /cmd_vel
```

Robot state and coordinate transforms are provided through:

```
robot.urdf.xacro
       │
       ▼
robot_state_publisher
       │
       ▼
      TF
```

---

## Physical Robot

The physical robot is designed around:

- ROS 2 Humble
- Ubuntu 22.04
- ESP32
- ESP-IDF 5.3.1
- LD08 / LDS-02 LiDAR
- USB serial communication
- Wheel encoders
- SLAM Toolbox
- RViz2
- Nav2

The physical-robot workflow provides a manual startup sequence for bringing up the robot, odometry, LiDAR, SLAM, visualization, and teleoperation.

## Full Assembled Chassis

<img width="4284" height="5712" alt="CHASSIS" src="https://github.com/user-attachments/assets/d6ff7ac7-5ee0-4f5b-845f-976b280e6ca4" />


---

## ESP32 Firmware

The ESP32 firmware is an independent ESP-IDF application.

The firmware is responsible for:

- Motor control
- PID control
- Encoder acquisition
- Wheel odometry
- Serial communication
- Low-level hardware interaction

The main firmware modules are:

```
main.c
   │
   ├── serial_comm.c
   ├── motor_control.c
   ├── encoder.c
   └── pid.c
```

The ROS computer does not directly control the motor GPIOs. Instead:

```
ROS /cmd_vel
      │
      ▼
Serial Bridge
      │
      ▼
USB Serial
      │
      ▼
ESP32
      │
      ├── PID
      ├── Motor Control
      └── Encoder Feedback
```

### ESP-IDF Installation

The project uses ESP-IDF 5.3.1.

```bash
cd ~
git clone -b v5.3.1 --recursive https://github.com/espressif/esp-idf.git
cd ~/esp-idf
./install.sh esp32
source ~/esp-idf/export.sh
idf.py --version
```

Optionally add ESP-IDF to the shell startup:

```bash
echo "source ~/esp-idf/export.sh" >> ~/.bashrc
source ~/.bashrc
```

### Build the Firmware

```bash
source ~/esp-idf/export.sh
cd ~/Columbus-Maximus/columbus_firmware
idf.py build
```

### Find the ESP32 Serial Port

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
dmesg | tail -50
```

The documentation commonly uses `/dev/ttyUSB0`, but the actual device may be different on your system.

### Flash the Firmware

> Make sure the robot wheels are safely secured during the first firmware test.
> 

```bash
source ~/esp-idf/export.sh
cd ~/Columbus-Maximus/columbus_firmware
idf.py -p /dev/ttyUSB0 flash
```

### ESP32 Monitor

```bash
idf.py -p /dev/ttyUSB0 monitor
```

Exit with `Ctrl + ]`.

> Do not leave the ESP-IDF monitor connected while starting the ROS serial bridge — both applications require exclusive access to the serial port.
> 

---

## Serial Communication Protocol

The ESP32 communicates with ROS 2 using a simple text protocol at **115200 baud**.

**ROS → ESP32** — Velocity command:

```
VEL,<linear>,<angular>
```

Example:

```
VEL,0.2,0.0
```

**ESP32 → ROS** — Odometry:

```
ODOM,<x>,<y>,<yaw>,<linear_velocity>,<angular_velocity>
```

Example:

```
ODOM,0.120000,0.030000,0.020000,0.100000,0.010000
```

This protocol allows the ROS computer and ESP32 firmware to remain cleanly separated.

---

## Wheel Odometry

The documented encoder configuration:

| Parameter | Value |
| --- | --- |
| Left encoder A | GPIO 4 |
| Left encoder B | GPIO 21 |
| Right encoder A | GPIO 22 |
| Right encoder B | GPIO 23 |
| Wheel diameter | 0.11 m |
| Wheel base | 0.22 m |
| Counts/revolution | 2925 |

These values are hardware-specific and should be recalibrated if the physical robot changes.

Odometry is generated from wheel encoder measurements and transmitted from the ESP32 to ROS 2.

```
Encoders
   │
   ▼
ESP32 Odometry
   │
   ▼
Serial
   │
   ▼
columbus_serial_bridge
   │
   ▼
/odom
   │
   ▼
odom → base_link
```

Before starting SLAM, verify:

```bash
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
```

---

# Teleop Demo



## LiDAR

Columbus Maximus uses an LD08 / LDS-02 2D LiDAR. The repository includes an `ld08_driver` ROS 2 package.

The LiDAR provides `/scan` with the configured frame `laser_frame`.

Start the driver:

```bash
ros2 run ld08_driver ld08_driver --ros-args -p frame_id:=laser_frame
```

Verify the scan:

```bash
ros2 topic echo /scan --once
```

Verify the LiDAR transform:

```bash
ros2 run tf2_ros tf2_echo base_link laser_frame
```

SLAM requires both `odom → base_link` and `base_link → laser_frame` to be valid.

---

## SLAM

Columbus Maximus uses SLAM Toolbox for 2D LiDAR-based mapping.

The physical robot uses `columbusmaximus/config/mapper_params_online_async.yaml` with:

```
map frame  = map
odom frame = odom
base frame = base_link
scan topic = /scan
```

Start SLAM on the physical robot:

```bash
ros2 run slam_toolbox async_slam_toolbox_node \
  --ros-args \
  --params-file ~/columbus_ws/src/columbusmaximus/config/mapper_params_online_async.yaml \
  -p use_sim_time:=false
```

```
LD08
 │
 ▼
/scan
 │
 ▼
SLAM Toolbox
 │
 ├── map
 └── map → odom
```

### Building a Map

A typical physical mapping session requires:

- `robot_state_publisher`
- `columbus_serial_bridge`
- `ld08_driver`
- `slam_toolbox`
- `rviz2`
- `columbus_teleop`

Drive the robot slowly through the environment. Monitor `/scan`, `/odom`, `odom → base_link`, and `base_link → laser_frame`.

For better loop closure, revisit previously mapped areas.

---

## Teleoperation

The `columbus_teleop` package provides keyboard-based robot control.

```bash
ros2 run columbus_teleop teleop_node
```

**Controls:**

| Key | Function |
| --- | --- |
| w | Forward |
| s | Backward |
| a | Rotate left |
| d | Rotate right |
| SPACE | Stop |
| q / z | Increase / decrease both speeds |
| e / c | Increase / decrease linear speed |
| r / f | Increase / decrease angular speed |
| CTRL+C | Exit |

```
teleop_node
     │
     ▼
 /cmd_vel
     │
     ▼
serial_bridge
     │
     ▼
ESP32
     │
     ▼
Motor Controller
```

For physical testing, always begin at low speed.

---

## Gazebo Simulation

The `simulation/` directory contains a ROS 2 simulation package for Columbus Maximus. It includes:

- Robot description / Xacro files
- Gazebo plugins and worlds
- Robot meshes
- RViz configurations
- SLAM configuration
- Launch files
- SDF model
- ROS 2 package metadata

The simulated robot is a differential-drive platform equipped with a 360° 2D LiDAR, reproducing `/cmd_vel`, `/odom`, `/scan`, and `/tf`.

### Simulation Robot Description

The robot URDF is composed from `robot_core.xacro`, `gazebo_control.xacro`, and `lidar.xacro`, containing the chassis, wheels, differential-drive controller, LiDAR, sensor mounting, and Gazebo integration.

### Simulation Setup

```bash
mkdir -p ~/columbus_ws/src
cd ~/columbus_ws/src
ros2 pkg create --build-type ament_python columbusmaximus
```

The package name must remain `columbusmaximus`.

```bash
cd path/to/Columbus-Maximus/simulation

rm -rf ~/columbus_ws/src/columbusmaximus/columbusmaximus
rm -rf ~/columbus_ws/src/columbusmaximus/resource
rm -rf ~/columbus_ws/src/columbusmaximus/test

cp -r description launch rviz worlds meshes resource \
  ~/columbus_ws/src/columbusmaximus/

cp package.xml setup.py setup.cfg model.config model.sdf \
  ~/columbus_ws/src/columbusmaximus/

mkdir -p ~/columbus_ws/src/columbusmaximus/columbusmaximus
touch ~/columbus_ws/src/columbusmaximus/columbusmaximus/__init__.py
```

Install dependencies and build:

```bash
cd ~/columbus_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select columbusmaximus
source ~/columbus_ws/install/setup.bash
```

### Launch Gazebo

```bash
ros2 launch columbusmaximus launch_sim.launch.py
```

### Open RViz2

```bash
rviz2 -d ~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/urdf_config.rviz
```

### Drive the Simulated Robot

```bash
sudo apt install ros-humble-teleop-twist-keyboard
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Simulation SLAM

```bash
ros2 launch columbusmaximus launch_sim.launch.py
```

```bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/mapper_params_online_async.yaml \
  use_sim_time:=true
```

```bash
rviz2 -d ~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/slam.rviz
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

The robot will generate an occupancy-grid map from LiDAR data while moving through the Gazebo environment.

---

## Saving a Map

```bash
sudo apt install ros-humble-nav2-map-server
ros2 run nav2_map_server map_saver_cli -f ~/columbus_ws/my_map
```

This produces `my_map.pgm` and `my_map.yaml`.

---

## Nav2

Nav2 is used for autonomous navigation. The simulation includes a demonstrated Nav2 workflow using a saved map.

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup -y
ros2 launch columbusmaximus launch_sim.launch.py
```

```bash
ros2 launch nav2_bringup bringup_launch.py \
  use_sim_time:=true \
  map:=~/columbus_ws/my_map.yaml
```

```bash
rviz2 -d ~/columbus_ws/install/columbusmaximus/share/columbusmaximus/rviz/urdf_config.rviz
```

In RViz:

1. Use **2D Pose Estimate** to localize the robot.
2. Use **Nav2 Goal** to select a destination.
3. Nav2 plans and controls the robot toward the goal using local/global costmaps for obstacle-aware navigation.

### Important Physical-Robot Status

The physical robot currently provides the interfaces Nav2 requires: `/scan`, `/odom`, `/cmd_vel`, `/map`, `map → odom`.

However, the physical Columbus Maximus documentation does **not** currently include a dedicated, tested Columbus-specific Nav2 parameter file. A complete physical Nav2 configuration still needs appropriate configuration for:

- Global planner
- Local controller
- Global costmap
- Local costmap
- Robot footprint
- Inflation
- Obstacle layers
- Velocity limits
- Localization / AMCL
- Behavior and recovery configuration

Therefore, the simulation Nav2 demonstration should not be interpreted as meaning that the physical robot’s Nav2 stack is fully configured.

---

## UWB Localization

The `uwb/` directory provides an independent UWB localization system. The UWB system reads distance measurements from four fixed anchors over serial and computes the position of a moving tag using trilateration.

```
UWB Anchor 1 ─┐
UWB Anchor 2 ─┤
UWB Anchor 3 ─┼── Serial ──> UWB ROS Node
UWB Anchor 4 ─┘                   │
                                  ▼
                            Trilateration
                                  │
                                  ▼
                            (x, y) position
                                  │
                                  ▼
                              /uwb_pose
```

### UWB Repository Structure

```
uwb/
├── datasheets/
│   └── *.pdf
│
└── uwb_tracker/
    ├── uwb_tracker/
    │   ├── __init__.py
    │   ├── uwb_node.py
    │   └── uwb_node_rviz.py
    │
    ├── setup.py
    ├── setup.cfg
    └── package.xml
```

### Components

| Component | Purpose |
| --- | --- |
| `uwb_node.py` | Minimal UWB position node |
| `uwb_node_rviz.py` | UWB node with RViz visualization |
| `trilateration/` | Standalone reference implementations of the positioning math |
| `datasheets/` | UWB hardware and SDK documentation |

The standalone trilateration scripts are reference material and are not intended to be used as ROS nodes.

### UWB Prerequisites

- Ubuntu
- ROS 2 Humble or later
- Python 3.10+
- pyserial
- numpy

```bash
pip install pyserial numpy --break-system-packages
```

### Build the UWB Package

```bash
cp -r uwb_tracker ~/ros2_ws/src/
cd ~/ros2_ws
colcon build --packages-select uwb_tracker
source install/setup.bash
```

### UWB Serial Permissions

UWB hardware commonly appears as `/dev/ttyACM0`.

Temporary permission fix:

```bash
sudo chmod 666 /dev/ttyACM0
```

Recommended permanent configuration:

```bash
sudo usermod -aG dialout $USER
```

Then log out and back in, or reboot. Verify with `groups` — the `dialout` group should appear.

### Run Basic UWB Tracking

```bash
ros2 run uwb_tracker uwb_node
```

The basic node publishes the estimated tag position as `/uwb_pose` using `geometry_msgs/Point`.

### Run UWB Tracking with RViz

```bash
ros2 run uwb_tracker uwb_node_rviz
rviz2
```

Set the RViz **Fixed Frame** to `world`. Add `/tag_marker`, `/tag_path`, and `/anchor_markers`.

The RViz node visualizes fixed anchors, the current tag position, and the tag trajectory / motion trail.

### UWB Testing Without Hardware

The UWB documentation includes a fake serial-data simulator, `fake_uwb_simple.py`, which simulates four anchors, a moving tag, and realistic distance measurements.

```bash
python3 fake_uwb_simple.py
```

The simulator prints a pseudo-terminal such as `/dev/pts/5`. Temporarily configure the UWB node to use that port:

```python
self.SERIAL_PORT = "/dev/pts/5"
```

Then rebuild and run:

```bash
cd ~/ros2_ws
colcon build --packages-select uwb_tracker
source install/setup.bash
ros2 run uwb_tracker uwb_node_rviz
```

Remember to restore the real hardware serial port before using the physical UWB hardware.

---

## RViz Visualization

RViz2 is used throughout the project to inspect the robot and sensor state. Depending on the subsystem, RViz can visualize:

- Robot model
- TF tree
- LiDAR scans
- SLAM map
- UWB anchors, tag, and trajectory
- Nav2 costmaps
- Navigation goals
- Planned paths

Useful configurations in the repository include `slam.rviz`, `lidar_scan.rviz`, and `urdf_config.rviz`.

---

## Installation

The primary physical-robot environment documented by the project:

| Component | Version |
| --- | --- |
| OS | Ubuntu 22.04 |
| ROS 2 | Humble |
| ESP-IDF | 5.3.1 |
| MCU | ESP32 |
| LiDAR | LD08 / LDS-02 |
| Python | 3.10+ for UWB |
| Serial | USB |

Install common development dependencies:

```bash
sudo apt update
sudo apt install -y \
  git \
  build-essential \
  cmake \
  python3-pip \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  tree
```

ROS dependencies:

```bash
sudo apt install -y \
  ros-humble-xacro \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-rviz2 \
  ros-humble-rclpy \
  ros-humble-geometry-msgs \
  ros-humble-nav-msgs \
  ros-humble-tf2-ros \
  ros-humble-std-msgs \
  ros-humble-sensor-msgs \
  ros-humble-slam-toolbox \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-map-server \
  ros-humble-nav2-amcl
```

Serial dependencies:

```bash
sudo apt install -y \
  python3-serial \
  libboost-system-dev \
  libudev-dev
```

### USB Permissions

The ESP32 and LiDAR use USB serial devices. Add the current user to `dialout`:

```bash
sudo usermod -aG dialout $USER
```

Log out and back in, then verify with `groups` — you should see `dialout`.

---

## Building the ROS 2 Workspace

```bash
mkdir -p ~/columbus_ws/src
```

Copy the physical ROS packages:

```bash
cp -r ~/Columbus-Maximus/"SLAM and NAV2"/columbusmaximus \
  ~/columbus_ws/src/

cp -r ~/Columbus-Maximus/"SLAM and NAV2"/lidar_driver/ld08_driver \
  ~/columbus_ws/src/

cp -r ~/Columbus-Maximus/"Teleop and Odometry"/columbus_serial_bridge \
  ~/columbus_ws/src/

cp -r ~/Columbus-Maximus/"Teleop and Odometry"/columbus_teleop \
  ~/columbus_ws/src/
```

The workspace should contain:

```
~/columbus_ws/src/
├── columbus_serial_bridge/
├── columbus_teleop/
├── columbusmaximus/
└── ld08_driver/
```

Initialize and install dependencies:

```bash
source /opt/ros/humble/setup.bash
sudo rosdep init
rosdep update
cd ~/columbus_ws
rosdep install --from-paths src --ignore-src -r -y
```

Build and source:

```bash
colcon build --symlink-install
source ~/columbus_ws/install/setup.bash
```

Optionally make it persistent:

```bash
echo "source ~/columbus_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
ros2 pkg list | grep -E "columbus|ld08"
```

Expected packages: `columbus_serial_bridge`, `columbus_teleop`, `columbusmaximus`, `ld08_driver`.

---

## Running the Physical Robot

A complete physical SLAM session consists of:

1. ESP32 firmware
2. `robot_state_publisher`
3. `serial_bridge`
4. LD08 driver
5. SLAM Toolbox
6. RViz2
7. Teleoperation

### Generate the URDF

```bash
ros2 run xacro xacro \
  ~/columbus_ws/src/columbusmaximus/description/robot.urdf.xacro \
  > /tmp/columbus_robot.urdf

ls -lh /tmp/columbus_robot.urdf
```

### Start Robot State Publisher

```bash
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args \
  -p robot_description:="$(cat /tmp/columbus_robot.urdf)"
```

### Start the Serial Bridge

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*

ros2 run columbus_serial_bridge serial_bridge \
  --ros-args \
  -p port:=/dev/ttyUSB0 \
  -p baud_rate:=115200
```

The integrated bridge receives `/cmd_vel`, sends velocity commands to the ESP32, receives encoder odometry, publishes `/odom`, and broadcasts `odom → base_link`.

**Alternative Serial Nodes:**

```bash
ros2 run columbus_serial_bridge hardware_interface \
  --ros-args \
  -p port:=/dev/ttyUSB0 \
  -p baud_rate:=115200
```

```bash
ros2 run columbus_serial_bridge odometry_publisher
```

The integrated `serial_bridge` is the recommended physical-robot path.

### Start LiDAR

```bash
ros2 run ld08_driver ld08_driver \
  --ros-args \
  -p frame_id:=laser_frame
```

### Start SLAM

```bash
ros2 run slam_toolbox async_slam_toolbox_node \
  --ros-args \
  --params-file \
  ~/columbus_ws/src/columbusmaximus/config/mapper_params_online_async.yaml \
  -p use_sim_time:=false
```

### Start RViz

```bash
rviz2 -d ~/columbus_ws/src/columbusmaximus/rviz/slam.rviz
```

### Start Teleoperation

```bash
ros2 run columbus_teleop teleop_node
```

At this point the robot should be able to:

```
Keyboard
   ↓
/cmd_vel
   ↓
ESP32
   ↓
Motors
   ↓
Wheel Encoders
   ↓
/odom
   ↓
SLAM Toolbox
   ↓
/map
```

### Saving a Physical Map

```bash
mkdir -p ~/columbus_ws/maps

ros2 run nav2_map_server map_saver_cli \
  -f ~/columbus_ws/maps/columbus_map
```

Output: `columbus_map.yaml` and `columbus_map.pgm`.

# Slam map Of Hallway

<img width="924" height="2000" alt="SLAM-MAP" src="https://github.com/user-attachments/assets/636509e4-769c-43f0-b51d-68f28c782f55" />


---

## Diagnostics

```bash
ros2 node list
ros2 topic list
ros2 topic echo /odom --once
ros2 topic echo /scan --once
ros2 topic echo /cmd_vel
```

Check transforms:

```bash
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
```

Generate a TF frame graph:

```bash
ros2 run tf2_tools view_frames
```

Check serial devices and kernel USB messages:

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
dmesg | tail -50
```

---

## Troubleshooting

### ESP32 Does Not Appear

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
dmesg | tail -50
groups
```

If `dialout` is missing:

```bash
sudo usermod -aG dialout $USER
```

Then log out and back in.

### Firmware Does Not Build

```bash
idf.py --version
```

The documented version is ESP-IDF 5.3.1. Build again:

```bash
cd ~/Columbus-Maximus/columbus_firmware
idf.py build
```

### Firmware Does Not Flash

```bash
ls /dev/ttyUSB*
idf.py -p /dev/ttyUSB0 flash
```

Replace `/dev/ttyUSB0` with the actual ESP32 port.

### Serial Bridge Cannot Open the Port

Make sure the ESP-IDF monitor is not running, then:

```bash
ls /dev/ttyUSB*

ros2 run columbus_serial_bridge serial_bridge \
  --ros-args \
  -p port:=/dev/ttyUSB0 \
  -p baud_rate:=115200
```

### `/odom` Is Empty

```bash
ros2 topic echo /odom --once
```

The ESP32 should be transmitting `ODOM,...`. If not, investigate encoder wiring, encoder GPIO configuration, ESP32 firmware, serial connection, and motor/encoder hardware.

> Do not continue to SLAM until odometry is functioning.
> 

### `/scan` Is Empty

```bash
ros2 topic echo /scan --once
ls /dev/ttyUSB*

ros2 run ld08_driver ld08_driver \
  --ros-args \
  -p frame_id:=laser_frame
```

### SLAM Does Not Generate a Map

Verify all four of these:

```bash
ros2 topic echo /scan --once
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
```

SLAM requires `/scan`, `/odom`, `odom → base_link`, and `base_link → laser_frame`.

### RViz Is Blank

For UWB visualization, make sure Fixed Frame is `world`. For robot visualization, make sure the correct TF frames and robot description are being published. For simulation, verify:

```bash
ros2 topic echo /robot_description --once
```

### Gazebo Does Not Spawn the Robot

```bash
ros2 topic echo /robot_description --once
colcon build --packages-select columbusmaximus
source ~/columbus_ws/install/setup.bash
```

If the package is not registering, make sure `resource/columbusmaximus` exists.

---

## Hardware / Software Separation

One of the project’s most important architectural decisions is keeping low-level hardware control separate from ROS 2.

| Layer | Location | Responsibility |
| --- | --- | --- |
| ESP32 | `columbus_firmware/` | Motor control, PID, encoders, odometry, serial |
| ROS 2 | `~/columbus_ws/src/` | Teleop, serial bridge, robot description, LiDAR, SLAM, RViz, Nav2 |
| Simulation | `simulation/` | Gazebo robot, worlds, sensors, and simulated odometry |
| UWB | `uwb/` | UWB serial processing and trilateration |

This separation makes it possible to replace one subsystem without rewriting the entire stack. For example:

```
Physical ESP32
       │
       ▼
Serial Bridge
       │
       ▼
ROS 2
```

can conceptually be replaced during simulation by:

```
Gazebo
   │
   ▼
Differential Drive Plugin
   │
   ▼
ROS 2
```

while the downstream ROS topics remain similar.

---

## Current Status

### Physical Robot

The repository currently documents and supports:

- ESP32 motor firmware
- PID motor control
- Encoder acquisition
- Wheel odometry
- Serial communication
- ROS 2 serial bridge
- LD08 / LDS-02 LiDAR
- ROS 2 teleoperation
- SLAM Toolbox
- RViz2 visualization
- Map generation and saving

### Simulation

- Gazebo robot model
- Differential-drive simulation
- 360° LiDAR simulation
- RViz2 visualization
- Keyboard teleoperation
- SLAM Toolbox mapping
- Map saving
- Nav2 autonomous-navigation demonstration

### UWB

- Four-anchor trilateration
- ROS 2 position publishing
- RViz visualization
- Anchor visualization
- Tag trajectory visualization
- Fake serial-data testing without physical UWB hardware

### Physical Nav2

The physical robot currently has the necessary basic ROS interfaces, but the repository does not yet ship a dedicated, tested Columbus-specific Nav2 configuration.

---

## Design Philosophy

Columbus Maximus intentionally keeps the system modular. The project is designed to make each layer independently visible and testable:

```
Hardware
   ↓
Firmware
   ↓
Serial Communication
   ↓
ROS Drivers
   ↓
Odometry / Sensors
   ↓
SLAM
   ↓
Localization
   ↓
Navigation
```

This makes debugging significantly easier than hiding the entire robot behind a single launch file. The physical-robot workflow therefore starts individual ROS processes manually so each subsystem can be inspected independently.

### Sensor and Localization Strategy

Indoor robot localization is not dependent on one sensor.

**Wheel Odometry**
- Advantages: fast, simple, always locally available
- Limitations: accumulated drift, wheel slip, encoder errors

**LiDAR SLAM**
- Advantages: builds a map, provides spatial constraints, works without GPS
- Limitations: can fail in repetitive environments, depends on LiDAR visibility, sensitive to poor odometry/TF

**UWB**
- Advantages: provides absolute indoor position information, does not require visual features, can correct long-term positional drift
- Limitations: requires infrastructure, anchor geometry affects accuracy, requires serial/UWB hardware integration

The long-term goal of the platform is to provide a foundation for combining these sensing modalities into a more robust indoor localization and navigation system.

### Example End-to-End Pipeline

A complete physical mapping session looks like:

```
                    ┌──────────────┐
                    │   Keyboard   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Teleop     │
                    └──────┬───────┘
                           │
                        /cmd_vel
                           │
                           ▼
                    ┌──────────────┐
                    │ Serial Bridge│
                    └──────┬───────┘
                           │
                       USB Serial
                           │
                           ▼
                    ┌──────────────┐
                    │    ESP32     │
                    │ PID + Motors │
                    │ + Encoders   │
                    └──────┬───────┘
                           │
                         /odom
                           │
                           ▼
                      ┌─────────┐
                      │  SLAM   │◄──── /scan ◄──── LD08
                      │ Toolbox │
                      └────┬────┘
                           │
                         /map
                           │
                           ▼
                       ┌───────┐
                       │ RViz2 │
                       └───────┘
```

For autonomous navigation:

```
Saved Map
   │
   ▼
Localization
   │
   ▼
Nav2
   │
   ├── Global Planner
   ├── Local Controller
   ├── Global Costmap
   ├── Local Costmap
   └── Recovery / Behaviors
   │
   ▼
 /cmd_vel
   │
   ▼
ESP32
   │
   ▼
Motor
```

---
