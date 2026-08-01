#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/gpio.h"
#include "driver/ledc.h"

#define LEFT_PWM_PIN    GPIO_NUM_18 //D18
#define LEFT_DIR_PIN    GPIO_NUM_19 //D19

#define RIGHT_PWM_PIN   GPIO_NUM_17 //TX2
#define RIGHT_DIR_PIN   GPIO_NUM_16 //RX2

#define MAX_SPEED       255
#define TURN_SPEED      120

void app_main(void)
{
    //---------------- Direction Pins ----------------//

    gpio_set_direction(LEFT_DIR_PIN, GPIO_MODE_OUTPUT);
    gpio_set_direction(RIGHT_DIR_PIN, GPIO_MODE_OUTPUT);

    //---------------- PWM Timer ----------------//

    ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .timer_num = LEDC_TIMER_0,
        .duty_resolution = LEDC_TIMER_8_BIT,
        .freq_hz = 20000,
        .clk_cfg = LEDC_AUTO_CLK
    };

    ledc_timer_config(&timer);

    //---------------- Left PWM ----------------//

    ledc_channel_config_t left = {
        .gpio_num = LEFT_PWM_PIN,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .hpoint = 0
    };

    ledc_channel_config(&left);

    //---------------- Right PWM ----------------//

    ledc_channel_config_t right = {
        .gpio_num = RIGHT_PWM_PIN,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_1,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .hpoint = 0
    };

    ledc_channel_config(&right);

    char cmd;

    while (1)
    {
        printf("\nEnter Command (W A S D X): ");
        scanf(" %c", &cmd);

        if(cmd == 'w')
        {
            gpio_set_level(LEFT_DIR_PIN,1);
            gpio_set_level(RIGHT_DIR_PIN,1);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0,MAX_SPEED);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1,MAX_SPEED);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1);
        }

        else if(cmd == 's')
        {
            gpio_set_level(LEFT_DIR_PIN,0);
            gpio_set_level(RIGHT_DIR_PIN,0);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0,MAX_SPEED);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1,MAX_SPEED);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1);
        }

        else if(cmd == 'a')
        {
            gpio_set_level(LEFT_DIR_PIN,1);
            gpio_set_level(RIGHT_DIR_PIN,1);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0,0);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1,TURN_SPEED);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1);
        }

        else if(cmd == 'd')
        {
            gpio_set_level(LEFT_DIR_PIN,1);
            gpio_set_level(RIGHT_DIR_PIN,1);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0,TURN_SPEED);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1,0);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1);
        }

        else if(cmd == 'x')
        {
            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0,0);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0);

            ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1,0);
            ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_1);
        }
    }
}
