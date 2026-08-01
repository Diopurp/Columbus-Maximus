# Keyboard Teleoperation

## Overview

This project allows the motors to be controlled using keyboard inputs.

The program receives commands from the keyboard through the serial monitor and controls the motor direction and speed accordingly. It is mainly intended for testing the motor driver and verifying that the motors respond correctly to different commands.

---

## Hardware Used

This project was developed using:

- ESP32 Development Board (38-pin, ESP-WROOM-32)
- SmartElex 15A DC Motor Driver
- Rhino GB37 12V DC Geared Motor

---

## Software Requirements

Before running this project, make sure you have:

- ESP-IDF installed and configured
- A USB cable to connect the ESP32 to your computer

---

## Running the Project

1. Open a terminal.

2. Navigate to the project folder.

```bash
cd motor_control/KeyboardTeleop
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

You can also flash the project and start the serial monitor together using:

```bash
idf.py -p /dev/ttyUSB0 flash monitor
```

> **Note:** The serial port may be different on your system. To check the correct port, run:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

---

## Controls

Once the serial monitor is open, enter the supported keyboard commands to control the motor.

The available commands are implemented in `main/main.c`. You can modify them or add your own commands as required.

---

## Uses

You can use this project to:

- Test your motor connections.
- Check if the motor is rotating in the correct direction.
- Verify that keyboard commands are working correctly.
- Try out new motor control ideas before using them in your main project.

Feel free to modify the code according to your own requirements.
