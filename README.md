# COLUMBUS MAXIMUS

**ROS 2 Mobile Robot Platform for Indoor SLAM, Navigation, Odometry & UWB Localization**

![ROS 2 Humble](https://img.shields.io/badge/ROS_2-Humble-22314E?style=for-the-badge&logo=ros)  ![ESP32](https://img.shields.io/badge/ESP32-ESP--IDF-0E83CD?style=for-the-badge&logo=espressif) ![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)  ![C/C++](https://img.shields.io/badge/C%2FC%2B%2B-Firmware-00599C?style=for-the-badge&logo=cplusplus&logoColor=white) ![Gazebo](https://img.shields.io/badge/Gazebo-Simulation-orange?style=for-the-badge)

![GitHub stars](https://img.shields.io/github/stars/Diopurp/Columbus-Maximus?style=flat-square) ![GitHub forks](https://img.shields.io/github/forks/Diopurp/Columbus-Maximus?style=flat-square) ![Last commit](https://img.shields.io/github/last-commit/Diopurp/Columbus-Maximus?style=flat-square) ![Repository size](https://img.shields.io/github/repo-size/Diopurp/Columbus-Maximus?style=flat-square)

---

## Project Description

**Columbus Maximus** is a ROS 2 mobile robot platform designed for indoor robotics, autonomous navigation, SLAM, sensor integration, embedded motor control, and localization.

GPS is unreliable or unavailable inside warehouses, factories, laboratories, and other indoor environments. Columbus Maximus explores an alternative approach by combining several sensing and localization technologies:

- **[Wheel odometry](columbus_firmware/README.md#odometry)** for short-term motion estimation.
- **[LiDAR](SLAM%20and%20NAV2/SLAM&NAV2.md#terminal-6--ld08-lidar)** for perception and [SLAM](SLAM%20and%20NAV2/SLAM&NAV2.md#terminal-9--slam-toolbox).
- **[UWB](uwb/README.md)** for absolute indoor position estimation.
- **[ROS 2](SLAM%20and%20NAV2/SLAM&NAV2.md#3-installation)** as the communication and robotics middleware.
- **[ESP32 firmware](columbus_firmware/README.md)** for low-level motor control, encoder acquisition, PID control, and serial communication.
- **RViz2** for visualization and debugging ([SLAM](SLAM%20and%20NAV2/SLAM&NAV2.md#terminal-10--rviz), [UWB](uwb/README.md#visualizing-in-rviz)).
- **[Gazebo](simulation/README.md)** for simulation and algorithm development.
- **[Nav2](SLAM%20and%20NAV2/SLAM&NAV2.md#7-nav2-status)** for autonomous navigation experiments ([simulation demo](simulation/README.md#nav2-implementation)).

The system is intentionally modular so that the [embedded hardware](columbus_firmware/README.md), ROS 2 drivers, robot description, [SLAM](SLAM%20and%20NAV2/SLAM&NAV2.md), [teleoperation](SLAM%20and%20NAV2/SLAM&NAV2.md#terminal-11--teleoperation), [simulation](simulation/README.md), and [UWB localization](uwb/README.md) can be developed and tested independently.

---

## Core Idea

GPS does not work indoors, and no single indoor sensor is reliable on its own. Columbus Maximus is built around combining three complementary sources of position information:

| Source | Strengths | Limitations |
| --- | --- | --- |
| [**Wheel odometry**](columbus_firmware/README.md#odometry) | Fast, simple, always locally available | Accumulated drift, wheel slip, encoder errors |
| [**LiDAR SLAM**](SLAM%20and%20NAV2/SLAM&NAV2.md#terminal-9--slam-toolbox) | Builds a map, provides spatial constraints, works without GPS | Can fail in repetitive environments, depends on LiDAR visibility, sensitive to poor odometry/TF |
| [**UWB**](uwb/README.md) | Absolute indoor position, needs no visual features, can correct long-term drift | Needs infrastructure, anchor geometry affects accuracy, requires UWB hardware integration |

The long-term goal is a platform that fuses these sources into a more robust indoor localization and navigation system. UWB currently runs as an independent tracker alongside the odometry + LiDAR SLAM pipeline.

To keep every layer visible and testable, the project separates the [ESP32 firmware from the ROS 2 software](SLAM%20and%20NAV2/SLAM&NAV2.md#12-hardware--software-separation) and brings the physical robot up node by node with `ros2 run` instead of one large launch file ([design notes](SLAM%20and%20NAV2/SLAM&NAV2.md#13-design-notes)).

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

The physical robot uses an ESP32 as the low-level controller ([firmware guide](columbus_firmware/README.md)). The ROS 2 computer communicates with the ESP32 over USB serial while independently receiving LiDAR measurements ([full bring-up steps](SLAM%20and%20NAV2/SLAM&NAV2.md#6-running-the-robot)).

The simulation replaces the physical hardware with Gazebo plugins while keeping the ROS 2 interfaces similar ([simulation guide](simulation/README.md)).

---

## Hardware

The physical robot is a differential-drive platform.

**Main components**

- **ESP32** — low-level controller for motors, encoders, PID and serial ([firmware](columbus_firmware/README.md))
- **Two driven wheels** with quadrature encoders, powered through **motor drivers** that take PWM + direction signals from the ESP32
- **LD08 / LDS-02 2D LiDAR** — `/scan` for SLAM ([bring-up](SLAM%20and%20NAV2/SLAM&NAV2.md#terminal-6--ld08-lidar))
- **USB serial** links from the ROS 2 computer to the ESP32 and to the LiDAR
- **Optional UWB tag and four anchors** ([UWB tutorial](uwb/README.md), [datasheets](uwb/datasheets/))
- **Chassis** — STL models for the base plates, upper plates and spacers in [`Chassis Design/`](Chassis%20Design/)

<img width="400" alt="Assembled Columbus Maximus chassis" src="https://github.com/user-attachments/assets/d6ff7ac7-5ee0-4f5b-845f-976b280e6ca4" />

**Hardware configuration** (as set in the [firmware](columbus_firmware/README.md#hardware-interface); recalibrate if the physical robot changes)

| Parameter | Value |
| --- | --- |
| Left motor PWM / direction | GPIO 18 / GPIO 19 |
| Right motor PWM / direction | GPIO 16 / GPIO 17 |
| PWM | 20 kHz, 8-bit (0–255) |
| Left encoder A / B | GPIO 4 / GPIO 21 |
| Right encoder A / B | GPIO 22 / GPIO 23 |
| Wheel diameter | 0.11 m |
| Wheel base | 0.22 m |
| Encoder counts per revolution | 2925 |
| ESP32 ↔ ROS 2 serial | 115200 baud over USB |

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
├── Chassis Design/
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

> **Workspace rule:** `columbus_firmware/` is an ESP-IDF project, **not** a ROS 2 package — never copy it into `~/columbus_ws/src/`. That workspace holds only the four ROS packages (`columbusmaximus`, `ld08_driver`, `columbus_serial_bridge`, `columbus_teleop`). Full setup steps: [SLAM & Nav2 guide → Repository Structure](SLAM%20and%20NAV2/SLAM&NAV2.md#1-repository-structure).

---

## Guides & Tutorials

### SLAM & Nav2 — Physical Robot Guide

Full guide: [`SLAM and NAV2/SLAM&NAV2.md`](SLAM%20and%20NAV2/SLAM&NAV2.md)

1. [Repository Structure](SLAM%20and%20NAV2/SLAM&NAV2.md#1-repository-structure)
2. [Requirements](SLAM%20and%20NAV2/SLAM&NAV2.md#2-requirements)
3. [Installation](SLAM%20and%20NAV2/SLAM&NAV2.md#3-installation)
4. [ESP32 Firmware](SLAM%20and%20NAV2/SLAM&NAV2.md#4-esp32-firmware)
5. [Firmware Reference](SLAM%20and%20NAV2/SLAM&NAV2.md#5-firmware-reference)
6. [Running the Robot](SLAM%20and%20NAV2/SLAM&NAV2.md#6-running-the-robot)
7. [Nav2 Status](SLAM%20and%20NAV2/SLAM&NAV2.md#7-nav2-status)
8. [System Architecture](SLAM%20and%20NAV2/SLAM&NAV2.md#8-system-architecture)
9. [Quick Reference — Startup Checklist](SLAM%20and%20NAV2/SLAM&NAV2.md#9-quick-reference--startup-checklist)
10. [Diagnostics](SLAM%20and%20NAV2/SLAM&NAV2.md#10-diagnostics)
11. [Troubleshooting](SLAM%20and%20NAV2/SLAM&NAV2.md#11-troubleshooting)
12. [Hardware / Software Separation](SLAM%20and%20NAV2/SLAM&NAV2.md#12-hardware--software-separation)
13. [Design Notes](SLAM%20and%20NAV2/SLAM&NAV2.md#13-design-notes)

*Serial bridge and wheel odometry, LiDAR bring-up, teleoperation and map saving are all covered step by step in [Section 6](SLAM%20and%20NAV2/SLAM&NAV2.md#6-running-the-robot).*

### UWB Localization Tutorial

Full tutorial: [`uwb/README.md`](uwb/README.md)

- [Repository structure](uwb/README.md#repository-structure)
- [Prerequisites](uwb/README.md#prerequisites)
- [Setup — cloning and building](uwb/README.md#setup--cloning-and-building)
- [Serial port permissions](uwb/README.md#serial-port-permissions)
  - [Option A — quick fix (temporary)](uwb/README.md#option-a--quick-fix-temporary)
  - [Option B — permanent fix (recommended)](uwb/README.md#option-b--permanent-fix-recommended)
- [Running the node](uwb/README.md#running-the-node)
- [Visualizing in RViz](uwb/README.md#visualizing-in-rviz)
- [Testing without physical hardware](uwb/README.md#testing-without-physical-hardware)
- [Troubleshooting quick reference](uwb/README.md#troubleshooting-quick-reference)

### Also in this repository

- [**ESP32 Firmware**](columbus_firmware/README.md) — motor control, encoder feedback, PID, odometry, build/flash workflow
- [**Gazebo Simulation**](simulation/README.md) — simulated robot, SLAM mapping and Nav2 demos

  ---
### OUR TEAM
  - Tejoshnanda Chilakalapudi - tejoshnanda.chilakalapudi@gmail.com
  - Durva Sunil Sohani - sohanidurva@gmail.com
  - Manas Hanwat - manashanwat@gmail.com
### Mentors 
  - Siddharth Mishra
  - Vedant Malkar
---
SRA - Society of Robotics
