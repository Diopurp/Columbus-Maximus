#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

void motor_control_init(void);

void motor_control_set_pwm(
    float left_pwm,
    float right_pwm
);

#endif
