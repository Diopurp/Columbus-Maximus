#include "serial_comm.h"
#include "motor_control.h"
#include "encoder.h"
#include "pid.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define ODOMETRY_PERIOD_MS 20

static void odometry_task(void *arg)
{
    (void)arg;

    EncoderData encoder_data;
    OdometryData odometry;

    TickType_t last_wake_time =
        xTaskGetTickCount();

    while (1)
    {
        if (encoder_get_data(&encoder_data))
        {
            odometry.x =
                encoder_data.x;

            odometry.y =
                encoder_data.y;

            odometry.yaw =
                encoder_data.theta;

            odometry.linear_velocity =
                encoder_data.linear_velocity;

            odometry.angular_velocity =
                encoder_data.angular_velocity;

            serial_comm_send_odometry(
                &odometry
            );
        }

        vTaskDelayUntil(
            &last_wake_time,
            pdMS_TO_TICKS(
                ODOMETRY_PERIOD_MS
            )
        );
    }
}

void app_main(void)
{
    serial_comm_init();
    encoder_init();
    motor_control_init();
    pid_init();

    xTaskCreate(
        odometry_task,
        "odometry_task",
        4096,
        NULL,
        9,
        NULL
    );

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

