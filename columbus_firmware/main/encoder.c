#include "encoder.h"

#include <math.h>
#include <stdint.h>

#include "driver/gpio.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_timer.h"


#define LEFT_ENCODER_A      GPIO_NUM_4
#define LEFT_ENCODER_B      GPIO_NUM_21

#define RIGHT_ENCODER_A     GPIO_NUM_22
#define RIGHT_ENCODER_B     GPIO_NUM_23


#define WHEEL_DIAMETER_M    0.11f
#define WHEEL_BASE_M        0.22f

#define COUNTS_PER_REV      2925.0f

#define ENCODER_PERIOD_MS   20

#define PI                  3.14159265359f


#define WHEEL_CIRCUMFERENCE_M \
    (PI * WHEEL_DIAMETER_M)

#define DISTANCE_PER_COUNT \
    (WHEEL_CIRCUMFERENCE_M / COUNTS_PER_REV)


static volatile int32_t left_count = 0;
static volatile int32_t right_count = 0;


static uint8_t left_last_state = 0;
static uint8_t right_last_state = 0;


static float odom_x = 0.0f;
static float odom_y = 0.0f;
static float odom_theta = 0.0f;


static int32_t previous_left_count = 0;
static int32_t previous_right_count = 0;


static EncoderData encoder_data =
{
    .left_count = 0,
    .right_count = 0,

    .left_distance = 0.0f,
    .right_distance = 0.0f,

    .left_velocity = 0.0f,
    .right_velocity = 0.0f,

    .linear_velocity = 0.0f,
    .angular_velocity = 0.0f,

    .x = 0.0f,
    .y = 0.0f,
    .theta = 0.0f
};


static portMUX_TYPE encoder_spinlock =
    portMUX_INITIALIZER_UNLOCKED;


static const int8_t quad_table[16] =
{
     0, -1,  1,  0,
     1,  0,  0, -1,
    -1,  0,  0,  1,
     0,  1, -1,  0
};


static void IRAM_ATTR left_encoder_isr(void *arg)
{
    uint8_t a;
    uint8_t b;
    uint8_t current_state;
    uint8_t index;

    a = gpio_get_level(LEFT_ENCODER_A);
    b = gpio_get_level(LEFT_ENCODER_B);

    current_state = (a << 1) | b;

    index =
        (left_last_state << 2) |
        current_state;

    portENTER_CRITICAL_ISR(&encoder_spinlock);

    left_count += quad_table[index];
    left_last_state = current_state;

    portEXIT_CRITICAL_ISR(&encoder_spinlock);
}


static void IRAM_ATTR right_encoder_isr(void *arg)
{
    uint8_t a;
    uint8_t b;
    uint8_t current_state;
    uint8_t index;

    a = gpio_get_level(RIGHT_ENCODER_A);
    b = gpio_get_level(RIGHT_ENCODER_B);

    current_state = (a << 1) | b;

    index =
        (right_last_state << 2) |
        current_state;

    portENTER_CRITICAL_ISR(&encoder_spinlock);

    right_count += quad_table[index];
    right_last_state = current_state;

    portEXIT_CRITICAL_ISR(&encoder_spinlock);
}


