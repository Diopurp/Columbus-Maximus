#ifndef SERIAL_COMM_H
#define SERIAL_COMM_H

#include <stdbool.h>

#include "freertos/FreeRTOS.h"

typedef struct
{
    float linear;
    float angular;
} VelocityCommand;

typedef struct
{
    float x;
    float y;
    float yaw;
    float linear_velocity;
    float angular_velocity;
} OdometryData;

void serial_comm_init(void);

bool serial_comm_receive_command(
    VelocityCommand *command,
    TickType_t timeout
);

bool serial_comm_send_odometry(
    const OdometryData *odometry
);

#endif
