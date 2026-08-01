# Motor Test

## Overview

This project is used to test the basic functionality of two DC motors using the ESP32.

It allows you to verify that the motor driver, motor connections, PWM output, and direction control are working correctly before integrating the motors into a larger project.

For instructions on building, flashing, and monitoring the project, please refer to the `README.md` in the `motor_control` folder.

---

## Hardware Used

This project was developed using:

- ESP32 Development Board (38-pin, ESP-WROOM-32)
- SmartElex 15A DC Motor Driver
- Rhino GB37 12V DC Geared Motor

---

## Changing the Motor Speed

The motor speed is controlled using the PWM duty cycle.

To change the speed, open `main/main.c` and modify the `.duty` values inside the motor channel configurations.

Example:

```c
.duty = 255
```

- `255` = Maximum speed
- `0` = Motor stopped

The left and right motors can be given different duty cycle values for testing.

---

## Changing the Motor Direction

The motor direction is controlled using the direction pins.

To change the direction, modify the following lines in `main/main.c`:

```c
gpio_set_level(LEFT_DIR_PIN, 1);
gpio_set_level(RIGHT_DIR_PIN, 1);
```

Changing the value from `1` to `0` reverses the direction of rotation.

> The actual direction (forward or reverse) depends on how the motor is connected to the motor driver.

---

## Uses

You can use this project to:

- Test motor connections.
- Verify motor direction.
- Test different motor speeds.
- Check that the motor driver is working correctly.
- Experiment with PWM values before using them in other projects.

Feel free to modify the code according to your own requirements.