static void encoder_task(void *arg)
{
    (void)arg;

    int64_t previous_time_us;

    previous_time_us = esp_timer_get_time();

    while (1)
    {
        int32_t current_left_count;
        int32_t current_right_count;

        int32_t delta_left_count;
        int32_t delta_right_count;

        int64_t current_time_us;

        float dt;

        float delta_left_distance;
        float delta_right_distance;

        float left_velocity;
        float right_velocity;

        float linear_velocity;
        float angular_velocity;

        float delta_distance;
        float delta_theta;

        float theta_mid;


        current_time_us =
            esp_timer_get_time();


        portENTER_CRITICAL(&encoder_spinlock);

        current_left_count = left_count;
        current_right_count = right_count;

        portEXIT_CRITICAL(&encoder_spinlock);


        delta_left_count =
            current_left_count -
            previous_left_count;

        delta_right_count =
            current_right_count -
            previous_right_count;


        dt =
            (float)(
                current_time_us -
                previous_time_us
            ) / 1000000.0f;


        previous_left_count =
            current_left_count;

        previous_right_count =
            current_right_count;

        previous_time_us =
            current_time_us;


        if (dt <= 0.0f)
        {
            vTaskDelay(
                pdMS_TO_TICKS(
                    ENCODER_PERIOD_MS
                )
            );

            continue;
        }


        delta_left_distance =
            delta_left_count *
            DISTANCE_PER_COUNT;

        delta_right_distance =
            delta_right_count *
            DISTANCE_PER_COUNT;


        left_velocity =
            delta_left_distance / dt;

        right_velocity =
            delta_right_distance / dt;


        linear_velocity =
            (left_velocity +
             right_velocity) / 2.0f;


        angular_velocity =
            (right_velocity -
             left_velocity) /
            WHEEL_BASE_M;


        delta_distance =
            (delta_left_distance +
             delta_right_distance)
            / 2.0f;


        delta_theta =
            (delta_right_distance -
             delta_left_distance)
            / WHEEL_BASE_M;


        theta_mid =
            odom_theta +
            (delta_theta / 2.0f);


        odom_x +=
            delta_distance *
            cosf(theta_mid);

        odom_y +=
            delta_distance *
            sinf(theta_mid);

        odom_theta +=
            delta_theta;


        portENTER_CRITICAL(&encoder_spinlock);

        encoder_data.left_count =
            current_left_count;

        encoder_data.right_count =
            current_right_count;

        encoder_data.left_distance =
            current_left_count *
            DISTANCE_PER_COUNT;

        encoder_data.right_distance =
            current_right_count *
            DISTANCE_PER_COUNT;

        encoder_data.left_velocity =
            left_velocity;

        encoder_data.right_velocity =
            right_velocity;

        encoder_data.linear_velocity =
            linear_velocity;

        encoder_data.angular_velocity =
            angular_velocity;

        encoder_data.x =
            odom_x;

        encoder_data.y =
            odom_y;

        encoder_data.theta =
            odom_theta;

        portEXIT_CRITICAL(&encoder_spinlock);


        vTaskDelay(
            pdMS_TO_TICKS(
                ENCODER_PERIOD_MS
            )
        );
    }
}


void encoder_init(void)
{
    gpio_config_t config =
    {
        .pin_bit_mask =
            (1ULL << LEFT_ENCODER_A) |
            (1ULL << LEFT_ENCODER_B) |
            (1ULL << RIGHT_ENCODER_A) |
            (1ULL << RIGHT_ENCODER_B),

        .mode =
            GPIO_MODE_INPUT,

        .pull_up_en =
            GPIO_PULLUP_DISABLE,

        .pull_down_en =
            GPIO_PULLDOWN_DISABLE,

        .intr_type =
            GPIO_INTR_ANYEDGE
    };


    gpio_config(&config);


    gpio_install_isr_service(0);


    gpio_isr_handler_add(
        LEFT_ENCODER_A,
        left_encoder_isr,
        NULL
    );

    gpio_isr_handler_add(
        LEFT_ENCODER_B,
        left_encoder_isr,
        NULL
    );


    gpio_isr_handler_add(
        RIGHT_ENCODER_A,
        right_encoder_isr,
        NULL
    );

    gpio_isr_handler_add(
        RIGHT_ENCODER_B,
        right_encoder_isr,
        NULL
    );


    uint8_t left_a =
        gpio_get_level(LEFT_ENCODER_A);

    uint8_t left_b =
        gpio_get_level(LEFT_ENCODER_B);

    left_last_state =
        (left_a << 1) | left_b;


    uint8_t right_a =
        gpio_get_level(RIGHT_ENCODER_A);

    uint8_t right_b =
        gpio_get_level(RIGHT_ENCODER_B);

    right_last_state =
        (right_a << 1) | right_b;


    xTaskCreate(
        encoder_task,
        "encoder_task",
        4096,
        NULL,
        10,
        NULL
    );
}


bool encoder_get_data(
    EncoderData *data
)
{
    if (data == NULL)
    {
        return false;
    }


    portENTER_CRITICAL(&encoder_spinlock);

    *data = encoder_data;

    portEXIT_CRITICAL(&encoder_spinlock);


    return true;
}


void encoder_reset_odometry(void)
{
    portENTER_CRITICAL(&encoder_spinlock);

    left_count = 0;
    right_count = 0;

    previous_left_count = 0;
    previous_right_count = 0;

    odom_x = 0.0f;
    odom_y = 0.0f;
    odom_theta = 0.0f;

    encoder_data.left_count = 0;
    encoder_data.right_count = 0;

    encoder_data.left_distance = 0.0f;
    encoder_data.right_distance = 0.0f;

    encoder_data.left_velocity = 0.0f;
    encoder_data.right_velocity = 0.0f;

    encoder_data.linear_velocity = 0.0f;
    encoder_data.angular_velocity = 0.0f;

    encoder_data.x = 0.0f;
    encoder_data.y = 0.0f;
    encoder_data.theta = 0.0f;

    portEXIT_CRITICAL(&encoder_spinlock);
}
