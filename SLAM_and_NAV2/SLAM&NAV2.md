# IRL SLAM AND NAV2 GUIDE

# Columbus Maximus — IRL SLAM & Nav2

![ROS](https://img.shields.io/badge/ros-%230A0FF9.svg?style=for-the-badge&logo=ros&logoColor=white)

![Gazebo](https://img.shields.io/badge/gazebo-%23F58113.svg?style=for-the-badge&logo=gazebo&logoColor=white)

[ESP32](https://img.shields.io/badge/esp32-E7352C?style=for-the-badge&logo=espressif&logoColor=white)

[Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

![C](https://img.shields.io/badge/c-%2300599C.svg?style=for-the-badge&logo=c&logoColor=white)

![XML](https://img.shields.io/badge/xml-%23005FAD.svg?style=for-the-badge&logo=xml&logoColor=white)

Columbus Maximus is a ROS 2 mobile robot platform using:

- ESP32 motor and encoder firmware
- Wheel odometry
- LD08 LiDAR
- LiDAR-based SLAM
- ROS 2 teleoperation
- Nav2 for autonomous navigation

This README covers the **real physical robot**. For the Gazebo/RViz simulation, see [`simulation/`](simulation/).

> **Note:** The ESP32 firmware is required for the physical robot. The ROS 2 serial bridge does **not** replace it — the firmware runs on the ESP32 itself and handles motor control, encoder reading, odometry calculation, and serial communication with the ROS computer.
> 

---

## Table of Contents

1. [Repository Structure](about:blank#1-repository-structure)
2. [Requirements](about:blank#2-requirements)
3. [Installation](about:blank#3-installation)
4. [ESP32 Firmware](about:blank#4-esp32-firmware)
5. [Firmware Reference](about:blank#5-firmware-reference)
6. [Running the Robot](about:blank#6-running-the-robot)
7. [Nav2 Status](about:blank#7-nav2-status)
8. [System Architecture](about:blank#8-system-architecture)
9. [Quick Reference — Startup Checklist](about:blank#9-quick-reference--startup-checklist)
10. [Diagnostics](about:blank#10-diagnostics)
11. [Troubleshooting](about:blank#11-troubleshooting)
12. [Hardware / Software Separation](about:blank#12-hardware--software-separation)
13. [Design Notes](about:blank#13-design-notes)

---

## 1. Repository Structure

The repository is intentionally split into the ESP32 firmware and the ROS 2 software.

```
Columbus-Maximus/
│
├── columbus_firmware/                 # ESP32 firmware — NOT a ROS package
│   ├── main/
│   │   ├── main.c
│   │   ├── serial_comm.c / .h
│   │   ├── motor_control.c / .h
│   │   ├── encoder.c / .h
│   │   └── pid.c / .h
│   ├── CMakeLists.txt
│   ├── sdkconfig
│   └── COLCON_IGNORE
│
├── SLAM and NAV2/
│   ├── columbusmaximus/
│   └── lidar_driver/
│       └── ld08_driver/
│
├── Teleop and Odometry/
│   ├── columbus_serial_bridge/
│   └── columbus_teleop/
│
├── Meshes/
├── simulation/
├── uwb/
├── .gitignore
└── README.md
```

**`columbus_firmware/` must stay at the repository root.** Do not copy it into `columbus_ws/src/` — the ROS 2 workspace should only ever contain ROS packages:

```
~/columbus_ws/src/
├── columbusmaximus/
├── ld08_driver/
├── columbus_serial_bridge/
└── columbus_teleop/
```

The firmware remains separately at:

```
~/Columbus-Maximus/columbus_firmware/
```

---

## 2. Requirements

| Component | Version / Notes |
| --- | --- |
| OS | Ubuntu 22.04 |
| ROS 2 | Humble |
| ESP-IDF | 5.3.1 (the committed `sdkconfig` was generated with this version) |
| MCU | ESP32 |
| LiDAR | LD08 / LDS-02 |
| Connections | USB to ESP32, USB to LiDAR |

---

## 3. Installation

### Terminal 1 — Clone the repository

```bash
cd ~
git clone https://github.com/Diopurp/Columbus-Maximus.git
cd ~/Columbus-Maximus
tree -L 2
```

You should see:

```
columbus_firmware/
SLAM and NAV2/
Teleop and Odometry/
Meshes/
simulation/
uwb/
README.md
```

### Terminal 2 — Install and source ROS 2 Humble

Install Ubuntu 22.04 first, then install ROS 2 Humble following the [official installation guide](https://docs.ros.org/en/humble/Installation.html). Once installed:

```bash
source /opt/ros/humble/setup.bash
ros2 --help
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Terminal 3 — Development tools

```bash
sudo apt update
sudo apt install -y git build-essential cmake python3-pip python3-colcon-common-extensions python3-rosdep python3-vcstool tree
```

### Terminal 4 — ROS packages and serial/LiDAR dependencies

```bash
sudo apt install -y ros-humble-xacro ros-humble-robot-state-publisher ros-humble-joint-state-publisher-gui ros-humble-rviz2 ros-humble-rclpy ros-humble-geometry-msgs ros-humble-nav-msgs ros-humble-tf2-ros ros-humble-std-msgs ros-humble-sensor-msgs ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-nav2-map-server ros-humble-nav2-amcl

sudo apt install -y python3-serial libboost-system-dev libudev-dev
```

### Terminal 5 — USB permissions

The ESP32 and LiDAR appear as USB serial devices, which require the `dialout` group.

```bash
sudo usermod -aG dialout $USER
```

Log out and back in, then confirm:

```bash
groups
```

`dialout` should appear in the list.

### Terminal 6 — Create the workspace and copy in the ROS packages

The firmware must **not** be copied into this workspace.

```bash
mkdir -p ~/columbus_ws/src

# Robot description, SLAM config, and Nav2 assets
cp -r ~/Columbus-Maximus/"SLAM and NAV2"/columbusmaximus ~/columbus_ws/src/

# LD08 LiDAR driver
cp -r ~/Columbus-Maximus/"SLAM and NAV2"/lidar_driver/ld08_driver ~/columbus_ws/src/

# ESP32 serial bridge
cp -r ~/Columbus-Maximus/"Teleop and Odometry"/columbus_serial_bridge ~/columbus_ws/src/

# Teleoperation
cp -r ~/Columbus-Maximus/"Teleop and Odometry"/columbus_teleop ~/columbus_ws/src/

tree ~/columbus_ws/src -L 2
```

Expected:

```
~/columbus_ws/src/
├── columbus_serial_bridge/
├── columbus_teleop/
├── columbusmaximus/
└── ld08_driver/
```

### Terminal 7 — Install workspace dependencies

```bash
source /opt/ros/humble/setup.bash
sudo rosdep init      # skip if it says already initialized
rosdep update
cd ~/columbus_ws
rosdep install --from-paths src --ignore-src -r -y
```

### Terminal 8 — Build the workspace

```bash
source /opt/ros/humble/setup.bash
cd ~/columbus_ws
colcon build --symlink-install

source ~/columbus_ws/install/setup.bash
echo "source ~/columbus_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc

ros2 pkg list | grep -E "columbus|ld08"
```

Expected:

```
columbus_serial_bridge
columbus_teleop
columbusmaximus
ld08_driver
```

---

## 4. ESP32 Firmware

The firmware is an ESP-IDF project. `main.c` initializes serial communication, the encoder system, motor control, and the PID controller, then runs an odometry task.

### Terminal 1 — Download and install ESP-IDF 5.3.1

```bash
cd ~
git clone -b v5.3.1 --recursive https://github.com/espressif/esp-idf.git
cd ~/esp-idf
./install.sh esp32
source ~/esp-idf/export.sh
idf.py --version

echo "source ~/esp-idf/export.sh" >> ~/.bashrc
source ~/.bashrc
```

### Terminal 2 — Build the firmware

```bash
source ~/esp-idf/export.sh
cd ~/Columbus-Maximus/columbus_firmware
idf.py build
```

Do not put this project into `~/columbus_ws/src`.

### Terminal 3 — Find the ESP32’s serial port

Connect the ESP32 over USB, then:

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
dmesg | tail -50
```

The example port used throughout this README is `/dev/ttyUSB0` — replace it with whatever your system assigns.

### Terminal 4 — Flash the firmware

**Make sure the robot’s wheels are safely off the ground or otherwise secured for the first firmware test.**

```bash
source ~/esp-idf/export.sh
cd ~/Columbus-Maximus/columbus_firmware
idf.py -p /dev/ttyUSB0 flash
```

`flash` rebuilds the project if necessary before flashing.

### Terminal 5 — Monitor the ESP32 (optional)

```bash
source ~/esp-idf/export.sh
cd ~/Columbus-Maximus/columbus_firmware
idf.py -p /dev/ttyUSB0 monitor
```

Exit with `Ctrl + ]`.

> Do not leave the monitor connected while starting the ROS serial bridge — both need exclusive access to the same serial port.
> 

---

## 5. Firmware Reference

### Serial Protocol

Baud rate: `115200`

| Direction | Format | Example |
| --- | --- | --- |
| ROS → ESP32 | `VEL,<linear>,<angular>` | `VEL,0.2,0.0` |
| ESP32 → ROS | `ODOM,<x>,<y>,<yaw>,<linear_velocity>,<angular_velocity>` | `ODOM,0.120000,0.030000,0.020000,0.100000,0.010000` |

The ROS serial bridge speaks the same protocol.

### Encoder Configuration (`encoder.c`)

```
Left encoder A  = GPIO 4
Left encoder B  = GPIO 21
Right encoder A = GPIO 22
Right encoder B = GPIO 23

Wheel diameter = 0.11 m
Wheel base     = 0.22 m
Counts/rev     = 2925
```

If the physical robot’s hardware changes, recalibrate these values.

### Motor Configuration

The ROS computer never drives the motor GPIOs directly — it only sends velocity commands over serial, and the firmware’s `motor_control.c` / `pid.c` handle the rest:

```
ROS /cmd_vel → serial bridge → USB serial → ESP32 firmware → PID + motor control → motors
```

---

## 6. Running the Robot

Every node below is started manually with `ros2 run` — see [Design Notes](about:blank#13-design-notes) for why this guide avoids launch files. Each terminal needs:

```bash
source /opt/ros/humble/setup.bash
source ~/columbus_ws/install/setup.bash
```

before its own command — omitted below for brevity.

### Terminal 1 — Identify the serial devices

Connect both the ESP32 and the LD08 LiDAR, then:

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
```

Example: `/dev/ttyUSB0` (ESP32), `/dev/ttyUSB1` (LiDAR). Confirm which is which before continuing.

### Terminal 2 — Generate the URDF

```bash
ros2 run xacro xacro ~/columbus_ws/src/columbusmaximus/description/robot.urdf.xacro > /tmp/columbus_robot.urdf
ls -lh /tmp/columbus_robot.urdf
```

### Terminal 3 — Robot state publisher

```bash
ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(cat /tmp/columbus_robot.urdf)"
```

Keep running.

### Terminal 4 — ESP32 serial bridge

The `columbus_serial_bridge` package installs three executables: `serial_bridge`, `hardware_interface`, and `odometry_publisher`. The recommended path for the real robot is the integrated `serial_bridge` node:

```bash
ros2 run columbus_serial_bridge serial_bridge --ros-args -p port:=/dev/ttyUSB0 -p baud_rate:=115200
```

Replace `/dev/ttyUSB0` with the ESP32’s port. This node receives `/cmd_vel`, sends `VEL,...` to the ESP32, receives `ODOM,...` back, publishes `/odom`, and broadcasts `odom → base_link`.

- Alternative — split nodes
    
    If you’d rather run the hardware interface and odometry publishing as two separate nodes instead of the integrated bridge:
    
    ```bash
    ros2 run columbus_serial_bridge hardware_interface --ros-args -p port:=/dev/ttyUSB0 -p baud_rate:=115200
    ros2 run columbus_serial_bridge odometry_publisher
    ```
    

Keep running.

### Terminal 5 — Check odometry

```bash
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
```

If `/odom` doesn’t update when the wheels move, stop and fix the ESP32/serial/encoder side before starting SLAM.

### Terminal 6 — LD08 LiDAR

```bash
ros2 run ld08_driver ld08_driver --ros-args -p frame_id:=laser_frame
```

Keep running. If your specific LD08 unit needs different serial settings, use whatever parameters the driver in this repo exposes.

### Terminal 7 — Check the LiDAR

```bash
ros2 topic echo /scan --once
```

The message should show `frame_id: laser_frame`.

### Terminal 8 — Check the LiDAR TF

```bash
ros2 run tf2_ros tf2_echo base_link laser_frame
```

SLAM needs both `odom → base_link` and `base_link → laser_frame` to be valid.

### Terminal 9 — SLAM Toolbox

Uses `columbusmaximus/config/mapper_params_online_async.yaml` (map frame `map`, odom frame `odom`, base frame `base_link`, scan topic `/scan`):

```bash
ros2 run slam_toolbox async_slam_toolbox_node --ros-args --params-file ~/columbus_ws/src/columbusmaximus/config/mapper_params_online_async.yaml -p use_sim_time:=false
```

Keep running.

### Terminal 10 — RViz

```bash
rviz2 -d ~/columbus_ws/src/columbusmaximus/rviz/slam.rviz
```

You should see the robot model, LiDAR scan, TF tree, and the growing map.

### Terminal 11 — Teleoperation

```bash
ros2 run columbus_teleop teleop_node
```

```
w / s   forward / backward
a / d   rotate left / right
SPACE   stop
q / z   increase / decrease both speeds
e / c   increase / decrease linear speed
r / f   increase / decrease angular speed
CTRL+C  exit
```

Start at low speed for physical testing.

### Terminal 12 — Check `/cmd_vel`

```bash
ros2 topic echo /cmd_vel
```

Should show `geometry_msgs/msg/Twist` messages while teleop is active:

```
teleop_node → /cmd_vel → serial_bridge → USB serial → ESP32 firmware → motor control
```

### Building the Map

With Terminals 3, 4, 6, 9, 10, and 11 all running, drive the robot slowly around the environment and watch `/map` build in RViz. Confirm:

```
/scan               is publishing
/odom               is publishing
odom → base_link    exists
base_link → laser_frame  exists
```

Revisit previously mapped areas when possible so SLAM can perform loop closure.

### Terminal 13 — Save the map

Stop the robot with `SPACE`, then:

```bash
mkdir -p ~/columbus_ws/maps
ros2 run nav2_map_server map_saver_cli -f ~/columbus_ws/maps/columbus_map
```

Produces:

```
~/columbus_ws/maps/columbus_map.yaml
~/columbus_ws/maps/columbus_map.pgm
```

---

## 7. Nav2 Status

Nav2 is installed as part of the ROS dependencies, but **this repository does not yet ship a Columbus-specific Nav2 parameter file.** Having the Nav2 packages installed does not mean the robot is ready for autonomous navigation.

The robot already provides the interfaces Nav2 needs:

```
/scan, /odom, /cmd_vel        (from the robot)
/map, map → odom              (from SLAM)
```

Still needed before Nav2 is usable:

```
controller, planner, local costmap, global costmap,
robot footprint, inflation, obstacle layers,
velocity limits, AMCL/localization, behavior/recovery configuration
```

Once a tested Columbus-specific configuration exists, Nav2 can also be started manually, node-by-node, following the same pattern used in [Section 6](about:blank#6-running-the-robot).

---

## 8. System Architecture

```
                         ┌─────────────────┐
                         │      ESP32      │
                         │  motor_control  │
                         │  PID            │
                         │  encoders       │
                         │  serial_comm    │
                         └────────┬────────┘
                                  │ USB Serial
                                  v
                    ┌─────────────────────────┐
                    │  columbus_serial_bridge  │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              v                                   v
           /odom                              /cmd_vel
              │                                   ^
              v                                   │
          SLAM Toolbox                       teleop_node
              │
              v
            /map

LD08 → ld08_driver → /scan → SLAM Toolbox

robot.urdf.xacro → robot_state_publisher → TF
```

Full physical-system view:

```
                 PC                                  ESP32
      ┌────────────────────┐                 ┌────────────────┐
      │   ROS 2 Humble      │   USB Serial    │  Motor Control  │   Motor
      │  Teleop             │ ──────────────> │  PID            │ ──Driver──> Motors
      │  Serial Bridge      │ <────────────── │  Encoders       │
      │  LiDAR Driver       │                 │  Odometry       │
      │  SLAM / Nav2        │                 └────────────────┘
      └────────────────────┘
```

---

## 9. Quick Reference — Startup Checklist

A normal SLAM/manual-driving session needs the following terminals from [Section 6](about:blank#6-running-the-robot) running simultaneously:

| Terminal | Node | Must stay running? |
| --- | --- | --- |
| 3 | `robot_state_publisher` | Yes |
| 4 | `columbus_serial_bridge serial_bridge` | Yes |
| 6 | `ld08_driver` | Yes |
| 9 | `slam_toolbox async_slam_toolbox_node` | Yes |
| 10 | `rviz2` | Optional (viewing only) |
| 11 | `columbus_teleop teleop_node` | Yes, while driving |

Terminals 1, 2, 5, 7, 8, and 12 are one-off checks and don’t need to stay open. Terminal 13 (`map_saver_cli`) is run once at the end.

---

## 10. Diagnostics

```bash
ros2 node list
ros2 topic list
ros2 topic echo /odom --once
ros2 topic echo /scan --once
ros2 topic echo /cmd_vel
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
ros2 run tf2_tools view_frames
```

---

## 11. Troubleshooting

**ESP32 does not appear**

```bash
ls /dev/ttyUSB*
ls /dev/ttyACM*
dmesg | tail -50
groups                          # confirm 'dialout' is present
sudo usermod -aG dialout $USER  # if missing, then log out/in
```

**Firmware will not build**

```bash
idf.py --version   # confirm ESP-IDF 5.3.1
cd ~/Columbus-Maximus/columbus_firmware
idf.py build
```

**Firmware will not flash**

```bash
ls /dev/ttyUSB*
idf.py -p /dev/ttyUSB0 flash   # use the actual ESP32 port
```

**ROS serial bridge cannot open the port**

Make sure the ESP-IDF monitor isn’t running, then:

```bash
ls /dev/ttyUSB*
ros2 run columbus_serial_bridge serial_bridge --ros-args -p port:=/dev/ttyUSB0 -p baud_rate:=115200
```

**`/odom` is empty**

```bash
ros2 topic echo /odom --once
```

Check that the ESP32 is sending `ODOM,...` over serial — this data comes from the physical wheel encoders.

**`/scan` is empty**

```bash
ros2 topic echo /scan --once
ls /dev/ttyUSB*
ros2 run ld08_driver ld08_driver --ros-args -p frame_id:=laser_frame
```

**SLAM does not generate a map**

Check all four of the following are valid:

```bash
ros2 topic echo /scan --once
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
```

---

## 12. Hardware / Software Separation

| Layer | Location | Responsible for |
| --- | --- | --- |
| ESP32 | `Columbus-Maximus/columbus_firmware/` | Motor control, PID, encoder reading, wheel odometry, serial communication |
| ROS 2 | `~/columbus_ws/src/` | Teleoperation, serial bridge, robot description, LiDAR, SLAM, RViz, Nav2 |

---

## 13. Design Notes

This guide intentionally avoids `ros2 launch ...` — every ROS process is started manually with `ros2 run ...`, and the ESP32 firmware is built and flashed independently with `idf.py build` / `idf.py flash`, kept entirely outside the ROS workspace’s `src/` directory. This keeps every moving part visible and easy to restart individually while bringing up the real robot.