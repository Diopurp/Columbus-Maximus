# Motor Control

## Overview

This folder contains the motor control programs developed for the **Columbus Maximus** project.

Each folder inside this directory is an independent **ESP-IDF project**. Every project performs a different motor control task and can be built and tested separately.

For more information about a specific project, please refer to the `README.md` file inside that project's folder.

---

## Hardware Used

The projects in this folder were developed using:

- ESP32 Development Board (38-pin, ESP-WROOM-32)
- SmartElex 15A DC Motor Driver
- Rhino GB37 12V DC Geared Motor

---

## Software Requirements

Before running any project, make sure you have:

- ESP-IDF installed and configured
- A USB cable to connect the ESP32 to your computer

---

## Running a Project

1. Open a terminal.
2. Navigate to the project you want to run.

Example:

```bash
cd motor_control/MotorTest
```

3. Build the project.

```bash
idf.py build
```

4. Flash the ESP32.

```bash
idf.py -p /dev/ttyUSB0 flash
```

5. Open the serial monitor.

```bash
idf.py -p /dev/ttyUSB0 monitor
```

You can also flash the program and start the serial monitor together using:

```bash
idf.py -p /dev/ttyUSB0 flash monitor
```

> **Note:** The serial port may be different on your system. To check the correct port, run:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

---

## Note

These projects are being developed as part of the **Columbus Maximus** robotics project.

The purpose of this folder is to keep different motor control programs organized so they can be tested individually before being integrated into the complete robot.
