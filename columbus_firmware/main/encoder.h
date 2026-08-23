#ifndef ENCODER_H
#define ENCODER_H

#include <stdbool.h>
#include <stdint.h>

typedef struct
{
    int32_t left_count;
    int32_t right_count;

    float left_distance;
    float right_distance;

    float left_velocity;
    float right_velocity;

    float linear_velocity;
    float angular_velocity;

    float x;
    float y;
    float theta;

} EncoderData;


void encoder_init(void);

bool encoder_get_data(
    EncoderData *data
);

void encoder_reset_odometry(void);


#endif
