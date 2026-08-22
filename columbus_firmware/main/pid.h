#ifndef PID_H
#define PID_H

#include <stdbool.h>

typedef struct
{
    float left_pwm;
    float right_pwm;

} PidOutput;


void pid_init(void);

void pid_set_command_velocity(
    float linear_velocity,
    float angular_velocity
);

bool pid_get_output(
    PidOutput *output
);

void pid_reset(void);

#endif
