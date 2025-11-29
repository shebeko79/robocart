#include <Arduino.h>

#include "power_managment.h"
#include "robot_defs.h"
#include "robot_pins.h"

static float avg_voltage = 0.0;
static unsigned long low_voltage_ms = 0;

void setupPowerPins()
{
  enablePowerModules(false);
  
  pinMode(VCC_CUT_PIN, OUTPUT);
  pinMode(V5_CUT_PIN, OUTPUT);
  pinMode(V12_CUT_PIN, OUTPUT);
  pinMode(V12_CUT2_PIN, OUTPUT);
}

void allOtherPinsToInputState()
{
  pinMode(ML_PWM_PIN, INPUT);
  pinMode(ML_DIR_PIN, INPUT);
  pinMode(ML_STOP_PIN, INPUT);
  pinMode(ML_A, INPUT);
  pinMode(ML_B, INPUT);
  pinMode(ML_C, INPUT);

  pinMode(MR_PWM_PIN, INPUT);
  pinMode(MR_DIR_PIN, INPUT);
  pinMode(MR_STOP_PIN, INPUT);
  pinMode(MR_A, INPUT);
  pinMode(MR_B, INPUT);
  pinMode(MR_C, INPUT);

  pinMode(VCC_ADC_PIN, INPUT);
}


void enablePowerModules(bool power_on)
{
  int val = power_on? HIGH: LOW;
  digitalWrite(VCC_CUT_PIN, val);
  digitalWrite(V12_CUT_PIN, val);
  digitalWrite(V12_CUT2_PIN, val);
  digitalWrite(V5_CUT_PIN, val);
}

void enablePowerModules(bool vcc, bool v12, bool v12_2, bool v5)
{
  digitalWrite(VCC_CUT_PIN, vcc);
  digitalWrite(V12_CUT_PIN, v12);
  digitalWrite(V12_CUT2_PIN, v12_2);
  digitalWrite(V5_CUT_PIN, v5);
}

void setupVCC_ADC()
{
  analogReadResolution(12);
  analogSetPinAttenuation(VCC_ADC_PIN, ADC_11db);
}

float getVCCVoltage()
{
  constexpr float a=(VCC_REF_V1-VCC_REF_V2)/(VCC_REF_ADC1-VCC_REF_ADC2);
  constexpr float b=VCC_REF_V1-a*VCC_REF_ADC1;
  
  int v = analogRead(VCC_ADC_PIN);
  return v*a+b;
}

void goToSleepMode(int seconds_to_sleep)
{
  enablePowerModules(false);

  esp_sleep_enable_timer_wakeup(seconds_to_sleep * 1000000ULL);
  esp_deep_sleep_start();
}

void checkIfEnoughVoltageToStart()
{
  float vcc = getVCCVoltage();
  if (vcc<POWER_ON_VOLTAGE)
    goToSleepMode(DEEP_SLEEP_DURATION);

    avg_voltage = vcc;
}

void checkLowVoltageSleep()
{
  float vcc = getVCCVoltage();
  avg_voltage = (vcc + avg_voltage) / 2.0;

  if (avg_voltage>=POWER_OFF_VOLTAGE)
  {
    low_voltage_ms = 0;
    return;
  }

  if(low_voltage_ms == 0)
  {
    low_voltage_ms = millis();
    return;
  }

  unsigned long d = millis() - low_voltage_ms;

  //Serial.print(" vcc=");
  //Serial.print(vcc,4);
  //Serial.print(" avg_voltage=");
  //Serial.print(avg_voltage,4);
  //Serial.print(" d=");
  //Serial.print(d);
  //Serial.print(" low_voltage_ms=");
  //Serial.print(low_voltage_ms);
  //Serial.println("");

  if(d > LOW_VOLTAGE_SLEEP_DELAY)
    goToSleepMode(DEEP_SLEEP_DURATION);
}
