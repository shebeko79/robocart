#pragma once
#include "robot_defs.h"

class MotorZsx11h
{
public:
  static constexpr unsigned PERIODS_COUNT = 50;
  static constexpr float KPER_SEC=1000.0/(PERIODS_COUNT*TIMER_MS);
  static const int MAX_PWM=255;

  enum State{st_off,st_forward,st_backward,st_brake};
  
  MotorZsx11h(int pwm,int dir,int pwm_channel, int stop,bool dir_forward,
              int hall_a, int hall_b, int hall_c):
    PWM(pwm),DIR(dir),PWM_CHANNEL(pwm_channel),STOP(stop),
    DIR_FORWARD(dir_forward), m_state(st_off),
    m_hall_a(hall_a),m_hall_b(hall_b),m_hall_c(hall_c)
    {}

  void init();
  void soft_stop();
  void brake();
  void forward(int val=MAX_PWM);
  void backward(int val=MAX_PWM);

  void speed_pin_isr();
  void timer_isr(unsigned timer_val);
  
  inline float get_speed_meters()const{return (DIR_FORWARD? 1.0:-1.0)*m_ticks_count*KPER_SEC/WHEEL_PULSES_PER_METER;}
  inline State get_state() const{return m_state;}
  
private:
  const int PWM;
  const int DIR;
  const int PWM_CHANNEL;
  const int STOP;

  const bool DIR_FORWARD;
  State m_state;

  const int m_hall_a,m_hall_b,m_hall_c;

  volatile unsigned m_timer_val=0;
  volatile int m_periods[PERIODS_COUNT];
  volatile int m_ticks_count = 0;
  volatile int m_hall_idx = 0;

  int readHallIndex();
};
