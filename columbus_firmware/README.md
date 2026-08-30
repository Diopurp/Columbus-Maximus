# Columbus Maximus Firmware

Firmware for the **Columbus Maximus** differential-drive mobile robot.

The firmware runs on an **ESP32-WROOM-32** using **ESP-IDF v5.1.7** and handles motor control, encoder feedback, PID-based wheel velocity control, odometry, and USB serial communication with the Raspberry Pi.

---

## Repository Structure

```text
columbus_firmware/
│
├── README.md
│
├── CMakeLists.txt
├── sdkconfig
├── sdkconfig.defaults
│
└── main/
    ├── CMakeLists.txt
    ├── main.c
    │
    ├── serial_comm.c
    ├── serial_comm.h
    │
    ├── motor_control.c
    ├── motor_control.h
    │
    ├── encoder.c
    ├── encoder.h
    │
    ├── pid.c
    └── pid.h
```

### File Responsibilities

| File                | Purpose                                                         |
| ------------------- | --------------------------------------------------------------- |
| `main.c`            | Initializes the firmware modules and starts the required tasks. |
| `serial_comm.c/h`   | Handles USB serial communication and velocity commands.         |
| `motor_control.c/h` | Controls motor direction and PWM output.                        |
| `encoder.c/h`       | Reads quadrature encoders and calculates wheel motion/velocity. |
| `pid.c/h`           | Performs closed-loop wheel velocity control using PID.          |
| `README.md`         | You're reading me. Yes, that's my entire job.                   |

---

## Hardware Interface

| Function              | GPIO |
| --------------------- | ---: |
| Left Motor PWM        |   18 |
| Left Motor Direction  |   19 |
| Right Motor PWM       |   16 |
| Right Motor Direction |   17 |

### PWM Configuration

```text
Frequency  : 20 kHz
Resolution : 8-bit
Range      : 0–255
```

The ESP32 provides the PWM and direction signals to the motor driver, while the motor driver supplies power to the motors.

---

## Encoder Feedback

The motor encoders provide quadrature feedback used to determine:

* Wheel rotation
* Wheel direction
* Wheel displacement
* Wheel velocity

Encoder velocity is fed into the PID controllers for closed-loop wheel-speed regulation.

```text
Target Velocity
       ↓
      PID
       ↓
      PWM
       ↓
     Motor
       ↓
    Encoder
       ↓
Measured Velocity
       └──────→ PID
```

---

## Differential Drive

The robot uses differential-drive kinematics.

For linear velocity `v` and angular velocity `ω`:

```text
left  = v - (ω × L / 2)
right = v + (ω × L / 2)
```

Current wheel base:

```text
L = 0.22 m
```

The resulting wheel velocity targets are passed to the individual PID controllers.

---

## PID Control

Each wheel has an independent velocity PID controller.

```text
error = target velocity - measured velocity
```

The controller calculates the required PWM output based on:

```text
output = Kp × error
       + Ki × integral(error)
       + Kd × derivative(error)
```

The left and right wheels use independently configurable PID gains.

PID tuning should be performed using encoder feedback under the actual robot load.

---

## Odometry

Wheel encoder measurements are used to estimate the robot's:

```text
x
y
θ
```

The firmware calculates wheel displacement and applies differential-drive kinematics to obtain robot odometry.

This odometry is sent to the Raspberry Pi through the USB serial interface and is used by the ROS 2 system.

---

## Communication

The ESP32 communicates with the Raspberry Pi through its **USB connection**.

The development board exposes the ESP32's UART0 through the USB serial interface.

Communication flow:

```text
Raspberry Pi
     ↓ USB
ESP32
     ↓
Motor Control
     ↓
Encoders
     ↓
Odometry
     ↑
Raspberry Pi
```

The serial interface operates at:

```text
115200 baud
```

---

# Setup

## Requirements

Install:

* Ubuntu/Linux
* ESP-IDF
* ESP-IDF Python environment
* ESP32 toolchain
* CMake
* Ninja

The required build tools are installed as part of the ESP-IDF setup.

This project uses:

```text
ESP-IDF v5.1.7
Target: ESP32
```

---

## 1. Setup ESP-IDF

After installing ESP-IDF:

```bash
cd ~/esp/esp-idf
source export.sh
```

Verify:

```bash
idf.py --version
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/Diopurp/Columbus-Maximus.git
```

Navigate to the firmware:

```bash
cd Columbus-Maximus/columbus_firmware
```

---

## 3. Set ESP32 Target

```bash
idf.py set-target esp32
```

---

## 4. Build

```bash
idf.py build
```

---

## 5. Find the ESP32 Serial Port

```bash
ls -l /dev/ttyUSB*
```

For example:

```text
/dev/ttyUSB0
```

Persistent device names can also be checked with:

```bash
ls -l /dev/serial/by-id/
```

---

## 6. Flash

Replace `/dev/ttyUSB0` with the correct ESP32 port:

```bash
idf.py -p /dev/ttyUSB0 flash
```

---

## 7. Monitor

```bash
idf.py -p /dev/ttyUSB0 monitor
```

Exit the monitor with:

```text
Ctrl + ]
```

---

## Serial Port Permissions

If the ESP32 cannot be accessed, check:

```bash
groups
```

The user should normally belong to the `dialout` group.

If required:

```bash
sudo usermod -aG dialout $USER
```

Log out and log back in after adding the group.

---

## Typical Workflow

```bash
cd ~/esp/esp-idf
source export.sh

cd ~/path/to/Columbus-Maximus/columbus_firmware

idf.py build
idf.py -p /dev/ttyUSB0 flash
idf.py -p /dev/ttyUSB0 monitor
```

---

## Important Serial-Port Note

When multiple USB serial devices are connected, such as the ESP32 and LDS-02 LiDAR, `/dev/ttyUSB0` and `/dev/ttyUSB1` may change between boots or reconnects.

Always verify the device before flashing or running the monitor:

```bash
ls -l /dev/serial/by-id/
```

Only one application should access the ESP32's serial port at a time. In particular, the ESP-IDF monitor and the ROS serial bridge should not simultaneously open the same ESP32 port.

---

## Development Flow

```text
ROS 2 / Raspberry Pi
        ↓
    Velocity Command
        ↓
      USB
        ↓
      ESP32
        ↓
Differential Drive
        ↓
   PID Control
        ↓
   Motor Driver
        ↓
      Motors
        ↓
     Encoders
        ↓
     Odometry
        ↓
      USB
        ↓
    Raspberry Pi
```

The firmware provides the real-time low-level control layer connecting the ROS 2 system to the robot's drive hardware.
