#include <Arduino.h>

#include "power_managment.h"
#include "robot_defs.h"
#include "robot_pins.h"

void setupPowerPins()
{
  enablePowerModules(false);
  
  pinMode(VCC_CUT_PIN, OUTPUT);
  pinMode(V5_CUT_PIN, OUTPUT);
  pinMode(V12_CUT_PIN, OUTPUT);
  pinMode(V12_CUT2_PIN, OUTPUT);
}

void enablePowerModules(bool power_on)
{
  int val = power_on? LOW: HIGH;
  digitalWrite(VCC_CUT_PIN, val);
  digitalWrite(V5_CUT_PIN, val);
  digitalWrite(V12_CUT_PIN, val);
  digitalWrite(V12_CUT2_PIN, val);
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
}

void checkLowVoltageSleep()
{
  float vcc = getVCCVoltage();
  if (vcc<POWER_OFF_VOLTAGE)
    goToSleepMode(DEEP_SLEEP_DURATION);
}
