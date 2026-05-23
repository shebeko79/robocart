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
  uint32_t cur_clock = ESP.getCycleCount();

  int hall_idx = readHallIndex();

  //Incorrect state of hall sensors
  if(hall_idx == -1)
    return;

  int d = hall_idx - m_hall_idx;
  if(std::abs(d)>3)
    d += 6*(d<0) -6*(d>0);

  m_hall_idx = hall_idx;

  if(m_empty_speed)
  {
    m_empty_speed = false;
    
    m_directions[0]=m_directions[1]= 0;
    m_directions[2] = d;
    m_direction=d;

    m_cpu_clock[0]=m_cpu_clock[1]=m_cpu_clock[2]=m_cpu_clock[3]=cur_clock;
    m_cpu_diff = 0;
    return;
  }

  m_ticks_count += d;

  m_direction -= m_directions[0];
  m_direction += d;

  m_directions[0]=m_directions[1];
  m_directions[1]=m_directions[2];
  m_directions[2]=d;

  m_cpu_clock[0]=m_cpu_clock[1];
  m_cpu_clock[1]=m_cpu_clock[2];
  m_cpu_clock[2]=m_cpu_clock[3];
  m_cpu_clock[3] = cur_clock;

  //Substruct all intervals to avoid overflow
  uint32_t diff = m_cpu_clock[1] - m_cpu_clock[0];
  diff += m_cpu_clock[2] - m_cpu_clock[1];
  diff += cur_clock - m_cpu_clock[2];

  m_cpu_diff = diff;
}

int MotorZsx11h::readHallIndex()
{
  unsigned st = (digitalRead(m_hall_a) == HIGH) | ((digitalRead(m_hall_b) == HIGH)<<1) | ((digitalRead(m_hall_c) == HIGH)<<2);
  return hall2idx[st];
}

void MotorZsx11h::check_speed_timeout()
{
  unsigned long cur_ms = millis();
  if(m_empty_speed)
  {
    m_speed = 0.0;
    m_last_clk_ms = cur_ms;
    return;
  }

  uint32_t diff = m_cpu_diff;
  int d = m_direction;
  uint32_t last_clk = m_cpu_clock[3];

  //Try to avoid inconsitency
  while(true)
  {
    uint32_t diff_new = m_cpu_diff;
    int d_new = m_direction;
    uint32_t last_clk_new = m_cpu_clock[3];
    
    if(diff==diff_new && d == d_new && last_clk == last_clk_new)
      break;
    
    diff = diff_new;
    d = d_new;
    last_clk = last_clk_new;
  }

  unsigned long ms_diff = 0;

  if(m_last_clk != last_clk)
  {
    m_last_clk = last_clk;
    m_last_clk_ms = cur_ms;
  }
  else
  {
    if(diff == 0)
      ms_diff = MAIN_CYCLE_DELAY;
    else
      ms_diff = cur_ms-m_last_clk_ms;

    if(ms_diff>=SPEED_TIMEOUT_MS)
    {
      m_speed = 0.0;
      m_last_clk_ms = cur_ms;
      m_empty_speed = true;
      //Serial.printf("cut to zero: cur_ms=%u m_last_clk_ms=%u ms_diff=%u\n", cur_ms,m_last_clk_ms,ms_diff);
      return;
    }
  }

  float speed = 0.0;

  if(diff > 0)
  {
    speed = m_cpu_freq*d/WHEEL_PULSES_PER_METER/diff;
    //Serial.printf("last_clk=%u diff=%u d=%d speed=%f d0=%d d1=%d d2=%d\n", last_clk, diff, d, speed,m_directions[0],m_directions[1],m_directions[2]);
  }

  if(ms_diff>0)
  {
    int ms_d = (d>=0)? 1:-1;
    float ms_speed = ms_d/WHEEL_PULSES_PER_METER/ms_diff*1000;

    if(diff == 0 || abs(speed)>abs(ms_speed)*2)
    {
      //Serial.printf("last_clk=%u diff=%u d=%d speed=%f ms_speed=%f\n", last_clk, diff, d, speed, ms_speed);
      speed = ms_speed;
    }
  }

  m_speed = (DIR_FORWARD? 1.0:-1.0)*speed;
}

float MotorZsx11h::get_blind_ms(double speed)
{
  return 1.0/WHEEL_PULSES_PER_METER/speed*1000;
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

  m_cpu_freq = ESP.getCpuFreqMHz()*1000000.0;

  ledcSetup(PWM_CHANNEL, 20000, PWM_BITS);
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
