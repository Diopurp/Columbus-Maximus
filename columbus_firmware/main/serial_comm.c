#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "driver/uart.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

#include "esp_log.h"
#include "esp_task_wdt.h"

#include "serial_comm.h"


#define UART_PORT           UART_NUM_0
#define UART_BAUD_RATE      115200

#define UART_RX_BUFFER_SIZE 1024
#define COMMAND_BUFFER_SIZE 64
#define COMMAND_QUEUE_SIZE  1

static const char *TAG = "SERIAL_COMM";

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
        ESP_LOGW(
            TAG,
            "FAILED TO PARSE: [%s]",
            message
        );

        return false;
    }

    command->linear = linear;
    command->angular = angular;

    ESP_LOGI(
        TAG,
        "PARSED COMMAND: linear=%.3f angular=%.3f",
        linear,
        angular
    );

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

    ESP_LOGI(
        TAG,
        "Serial receiver task started"
    );

    ESP_LOGI(
        TAG,
        "Listening on UART0 @ %d baud",
        UART_BAUD_RATE
    );

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


        /*
         * Echo every received byte in hexadecimal.
         *
         * This lets us verify exactly what is
         * physically arriving at the ESP32.
         */
        ESP_LOGI(
            TAG,
            "RX byte: 0x%02X '%c'",
            received_byte,
            (received_byte >= 32 && received_byte <= 126)
                ? received_byte
                : '.'
        );


        if (received_byte == '\n')
        {
            command_buffer[buffer_index] = '\0';

            ESP_LOGI(
                TAG,
                "COMPLETE MESSAGE: [%s]",
                command_buffer
            );

            if (parse_velocity_command(
                    command_buffer,
                    &command))
            {
                if (xQueueOverwrite(
                        command_queue,
                        &command) != pdTRUE)
                {
                    ESP_LOGE(
                        TAG,
                        "Failed to write command to queue"
                    );
                }
                else
                {
                    ESP_LOGI(
                        TAG,
                        "COMMAND QUEUED"
                    );
                }
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
            ESP_LOGW(
                TAG,
                "Command buffer overflow - resetting"
            );

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


    ESP_LOGI(
        TAG,
        "Initializing UART0..."
    );


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


    if (command_queue == NULL)
    {
        ESP_LOGE(
            TAG,
            "Failed to create command queue"
        );

        return;
    }


    ESP_LOGI(
        TAG,
        "Command queue created"
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


    if (xQueueReceive(
            command_queue,
            command,
            timeout
        ) == pdTRUE)
    {
        ESP_LOGI(
            TAG,
            "COMMAND DELIVERED TO MOTOR CONTROL: linear=%.3f angular=%.3f",
            command->linear,
            command->angular
        );

        return true;
    }


    return false;
}
