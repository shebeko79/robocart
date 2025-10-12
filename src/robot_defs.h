#pragma once
#include <math.h>

constexpr int FAIL_SAFE_DELAY = 500;

constexpr float WHEEL_PULSES_PER_ROTATION=90.0;
constexpr float WHEEL_DIAMETER=6.5*0.0254; //meters
constexpr float WHEEL_PERIMETER=M_PI*WHEEL_DIAMETER;
constexpr float WHEEL_PULSES_PER_METER=WHEEL_PULSES_PER_ROTATION/WHEEL_PERIMETER;
 
constexpr float MAX_SPEED = 4.0; //Estimated speed of unloaded wheel on maximum power (meters per second)
constexpr float OFF_SPEED = 0.01; //meters per second
constexpr float CLOSE_TO_ZERO_ACCELERATION = 0.02;
constexpr float CLOSE_TO_ZERO_SPEED_DIFF = 0.05;
constexpr float UP_SPEED_CORRECTION = 0.01;
constexpr float DOWN_SPEED_CORRECTION = 0.03;
constexpr float BREAK_MAX_SPEED_DIFF = 1.0;
constexpr float BREAK_MAX_SPEED_DIFF_WITH_ACCELERATION = 0.5;
constexpr float KICK_PWM_CORRECTION = 0.1;
constexpr float BREAK_PWM_CORRECTION = 0.2;
constexpr unsigned long MAIN_CYCLE_DELAY = 50;
constexpr float EXPECTED_PWM_DELAY = MAIN_CYCLE_DELAY/1000.0;

constexpr float RELATIVE_MAX_SPEED = 0.3; //meters per second
constexpr float RELATIVE_MAX_ROT = 0.2; //meters per second

constexpr unsigned TIMER_MS=10;

constexpr float POWER_OFF_VOLTAGE = 20.3; //Volts
constexpr float POWER_ON_VOLTAGE = 22.0; //Volts
constexpr unsigned long DEEP_SLEEP_DURATION = 60; //Seconds
constexpr float VCC_REF_ADC1=1347.0; //Reference ADC value point 1
constexpr float VCC_REF_V1=25.0; //Reference voltage point 1
constexpr float VCC_REF_ADC2=747.0; //Reference ADC value point 2
constexpr float VCC_REF_V2=15.0; //Reference voltage point 1

