#include "serial_comm.h"
#include "motor_control.h"
#include "encoder.h"
#include "pid.h"

void app_main(void)
{
    serial_comm_init();
    encoder_init();
    motor_control_init();
    pid_init();

    VelocityCommand command;

    while (1)
    {
        if (serial_comm_receive_command(
                &command,
                portMAX_DELAY))
        {
            pid_set_command_velocity(
                command.linear,
                command.angular
            );
        }
    }
}
