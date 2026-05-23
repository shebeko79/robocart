#pragma once
#include "robot_defs.h"

class MotorZsx11h
{
public:
  static constexpr int PWM_BITS=10;
  static constexpr int MAX_PWM=(1<<PWM_BITS)-1;

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
  void check_speed_timeout();
  
  inline float get_speed_meters()const{return m_speed;}
  inline State get_state() const{return m_state;}
  inline int get_ticks_count()const{return (DIR_FORWARD? 1.0:-1.0)*m_ticks_count;}

  static float get_blind_ms(double speed);
  
private:
  const int PWM;
  const int DIR;
  const int PWM_CHANNEL;
  const int STOP;

  const bool DIR_FORWARD;
  State m_state;

  const int m_hall_a,m_hall_b,m_hall_c;

  volatile int m_ticks_count = 0;
  volatile int m_hall_idx = 0;

  volatile uint32_t m_cpu_clock[4]={};
  volatile int m_directions[3]={};

  volatile uint32_t m_cpu_diff = 0;
  volatile int m_direction = 0;
  volatile bool m_empty_speed = true;

  float m_cpu_freq;
  float m_speed = 0.0;

  uint32_t m_last_clk = 0;
  unsigned long m_last_clk_ms;

  int readHallIndex();
};
