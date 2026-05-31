#pragma once
#include "robot_defs.h"
#include "motor_zsx11h.h"

class MotorSpeed
{
public:
  typedef MotorZsx11h Motor;

  struct shot_t
  {
    unsigned long time=0;
    float speed=0.0;
    float dst_speed=0.0;
    float func_pwm=0.0;
    float correction_pwm=0.0;
    float kick_pwm=0.0;
    bool is_brake = false;
    bool is_stalled = false;

    float pwm() const{return constrain(func_pwm + correction_pwm + kick_pwm, -m_pwm_limit, m_pwm_limit);}
    void dump_state(Stream& stream);
  };
  
public:
  static float m_pwm_limit;

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
    m_distance_mode = false;
  }

  void set_distance(float speed, float distance);

  bool get_path(double& cur_dist) const;
  
  void apply();
  
  void fail_safe();
  void dump_state(const String& caption, Stream& stream);

  void speed_pin_isr();

private:
  float calc_pwm(float cur_speed, bool &is_brake);
  void reset_pid();
  float speed2pwm(float speed) const;

  static unsigned wrap_shot_idx(unsigned idx);

  bool anti_stall();

private:
  volatile float m_dst_speed = 0.0;
  volatile bool m_distance_mode = false;
  volatile int m_distance = 0;
  volatile int m_start_distance_tick = 0;

  Motor& m_motor;

  static constexpr unsigned SHOTS_COUNT = 32;
  std::array<shot_t, SHOTS_COUNT> m_shots;
  unsigned m_cur_shot;

  static constexpr float m_speed2pwm = 1.0/MAX_SPEED;
};
