#include <Arduino.h>
#include "motor_speed.h"

void MotorSpeed::apply()
{
  float cur_speed = m_motor.get_speed_meters();
  Motor::State st = m_motor.get_state();

  if(st == Motor::st_brake && m_brake_state == bs_change_direction)
  {
    if(std::abs(cur_speed)>OFF_SPEED)
      return;
    
    m_motor.soft_stop();
    cur_speed = 0.0;
    // Serial.println("after brake off");
  }

  if(st==Motor::st_forward && m_dst_speed<-OFF_SPEED ||
      st==Motor::st_backward && m_dst_speed>OFF_SPEED)
  {
    // Serial.println("brake");
    m_motor.brake();
    m_brake_state = bs_change_direction;
    reset_pid();
    return;
  }

  if(m_dst_speed==0.0)
  {
    m_motor.brake();
    m_brake_state = bs_zero_speed;
    reset_pid();
    return;
  }

  bool is_brake = false;
  float ctl_pwm=calc_pwm(cur_speed,is_brake);
  if(is_brake)
  {
    m_motor.brake();
    m_brake_state = bs_speed_compensation;
    return;
  }

  int pwm = ctl_pwm*Motor::MAX_PWM;
  pwm = constrain(pwm, -Motor::MAX_PWM, Motor::MAX_PWM);

  if(pwm<0)
    m_motor.backward(-pwm);
  else
    m_motor.forward(pwm);
}

float MotorSpeed::calc_pwm(float cur_speed, bool &is_brake)
{
  unsigned long cur_time = millis();

  float cur_delay;
  if(cur_time == m_prev_time)
    cur_delay=EXPECTED_PWM_DELAY;
  else
    cur_delay = (cur_time - m_prev_time)/1000.0;

  float cur_acc = (cur_speed-m_prev_speed)/cur_delay;
  const float kdirection = (m_dst_speed<0)? -1.0:1.0;
  const float kincrease = (cur_speed*kdirection<=m_dst_speed*kdirection)? 1.0:-1.0;
  const float kspeed_correction = kincrease>0? UP_SPEED_CORRECTION:DOWN_SPEED_CORRECTION;

  float func_pwm = speed2pwm(m_dst_speed);
  float correction_pwm = m_prev_correction_pwm;
  float kick_pwm = 0.0;

  if(cur_acc*kincrease*kdirection<0.0 || cur_acc*kincrease*kdirection<CLOSE_TO_ZERO_ACCELERATION)
  {
    correction_pwm = m_prev_correction_pwm+(m_dst_speed-cur_speed)*kspeed_correction;
  }

  if(kincrease>0)
  {
    if(m_prev_acc == 0.0 && cur_acc==0.0 && cur_speed == 0.0 && std::abs(m_dst_speed)>CLOSE_TO_ZERO_SPEED_DIFF)
        kick_pwm = KICK_PWM_CORRECTION*kdirection;
  }
  else
  {
    if(cur_acc*kdirection>CLOSE_TO_ZERO_ACCELERATION && (cur_speed-m_dst_speed)*kdirection>BREAK_MAX_SPEED_DIFF_WITH_ACCELERATION || (cur_speed-m_dst_speed)*kdirection>BREAK_MAX_SPEED_DIFF)
    {
      is_brake=true;
      kick_pwm = BREAK_PWM_CORRECTION*kdirection;
    }
  }

  correction_pwm = constrain(correction_pwm, -2.0, 2.0);
  
  float res_pwm = func_pwm + correction_pwm + kick_pwm;
  res_pwm = constrain(res_pwm, -1.0, 1.0);
  
  Serial.print(" dst_sp=");
  Serial.print(m_dst_speed,4);
  Serial.print(" cur_sp=");
  Serial.print(cur_speed,4);
  Serial.print(" acc=");
  Serial.print(cur_acc,4);
  Serial.print(" prev_acc=");
  Serial.print(m_prev_acc,4);
  Serial.print(" res_pwm=");
  Serial.print(res_pwm,4);
  Serial.print(" correction_pwm=");
  Serial.print(correction_pwm,4);
  Serial.print(" kick_pwm=");
  Serial.print(kick_pwm,4);
  Serial.print(" is_brake=");
  Serial.print(is_brake);
  Serial.print(" prev_correction=");
  Serial.print(m_prev_correction_pwm,4);
  Serial.println("");

  m_prev_speed=cur_speed;
  m_prev_acc = cur_acc;
  m_prev_time=cur_time;
  m_prev_correction_pwm = correction_pwm;
  
  return  res_pwm;
}

void MotorSpeed::reset_pid()
{
  m_prev_speed = 0.0;
  m_prev_time = millis();
  m_prev_acc = 0.0;
  m_prev_correction_pwm = 0.0;
}

void MotorSpeed::fail_safe()
{
  m_dst_speed = 0.0;
  m_motor.brake();
  m_brake_state = bs_fail_safe;
  m_distance_mode = false;
  reset_pid();
}

float MotorSpeed::speed2pwm(float speed) const
{
  return m_speed2pwm * speed;
}

void MotorSpeed::set_distance(float speed, float distance)
{
  if(speed == 0.0)
    return set_speed(speed);
  
  m_dst_speed = constrain(speed, -MAX_SPEED, MAX_SPEED);
  m_distance = static_cast<int>(distance*WHEEL_PULSES_PER_METER);
  m_start_distance_tick = m_motor.get_ticks_count();
  m_distance_mode = true;
}

bool MotorSpeed::get_path(double& cur_dist) const
{
  if(m_distance_mode)
    cur_dist = (m_motor.get_ticks_count() - m_start_distance_tick) / WHEEL_PULSES_PER_METER;
  return m_distance_mode;
}

void MotorSpeed::speed_pin_isr()
{
  m_motor.speed_pin_isr();
  if(!m_distance_mode)
    return;
  
  int diff = m_motor.get_ticks_count() - m_start_distance_tick;
  int dx = (m_distance>=0) ? 1.0:-1.0;

  if(diff*dx >= m_distance*dx)
  {
    m_distance_mode = false;
    m_dst_speed = 0.0;
    m_motor.brake();
    m_brake_state = bs_distance_reached;
    reset_pid();
  }
}

void MotorSpeed::dump_state(const String& caption, Stream& stream)
{
  float cur_speed = m_motor.get_speed_meters();
  Motor::State st = m_motor.get_state();

  if(st == Motor::st_brake && cur_speed == 0.0)
  {
    return;
  }

  stream.print(caption);
  stream.print(":");
  stream.print(" time=");
  stream.print(millis());
  stream.print(" dst_speed=");
  stream.print(m_dst_speed,4);
  stream.print(" cur_speed=");
  stream.print(cur_speed,4);
  stream.println("");
}
