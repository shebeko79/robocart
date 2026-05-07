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

float cpu_freq = 0.0;
uint32_t pwm_duty = 0;
constexpr int pwm_bits=10;
constexpr int max_pwm=(1<<pwm_bits) - 1;

float avg_speed = 0.0;

constexpr float WHEEL_PULSES_PER_ROTATION=90.0;
constexpr float WHEEL_DIAMETER=6.5*0.0254; //meters
constexpr float WHEEL_PERIMETER=M_PI*WHEEL_DIAMETER;
constexpr float WHEEL_PULSES_PER_METER=WHEEL_PULSES_PER_ROTATION/WHEEL_PERIMETER;

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

int last_increase = 0;

void increase_pwm()
{
  int ms = millis();
  if(ms-last_increase<50)
    return;
  
  last_increase = ms;

  ++pwm_duty;
  pwm_duty %= max_pwm;

  uint32_t diff = ESP.getCycleCount() - cur_cycle;
  bool do_reset = diff*1.0>cpu_freq;

  if(do_reset)
  {
    digitalWrite(ML_STOP_PIN, HIGH);
    delay(100);
  }
  
  ledcWrite(0, pwm_duty);
  Serial.printf("increase_pwm(): prev_avg_speed=%f pwm_duty=%u diff=%u do_reset=%d\n", avg_speed, pwm_duty, diff, do_reset);

  if(do_reset)
    digitalWrite(ML_STOP_PIN, LOW);
}


void IRAM_ATTR left_tick_isr()
{
  prev_cycle = cur_cycle;
  cur_cycle = ESP.getCycleCount();

  cycle_diff = static_cast<int>(cur_cycle-prev_cycle);
}

void IRAM_ATTR right_tick_isr()
{
//  ++ticks_count;
}

void setup() {
  allOtherPinsToInputState();
  // initialize serial communication at 115200 bits per second:
  Serial.begin(115200);

  cpu_freq = ESP.getCpuFreqMHz()*1000000.0;

  setupPowerPins();
  
  enablePowerModules(true);

  attachInterrupt(digitalPinToInterrupt(ML_A), left_tick_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ML_B), left_tick_isr, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ML_C), left_tick_isr, CHANGE);

  //attachInterrupt(digitalPinToInterrupt(MR_A), right_tick_isr, CHANGE);
  //attachInterrupt(digitalPinToInterrupt(MR_B), right_tick_isr, CHANGE);
  //attachInterrupt(digitalPinToInterrupt(MR_C), right_tick_isr, CHANGE);

  runLeftMotor();
}

void print_speed()
{
  if(printed_cycle == cur_cycle)
    return;

  int diff = cycle_diff;
  float seconds = diff/cpu_freq;
  float speed = 1.0/WHEEL_PULSES_PER_METER/seconds;

  avg_speed = (avg_speed+speed)/2.0;

  //Serial.printf("cycle_diff=%u pwm_duty=%u seconds=%f speed=%f m/s\n",diff, pwm_duty, seconds, speed);

  printed_cycle = cur_cycle;
}


void loop()
{
  print_speed();
  increase_pwm();
}
