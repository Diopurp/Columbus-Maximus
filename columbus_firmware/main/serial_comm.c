#include "serial_comm.h"

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#include "driver/uart.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

#include "esp_task_wdt.h"

#define UART_PORT           UART_NUM_0
#define UART_BAUD_RATE      115200

#define UART_RX_BUFFER_SIZE 1024
#define COMMAND_BUFFER_SIZE 64
#define COMMAND_QUEUE_SIZE  1

static QueueHandle_t command_queue = NULL;

static bool parse_velocity_command(
    const char *message,
    VelocityCommand *command
)
{
    float linear;
    float angular;

    int result = sscanf(
        message,
        "VEL,%f,%f",
        &linear,
        &angular
    );

    if (result != 2)
    {
        return false;
    }

    command->linear = linear;
    command->angular = angular;

    return true;
}

static void serial_receive_task(void *arg)
{
    (void)arg;

    uint8_t received_byte;
    char command_buffer[COMMAND_BUFFER_SIZE];

    size_t buffer_index = 0;

    VelocityCommand command;

    esp_task_wdt_add(NULL);

    while (1)
    {
        int length = uart_read_bytes(
            UART_PORT,
            &received_byte,
            1,
            pdMS_TO_TICKS(100)
        );

        if (length <= 0)
        {
            esp_task_wdt_reset();
            continue;
        }

        if (received_byte == '\n')
        {
            command_buffer[buffer_index] = '\0';

            if (parse_velocity_command(
                    command_buffer,
                    &command))
            {
                xQueueOverwrite(
                    command_queue,
                    &command
                );
            }

            buffer_index = 0;

            esp_task_wdt_reset();
            continue;
        }

        if (buffer_index < COMMAND_BUFFER_SIZE - 1)
        {
            command_buffer[buffer_index] =
                (char)received_byte;

            buffer_index++;
        }
        else
        {
            buffer_index = 0;
        }

        esp_task_wdt_reset();
    }
}

void serial_comm_init(void)
{
    const uart_config_t uart_config =
    {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };

    uart_param_config(
        UART_PORT,
        &uart_config
    );

    uart_driver_install(
        UART_PORT,
        UART_RX_BUFFER_SIZE,
        0,
        0,
        NULL,
        0
    );

    uart_set_pin(
        UART_PORT,
        UART_PIN_NO_CHANGE,
        UART_PIN_NO_CHANGE,
        UART_PIN_NO_CHANGE,
        UART_PIN_NO_CHANGE
    );

    command_queue = xQueueCreate(
        COMMAND_QUEUE_SIZE,
        sizeof(VelocityCommand)
    );

    xTaskCreate(
        serial_receive_task,
        "serial_receive",
        4096,
        NULL,
        10,
        NULL
    );
}

bool serial_comm_receive_command(
    VelocityCommand *command,
    TickType_t timeout
)
{
    if (command_queue == NULL)
    {
        return false;
    }

    return (
        xQueueReceive(
            command_queue,
            command,
            timeout
        ) == pdTRUE
    );
}
