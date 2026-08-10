#include "motor_control.h"

#include <math.h>

#include "driver/gpio.h"
#include "driver/ledc.h"

#define LEFT_PWM_GPIO       18  // ESP32 board: D18
#define LEFT_DIR_GPIO       19  // ESP32 board: D19

#define RIGHT_PWM_GPIO      16  // ESP32 board: RX2
#define RIGHT_DIR_GPIO      17  // ESP32 board: TX2

#define PWM_FREQUENCY       20000
#define PWM_RESOLUTION      LEDC_TIMER_8_BIT
#define PWM_MAX             255

#define WHEEL_BASE_M        0.22f
#define MAX_WHEEL_SPEED_MPS 1.0f

#define PWM_TIMER           LEDC_TIMER_0

#define LEFT_PWM_CHANNEL    LEDC_CHANNEL_0
#define RIGHT_PWM_CHANNEL   LEDC_CHANNEL_1


static int velocity_to_pwm(float velocity)
{
    if (velocity < 0.0f)
    {
        velocity = -velocity;
    }

    if (velocity >= MAX_WHEEL_SPEED_MPS)
    {
        return PWM_MAX;
    }

    return (int)(
        (velocity / MAX_WHEEL_SPEED_MPS) * PWM_MAX
    );
}


static void set_left_motor(float velocity)
{
    int pwm = velocity_to_pwm(velocity);

    if (velocity >= 0.0f)
    {
        gpio_set_level(LEFT_DIR_GPIO, 1);
    }
    else
    {
        gpio_set_level(LEFT_DIR_GPIO, 0);
    }

    ledc_set_duty(
        LEDC_LOW_SPEED_MODE,
        LEFT_PWM_CHANNEL,
        pwm
    );

    ledc_update_duty(
        LEDC_LOW_SPEED_MODE,
        LEFT_PWM_CHANNEL
    );
}


static void set_right_motor(float velocity)
{
    int pwm = velocity_to_pwm(velocity);

    if (velocity >= 0.0f)
    {
        gpio_set_level(RIGHT_DIR_GPIO, 1);
    }
    else
    {
        gpio_set_level(RIGHT_DIR_GPIO, 0);
    }

    ledc_set_duty(
        LEDC_LOW_SPEED_MODE,
        RIGHT_PWM_CHANNEL,
        pwm
    );

    ledc_update_duty(
        LEDC_LOW_SPEED_MODE,
        RIGHT_PWM_CHANNEL
    );
}


void motor_control_init(void)
{
    gpio_config_t dir_config =
    {
        .pin_bit_mask =
            (1ULL << LEFT_DIR_GPIO) |
            (1ULL << RIGHT_DIR_GPIO),

        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    gpio_config(&dir_config);


    ledc_timer_config_t timer_config =
    {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_num = PWM_TIMER,
        .duty_resolution = PWM_RESOLUTION,
        .freq_hz = PWM_FREQUENCY,
        .clk_cfg = LEDC_AUTO_CLK
    };

    ledc_timer_config(&timer_config);


    ledc_channel_config_t left_channel =
    {
        .gpio_num = LEFT_PWM_GPIO,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEFT_PWM_CHANNEL,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = PWM_TIMER,
        .duty = 0,
        .hpoint = 0
    };

    ledc_channel_config(&left_channel);


    ledc_channel_config_t right_channel =
    {
        .gpio_num = RIGHT_PWM_GPIO,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = RIGHT_PWM_CHANNEL,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = PWM_TIMER,
        .duty = 0,
        .hpoint = 0
    };

    ledc_channel_config(&right_channel);
}


void motor_control_set_velocity(
    float linear,
    float angular
)
{
    float left_velocity;
    float right_velocity;

    left_velocity =
        linear - (angular * WHEEL_BASE_M / 2.0f);

    right_velocity =
        linear + (angular * WHEEL_BASE_M / 2.0f);

    set_left_motor(left_velocity);
    set_right_motor(right_velocity);
}
