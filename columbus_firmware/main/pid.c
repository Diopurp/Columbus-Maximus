#include "pid.h"
#include "encoder.h"
#include "motor_control.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_timer.h"


#define WHEEL_BASE_M        0.22f

#define PID_PERIOD_MS       10

#define PWM_MIN             0.0f
#define PWM_MAX             255.0f

#define MAX_WHEEL_SPEED_MPS 0.62f

#define INTEGRAL_LIMIT      1.0f


#define LEFT_KP             2000.0f
#define LEFT_KI             10.0f
#define LEFT_KD             0.0f

#define RIGHT_KP            1950.0f
#define RIGHT_KI            10.0f
#define RIGHT_KD             0.0f


typedef struct
{
    float kp;
    float ki;
    float kd;

    float integral;
    float previous_error;

} PIDController;


static PIDController left_pid =
{
    .kp = LEFT_KP,
    .ki = LEFT_KI,
    .kd = LEFT_KD,

    .integral = 0.0f,
    .previous_error = 0.0f
};


static PIDController right_pid =
{
    .kp = RIGHT_KP,
    .ki = RIGHT_KI,
    .kd = RIGHT_KD,

    .integral = 0.0f,
    .previous_error = 0.0f
};


static float command_linear_velocity = 0.0f;
static float command_angular_velocity = 0.0f;


static PidOutput pid_output =
{
    .left_pwm = 0.0f,
    .right_pwm = 0.0f
};


static portMUX_TYPE pid_spinlock =
    portMUX_INITIALIZER_UNLOCKED;


static float clamp(
    float value,
    float minimum,
    float maximum
)
{
    if (value < minimum)
    {
        return minimum;
    }

    if (value > maximum)
    {
        return maximum;
    }

    return value;
}


static float calculate_pid(
    PIDController *pid,
    float target,
    float actual,
    float dt
)
{
    float error;
    float derivative;
    float output;


    error =
        target - actual;


    pid->integral +=
        error * dt;


    pid->integral =
        clamp(
            pid->integral,
            -INTEGRAL_LIMIT,
            INTEGRAL_LIMIT
        );


    derivative =
        (error - pid->previous_error)
        / dt;


    output =
        (pid->kp * error)
        +
        (pid->ki * pid->integral)
        +
        (pid->kd * derivative);


    pid->previous_error =
        error;


    return output;
}


static void pid_task(void *arg)
{
    (void)arg;


    int64_t previous_time_us =
        esp_timer_get_time();


    TickType_t last_wake_time =
        xTaskGetTickCount();


    while (1)
    {
        int64_t current_time_us;

        float dt;

        EncoderData encoder_data;

        float linear_command;
        float angular_command;

        float left_target;
        float right_target;

        float left_pwm;
        float right_pwm;


        current_time_us =
            esp_timer_get_time();


        dt =
            (float)(
                current_time_us -
                previous_time_us
            ) / 1000000.0f;


        previous_time_us =
            current_time_us;


        if (dt <= 0.0f)
        {
            vTaskDelay(
                pdMS_TO_TICKS(
                    PID_PERIOD_MS
                )
            );

            continue;
        }


        encoder_get_data(
            &encoder_data
        );


        portENTER_CRITICAL(
            &pid_spinlock
        );

        linear_command =
            command_linear_velocity;

        angular_command =
            command_angular_velocity;

        portEXIT_CRITICAL(
            &pid_spinlock
        );


        left_target =
            linear_command -
            (
                angular_command *
                WHEEL_BASE_M /
                2.0f
            );


        right_target =
            linear_command +
            (
                angular_command *
                WHEEL_BASE_M /
                2.0f
            );


        left_target =
            clamp(
                left_target,
                -MAX_WHEEL_SPEED_MPS,
                MAX_WHEEL_SPEED_MPS
            );


        right_target =
            clamp(
                right_target,
                -MAX_WHEEL_SPEED_MPS,
                MAX_WHEEL_SPEED_MPS
            );


        if (
            fabsf(left_target) < 0.001f &&
            fabsf(encoder_data.left_velocity) < 0.001f
        )
        {
            left_pid.integral = 0.0f;
            left_pid.previous_error = 0.0f;

            left_pwm = 0.0f;
        }
        else
        {
            left_pwm =
                calculate_pid(
                    &left_pid,
                    left_target,
                    encoder_data.left_velocity,
                    dt
                );
        }


        if (
            fabsf(right_target) < 0.001f &&
            fabsf(encoder_data.right_velocity) < 0.001f
        )
        {
            right_pid.integral = 0.0f;
            right_pid.previous_error = 0.0f;

            right_pwm = 0.0f;
        }
        else
        {
            right_pwm =
                calculate_pid(
                    &right_pid,
                    right_target,
                    encoder_data.right_velocity,
                    dt
                );
        }


        left_pwm =
            clamp(
                left_pwm,
                -PWM_MAX,
                PWM_MAX
            );


        right_pwm =
            clamp(
                right_pwm,
                -PWM_MAX,
                PWM_MAX
            );


        portENTER_CRITICAL(
            &pid_spinlock
        );

        pid_output.left_pwm =
            left_pwm;

        pid_output.right_pwm =
            right_pwm;

        portEXIT_CRITICAL(
            &pid_spinlock
        );


        motor_control_set_pwm(
            left_pwm,
            right_pwm
        );


        printf(
            "PID | Target L: %.3f R: %.3f | "
            "Actual L: %.3f R: %.3f | "
            "PWM L: %.1f R: %.1f | dt: %.4f\n",
            left_target,
            right_target,
            encoder_data.left_velocity,
            encoder_data.right_velocity,
            left_pwm,
            right_pwm,
            dt
        );


        vTaskDelayUntil(
            &last_wake_time,
            pdMS_TO_TICKS(
                PID_PERIOD_MS
            )
        );
    }
}


void pid_init(void)
{
    xTaskCreate(
        pid_task,
        "pid_task",
        4096,
        NULL,
        10,
        NULL
    );
}


void pid_set_command_velocity(
    float linear_velocity,
    float angular_velocity
)
{
    portENTER_CRITICAL(
        &pid_spinlock
    );

    command_linear_velocity =
        linear_velocity;

    command_angular_velocity =
        angular_velocity;

    portEXIT_CRITICAL(
        &pid_spinlock
    );
}


bool pid_get_output(
    PidOutput *output
)
{
    if (output == NULL)
    {
        return false;
    }


    portENTER_CRITICAL(
        &pid_spinlock
    );

    *output =
        pid_output;

    portEXIT_CRITICAL(
        &pid_spinlock
    );


    return true;
}


void pid_reset(void)
{
    portENTER_CRITICAL(
        &pid_spinlock
    );

    left_pid.integral = 0.0f;
    left_pid.previous_error = 0.0f;

    right_pid.integral = 0.0f;
    right_pid.previous_error = 0.0f;

    pid_output.left_pwm = 0.0f;
    pid_output.right_pwm = 0.0f;

    portEXIT_CRITICAL(
        &pid_spinlock
    );
}
