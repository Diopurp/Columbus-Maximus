#include "serial_comm.h"
#include "motor_control.h"

void app_main(void)
{
    serial_comm_init();
    motor_control_init();

    VelocityCommand command;

    while (1)
    {
        if (serial_comm_receive_command(
                &command,
                portMAX_DELAY))
        {
            motor_control_set_velocity(
                command.linear,
                command.angular
            );
        }
    }
}
