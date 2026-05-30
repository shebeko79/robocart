#include <Arduino.h>
#include "motor_speed.h"

void MotorSpeed::apply()
{
  float cur_speed = m_motor.get_speed_meters();

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

  if(anti_stall())
    return;

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
  const shot_t& prev = m_shots[m_cur_shot];
  const shot_t& pprev = m_shots[wrap_shot_idx(m_cur_shot-1)];

  if(prev.is_stalled && cur_speed == 0.0 && cur_time-prev.time < STALED_DURATION_MS)
  {
    //Serial.printf("stall cool down: diff=%u\n", cur_time - prev.time);
    is_brake = prev.is_brake;
    return prev.pwm();
  }

  if(prev.dst_speed == m_dst_speed && prev.speed == cur_speed)
  {
    float blind_ms = m_motor.get_blind_ms(m_dst_speed);
    if(blind_ms > cur_time - prev.time)
    {
      //Serial.printf("skip: blind_ms=%.4f diff=%u\n",blind_ms, cur_time - prev.time);
      is_brake = prev.is_brake;
      return prev.pwm();
    }
  }

  m_cur_shot = wrap_shot_idx(m_cur_shot + 1);
  shot_t& cur = m_shots[m_cur_shot];

  cur = shot_t();
  cur.time = cur_time;
  cur.speed = cur_speed;
  cur.dst_speed = m_dst_speed;


  float cur_delay;
  if(cur.time == prev.time)
    cur_delay=EXPECTED_PWM_DELAY;
  else
    cur_delay = (cur.time - prev.time)/1000.0;

  float cur_acc = (cur_speed-prev.speed)/cur_delay;
  const float kdirection = (m_dst_speed<0)? -1.0:1.0;
  const float kincrease = (cur_speed*kdirection<=m_dst_speed*kdirection)? 1.0:-1.0;
  const float kspeed_correction = kincrease>0? UP_SPEED_CORRECTION:DOWN_SPEED_CORRECTION;

  cur.func_pwm = speed2pwm(m_dst_speed);
  cur.correction_pwm = prev.correction_pwm;

  if(cur_acc*kincrease*kdirection<0.0 || cur_acc*kincrease*kdirection<CLOSE_TO_ZERO_ACCELERATION)
  {
    cur.correction_pwm = prev.correction_pwm+(m_dst_speed-cur_speed)*kspeed_correction;
    //Serial.printf("%f=%f+(%f-%f)*%f\n",cur.correction_pwm, prev.correction_pwm, m_dst_speed, cur_speed, kspeed_correction);
  }

  if(kincrease>0)
  {
    if(pprev.speed == 0.0 && prev.speed ==0.0 && cur_speed == 0.0 && std::abs(m_dst_speed)>CLOSE_TO_ZERO_SPEED_DIFF)
        cur.kick_pwm = KICK_PWM_CORRECTION*kdirection;
  }
  else
  {
    if(cur_acc*kdirection>CLOSE_TO_ZERO_ACCELERATION && (cur_speed-m_dst_speed)*kdirection>BREAK_MAX_SPEED_DIFF_WITH_ACCELERATION || (cur_speed-m_dst_speed)*kdirection>BREAK_MAX_SPEED_DIFF)
    {
      cur.is_brake=true;
      cur.kick_pwm = -BREAK_PWM_CORRECTION*kdirection;
    }
  }

  cur.correction_pwm = constrain(cur.correction_pwm, -2.0, 2.0);

  float res_pwm = cur.pwm();
  is_brake = cur.is_brake;
#if 0
  Serial.print(" dst_sp=");
  Serial.print(m_dst_speed,4);
  Serial.print(" acc=");
  Serial.print(cur_acc,4);
  Serial.print(" dt=");
  Serial.print(cur.time-prev.time);
  Serial.print(" cur: ");
  cur.dump_state(Serial);
  Serial.println("");
#endif
  return  res_pwm;
}

void MotorSpeed::reset_pid()
{
  shot_t s;
  s.time = millis();
  std::fill(m_shots.begin(),m_shots.end(),s);
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

unsigned MotorSpeed::wrap_shot_idx(unsigned idx)
{
  static_assert( (std::numeric_limits<unsigned>::max()%SHOTS_COUNT) == SHOTS_COUNT-1);
  return idx % SHOTS_COUNT;
}

bool MotorSpeed::anti_stall()
{
  shot_t& cur = m_shots[m_cur_shot];
  const shot_t& last = m_shots[wrap_shot_idx(m_cur_shot + 1)];

  if(cur.is_stalled)
    return true;
  
  if(cur.dst_speed==0 || cur.speed != 0.0  || cur.time-last.time < STALED_TRIGER_MS)
    return false;
  
  for(const shot_t& v : m_shots)
    if(v.is_stalled || v.speed != 0.0)
      return false;
  
  //Serial.println("stalled");
  m_motor.brake();
  m_brake_state = bs_anti_stall;

  cur.is_stalled = true;
  return true;
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

void MotorSpeed::shot_t::dump_state(Stream& stream)
{
  stream.printf("speed=%.4f pwm=%.4f(%.4f ; %.4f ; %.4f) brake=%d",speed, pwm(), func_pwm, correction_pwm, kick_pwm, is_brake);
}
