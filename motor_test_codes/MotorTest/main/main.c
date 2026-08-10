#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/gpio.h"
#include "driver/ledc.h"

#define LEFT_PWM_PIN   GPIO_NUM_18
#define LEFT_DIR_PIN   GPIO_NUM_19

#define RIGHT_PWM_PIN  GPIO_NUM_17
#define RIGHT_DIR_PIN  GPIO_NUM_16

void app_main(void)
{
    //---------------- Direction Pins ----------------

    gpio_set_direction(LEFT_DIR_PIN, GPIO_MODE_OUTPUT);
    gpio_set_direction(RIGHT_DIR_PIN, GPIO_MODE_OUTPUT);

    gpio_set_level(LEFT_DIR_PIN, 1);
    gpio_set_level(RIGHT_DIR_PIN, 1);

    //---------------- PWM Timer ----------------

    ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_num = LEDC_TIMER_0,
        .duty_resolution = LEDC_TIMER_8_BIT,
        .freq_hz = 20000,
        .clk_cfg = LEDC_AUTO_CLK
    };

    ledc_timer_config(&timer);

    //---------------- Left Motor ----------------

    ledc_channel_config_t left_motor = {
        .gpio_num = LEFT_PWM_PIN,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .duty = 255,
        .hpoint = 0
    };

    ledc_channel_config(&left_motor);

    //---------------- Right Motor ----------------

    ledc_channel_config_t right_motor = {
        .gpio_num = RIGHT_PWM_PIN,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1,
        .timer_sel = LEDC_TIMER_0,
        .duty = 150,
        .hpoint = 0
    };

    ledc_channel_config(&right_motor);

    //---------------- Keep Running ----------------

    while (1)
    {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
