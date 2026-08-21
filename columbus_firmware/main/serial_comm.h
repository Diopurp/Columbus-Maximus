
#ifndef SERIAL_COMM_H
#define SERIAL_COMM_H

#include <stdbool.h>
#include "freertos/FreeRTOS.h"

/*
 a decoded velocity command received from the Raspberry Pi.
 linear  -> m/s
 angular -> rad/s
 */
typedef struct
{
    float linear;
    float angular;
} VelocityCommand;


/*
 initialize the UART interface and start
 the serial receiver task.
 */
void serial_comm_init(void);


/*
 this function checks whether velocity command was received or not and then 
 gives back a respective boolean value accordingly
 */
bool serial_comm_receive_command(
    VelocityCommand *command,
    TickType_t timeout
);

#endif
