#include <Arduino.h>

constexpr int VCC_CUT_PIN = 15;
constexpr int V5_CUT_PIN = 19;
constexpr int V12_CUT_PIN = 4;
constexpr int V12_CUT2_PIN = 5;

constexpr int ML_PWM_PIN = 26;
constexpr int ML_DIR_PIN = 27;
constexpr int ML_STOP_PIN = 25;
constexpr int ML_A = 34;
constexpr int ML_B = 23;
constexpr int ML_C = 18;

constexpr int MR_PWM_PIN = 12;
constexpr int MR_DIR_PIN = 13;
constexpr int MR_STOP_PIN = 14;
constexpr int MR_A = 33;
constexpr int MR_B = 32;
constexpr int MR_C = 35;

constexpr int VCC_ADC_PIN = 36;

int64_t prev_cycle = 0;
volatile int64_t cur_cycle = 0;
volatile int cycle_diff = 0;
int64_t printed_cycle = 0;
volatile int min_cycle_diff = std::numeric_limits<int>::max();
volatile int max_cycle_diff = std::numeric_limits<int>::min();

float cpu_freq = 0.0;
uint32_t pwm_duty = 0;
constexpr int pwm_bits=10;

constexpr float WHEEL_PULSES_PER_ROTATION=90.0;
constexpr float WHEEL_DIAMETER=6.5*0.0254; //meters
constexpr float WHEEL_PERIMETER=M_PI*WHEEL_DIAMETER;
constexpr float WHEEL_PULSES_PER_METER=WHEEL_PULSES_PER_ROTATION/WHEEL_PERIMETER;

static constexpr int hall2idx[]={-1,4,2,3,0,5,1,-1};
int m_hall_idx = 0;

constexpr unsigned TIMER_MS=10;
static constexpr unsigned PERIODS_COUNT = 50;
static constexpr float KPER_SEC=1000.0/(PERIODS_COUNT*TIMER_MS);

unsigned m_timer_val=0;
int m_periods[PERIODS_COUNT];
int m_speed_ticks_count = 0;

int last_increase = 0;

double cpu_speed_sum = 0.0;
double timer_speed_sum = 0.0;
unsigned measures_count=0;

void enablePowerModules(bool power_on)
{
  int val = power_on? HIGH: LOW;
  digitalWrite(VCC_CUT_PIN, val);
  //digitalWrite(V5_CUT_PIN, val);
  //digitalWrite(V12_CUT_PIN, val);
  //digitalWrite(V12_CUT2_PIN, val);
}

void setupPowerPins()
{
  enablePowerModules(false);
  
  pinMode(VCC_CUT_PIN, OUTPUT);
  pinMode(V5_CUT_PIN, OUTPUT);
  pinMode(V12_CUT_PIN, OUTPUT);
  pinMode(V12_CUT2_PIN, OUTPUT);
}

void allOtherPinsToInputState()
{
  pinMode(ML_PWM_PIN, INPUT);
  pinMode(ML_DIR_PIN, INPUT);
  pinMode(ML_STOP_PIN, INPUT);
  pinMode(ML_A, INPUT);
  pinMode(ML_B, INPUT);
  pinMode(ML_C, INPUT);

  pinMode(MR_PWM_PIN, INPUT);
  pinMode(MR_DIR_PIN, INPUT);
  pinMode(MR_STOP_PIN, INPUT);
  pinMode(MR_A, INPUT);
  pinMode(MR_B, INPUT);
  pinMode(MR_C, INPUT);

  pinMode(VCC_ADC_PIN, INPUT);
}

void runLeftMotor()
{
  pinMode(ML_STOP_PIN, OUTPUT);
  pinMode(ML_DIR_PIN, OUTPUT);
  pinMode(ML_PWM_PIN, OUTPUT);

  ledcSetup(0, 20000, pwm_bits);
  digitalWrite(ML_STOP_PIN, LOW);
  digitalWrite(ML_DIR_PIN, HIGH);
  ledcAttachPin(ML_PWM_PIN, 0);
  
  ledcWrite(0, pwm_duty);
}

int readHallIndex()
{
  unsigned st = (digitalRead(ML_A) == HIGH) | ((digitalRead(ML_B) == HIGH)<<1) | ((digitalRead(ML_C) == HIGH)<<2);
  return hall2idx[st];
}

void speed_by_CPU()
{
  prev_cycle = cur_cycle;
  cur_cycle = ESP.getCycleCount();

  cycle_diff = static_cast<int>(cur_cycle-prev_cycle);

  min_cycle_diff = min(min_cycle_diff,cycle_diff);
  max_cycle_diff = max(max_cycle_diff,cycle_diff);
}

