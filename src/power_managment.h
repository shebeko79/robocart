#pragma once

void setupPowerPins();
void allOtherPinsToInputState();
void enablePowerModules(bool power_on);
void enablePowerModules(bool vcc, bool v12, bool v12_2, bool v5);

void setupVCC_ADC();
float getVCCVoltage();

void goToSleepMode(int seconds_to_sleep);
void checkIfEnoughVoltageToStart();
void checkLowVoltageSleep();
