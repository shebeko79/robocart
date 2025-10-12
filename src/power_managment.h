#pragma once

void setupPowerPins();
void enablePowerModules(bool power_on);

void setupVCC_ADC();
float getVCCVoltage();

void goToSleepMode(int seconds_to_sleep);
void checkIfEnoughVoltageToStart();
void checkLowVoltageSleep();