void speed_by_timer()
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
  m_speed_ticks_count += d;
}

void IRAM_ATTR left_tick_isr()
{
  speed_by_CPU();
  speed_by_timer();
}

void IRAM_ATTR right_tick_isr()
{
//  ++ticks_count;
}

void IRAM_ATTR SpeedTimer_ISR()
{
  unsigned timer_val = m_timer_val + 1;

  unsigned new_pi=timer_val%PERIODS_COUNT;
  unsigned old_pi=m_timer_val%PERIODS_COUNT;

  if(new_pi != old_pi)
  {
    m_speed_ticks_count-=m_periods[new_pi];
    m_periods[new_pi] = 0;
  }

  m_timer_val = timer_val;
}

void setup() {
  allOtherPinsToInputState();
  // initialize serial communication at 115200 bits per second:
  Serial.begin(115200);

  cpu_freq = ESP.getCpuFreqMHz()*1000000.0;

  setupPowerPins();
  
  enablePowerModules(true);

  m_hall_idx = readHallIndex();
  
  hw_timer_t *speed_timer = timerBegin(0, 80, true);
  timerAttachInterrupt(speed_timer, &SpeedTimer_ISR, true);
  timerAlarmWrite(speed_timer, TIMER_MS*1000, true);
  timerAlarmEnable(speed_timer);

  attachInterrupt(digitalPinToInterrupt(ML_A), left_tick_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ML_B), left_tick_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ML_C), left_tick_isr, CHANGE);

  //attachInterrupt(digitalPinToInterrupt(MR_A), right_tick_isr, CHANGE);
  //attachInterrupt(digitalPinToInterrupt(MR_B), right_tick_isr, CHANGE);
  //attachInterrupt(digitalPinToInterrupt(MR_C), right_tick_isr, CHANGE);

  runLeftMotor();
}

float get_speed_by_timer()
{
  return m_speed_ticks_count*KPER_SEC/WHEEL_PULSES_PER_METER;
}

void print_speed()
{
  if(printed_cycle == cur_cycle)
    return;

  int diff = cycle_diff;
  float seconds = diff/cpu_freq;
  float speed = 1.0/WHEEL_PULSES_PER_METER/seconds;

  float timer_speed = get_speed_by_timer();

  cpu_speed_sum += speed;
  timer_speed_sum += timer_speed;
  ++measures_count;

  double avg_cpu_speed = cpu_speed_sum / measures_count;
  double avg_timer_speed = timer_speed_sum / measures_count;

  //Serial.printf("cycle_diff=%u pwm_duty=%u seconds=%f speed=%f(%lf) timer_speed=%f(%lf) \n",diff, pwm_duty, seconds, speed,avg_cpu_speed, timer_speed,avg_timer_speed);

  printed_cycle = cur_cycle;
}

void increase_pwm()
{
  int ms = millis();
  if(ms-last_increase<5000)
    return;
  
  last_increase = ms;

  double avg_cpu_speed = cpu_speed_sum / measures_count;
  double avg_timer_speed = timer_speed_sum / measures_count;

  cpu_speed_sum = 0.0;
  timer_speed_sum = 0.0;
  measures_count=0;
  
  int min_cycle = min_cycle_diff;
  int max_cycle = max_cycle_diff;

  float max_speed = 1.0/WHEEL_PULSES_PER_METER/(min_cycle/cpu_freq);
  float min_speed = 1.0/WHEEL_PULSES_PER_METER/(max_cycle/cpu_freq);

  min_cycle_diff = std::numeric_limits<int>::max();
  max_cycle_diff = std::numeric_limits<int>::min();

  pwm_duty += 32;
  pwm_duty %= (1<<pwm_bits);

  uint32_t diff = ESP.getCycleCount() - cur_cycle;
  bool do_reset = diff*1.0>cpu_freq;

  if(do_reset)
  {
    digitalWrite(ML_STOP_PIN, HIGH);
    delay(100);
  }
  
  ledcWrite(0, pwm_duty);
  Serial.printf("increase_pwm(): min_speed=%lf (%d) max_speed=%lf (%d)\n", min_speed, max_cycle, max_speed, min_cycle);
  Serial.printf("increase_pwm(): prev:(cpu_speed=%lf timer_speed=%lf) pwm_duty=%u diff=%u do_reset=%d\n", avg_cpu_speed,avg_timer_speed, pwm_duty, diff, do_reset);

  if(do_reset)
    digitalWrite(ML_STOP_PIN, LOW);
}

void loop()
{
  print_speed();
  increase_pwm();
}
