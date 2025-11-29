#pragma once
#include "robot_defs.h"
#include "motor_zsx11h.h"

class MotorSpeed
{
public:
  typedef MotorZsx11h Motor;

  enum BrakeState
  {
    bs_zero_speed,
    bs_fail_safe,
    bs_change_direction,
    bs_speed_compensation
  };
  
public:
  MotorSpeed(Motor& motor) : 
    m_motor(motor)
  {
  }

  void init()
  {
    m_motor.init();
  }

  void set_speed(float speed)
  {
    m_dst_speed = constrain(speed, -MAX_SPEED, MAX_SPEED);
  }

  void apply();
  
  void fail_safe();
  void dump_state(const String& caption, Stream& stream);

private:
  float calc_pwm(float cur_speed, bool &is_brake);
  void reset_pid();
  
private:
  volatile float m_dst_speed = 0.0;

  Motor& m_motor;

  unsigned m_prev_steps=0;
  float m_prev_speed=0.0;
  unsigned long m_prev_time=0;
  float m_prev_acc = 0.0;
  static constexpr float m_speed2pwm = 1.0/MAX_SPEED;
  float m_prev_pwm=0.0;
  
  BrakeState m_brake_state = bs_zero_speed;
};
