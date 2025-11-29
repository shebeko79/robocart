#include <Arduino.h>
#include "motor_zsx11h.h"

//st=4 0;0;1
//st=6 0;1;1
//st=2 0;1;0
//st=3 1;1;0
//st=1 1;0;0
//st=5 1;0;1
static constexpr int hall2idx[]={-1,4,2,3,0,5,1,-1};

void MotorZsx11h::speed_pin_isr()
{
  int hall_idx = readHallIndex();

  //Incorrect state of hall sensors
  if(hall_idx == -1)
    return;

  int d = hall_idx - m_hall_idx;
  if(std::abs(d)>3)
    d += 6*(d<0) -6*(d>0);

  m_hall_idx = hall_idx;

  unsigned t = m_timer_val;
  m_periods[t%PERIODS_COUNT] += d;
  m_ticks_count += d;
}

int MotorZsx11h::readHallIndex()
{
  unsigned st = (digitalRead(m_hall_a) == HIGH) | ((digitalRead(m_hall_b) == HIGH)<<1) | ((digitalRead(m_hall_c) == HIGH)<<2);
  return hall2idx[st];
}

void MotorZsx11h::timer_isr(unsigned timer_val)
{
  unsigned new_pi=timer_val%PERIODS_COUNT;
  unsigned old_pi=m_timer_val%PERIODS_COUNT;

  if(new_pi != old_pi)
  {
    m_ticks_count-=m_periods[new_pi];
    m_periods[new_pi] = 0;
  }

  m_timer_val = timer_val;
}

void MotorZsx11h::init()
{
  pinMode(m_hall_a, INPUT);
  pinMode(m_hall_b, INPUT);
  pinMode(m_hall_c, INPUT);
  
  int hall_idx = readHallIndex();
  if(hall_idx != -1)
    m_hall_idx = hall_idx;

  pinMode(STOP, OUTPUT);
  digitalWrite(STOP, HIGH);

  ledcSetup(PWM_CHANNEL, 20000, 8);
  ledcDetachPin(PWM);
  digitalWrite(PWM, LOW);
  pinMode(PWM, OUTPUT);

  pinMode(DIR, OUTPUT);
  digitalWrite(DIR, DIR_FORWARD);

  soft_stop();
}

void MotorZsx11h::soft_stop()
{
  ledcDetachPin(PWM);
  digitalWrite(PWM, LOW);
  digitalWrite(STOP, LOW);
  
  m_state = st_off;
}

void MotorZsx11h::brake()
{
  ledcDetachPin(PWM);
  digitalWrite(PWM, LOW);
  digitalWrite(STOP, HIGH);
  
  m_state = st_brake;
}

void MotorZsx11h::forward(int val)
{
  if(m_state != st_forward)
  {
    soft_stop();
    digitalWrite(STOP, LOW);
    digitalWrite(DIR, DIR_FORWARD);
    ledcAttachPin(PWM, PWM_CHANNEL);
  }
  
  ledcWrite(PWM_CHANNEL, val);
  m_state = st_forward;
}

void MotorZsx11h::backward(int val)
{
  if(m_state != st_backward)
  {
    soft_stop();
    digitalWrite(STOP, LOW);
    digitalWrite(DIR, !DIR_FORWARD);
    ledcAttachPin(PWM, PWM_CHANNEL);
  }
  
  ledcWrite(PWM_CHANNEL, val);
  m_state = st_backward;
}
