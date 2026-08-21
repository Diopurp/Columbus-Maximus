#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <stdint.h>

void motor_control_init(void);

void motor_control_set_velocity(
    float linear,
    float angular
);

#endif
