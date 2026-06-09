//Board LOLIN D32
#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>

uint8_t broadcastAddress[] = {
#include "esp_now_robocart_mac.h"  
};

#define REMOTE_NAME "rccar"

#define VRX_PIN  32
#define VRY_PIN  33
#define BUTTON_PIN  35
#define LED 22

int central_minx=0;
int central_maxx=0;
int central_miny=0;
int central_maxy=0;

float last_vx = 0.0;
float last_vy = 0.0;
unsigned long last_send_time=0;
bool send_clear = true;

esp_now_peer_info_t peerInfo;


bool processCommand(const char* buf);
void detectCentralPoint();

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status);
void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len);


void setup() 
{
  Serial.begin(115200);

  pinMode(BUTTON_PIN ,INPUT_PULLUP);

  analogSetAttenuation(ADC_11db);

  pinMode(LED,OUTPUT);
  digitalWrite(LED,LOW);  
  delay(500);
  digitalWrite(LED,HIGH);  

  detectCentralPoint();

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK)
    Serial.println("esp_now_init() failed");
  
  memcpy(peerInfo.peer_addr, broadcastAddress, sizeof(broadcastAddress));
  peerInfo.channel = 0;  
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK)
    Serial.println("esp_now_add_peer() failed");

  esp_now_register_send_cb(OnDataSent);
  esp_now_register_recv_cb(OnDataRecv);
}

void detectCentralPoint()
{
  central_minx = central_maxx = analogRead(VRX_PIN);
  central_miny = central_maxy = analogRead(VRY_PIN);
  
  for(int i=0;i<50;i++)
  {
    int x = analogRead(VRX_PIN);
    int y = analogRead(VRY_PIN);

    if(x<central_minx)
      central_minx = x;
    else if(x>central_maxx)
      central_maxx = x;

    if(y<central_miny)
      central_miny = y;
    else if(y>central_maxy)
      central_maxy = y;
    
    delay(50);
  }

  central_minx-=30;
  central_maxx+=30;
  central_miny-=30;
  central_maxy+=30;

  Serial.print("CenterX=[");
  Serial.print(central_minx);
  Serial.print(",");
  Serial.print(central_maxx);
  Serial.println("]");

  Serial.print("CenterY=[");
  Serial.print(central_miny);
  Serial.print(",");
  Serial.print(central_maxy);
  Serial.println("]");
}

void sendData(const String& str)
{
  send_clear = false;
  
  esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *) str.c_str(), str.length());
  Serial.printf("sendData(): %d\n",result);
}

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status)
{
}

void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len)
{
  String s(incomingData,len);
  Serial.printf("%02x:%02x:%02x:%02x:%02x:%02x msg=%s",
    mac[0],mac[1],mac[2],mac[3],mac[4],mac[5],
    s.c_str());
  
  if(memcmp(mac,broadcastAddress,sizeof(broadcastAddress))==0)
    send_clear = true;
}

float convert(int val,int central_min,int central_max)
{
  if(val<central_min)
  {
    return 1.0*(val-(central_min-1))/(central_min-1);
  }

  if(val>central_max)
  {
    return 1.0*(val-(central_max+1))/(4095-(central_max+1));
  }

  return 0.0;
}

void processJoystick()
{
  // read X and Y analog values
  int x = analogRead(VRX_PIN);
  int y = analogRead(VRY_PIN);

  float vx = convert(x,central_minx,central_maxx);
  float vy = convert(y,central_miny,central_maxy);

  unsigned long cur_time=millis();

  const bool is_timeout = send_clear&&cur_time-last_send_time>=250 || !send_clear&&cur_time-last_send_time>=500;

  //Serial.printf("processJoystick()is_timeout=%d send_clear=%d diff=%d\n",is_timeout,send_clear,cur_time-last_send_time);

  if(last_vx==vx && last_vy==vy && !is_timeout)
    return;

  last_send_time=cur_time;
  last_vx=vx;
  last_vy=vy;

  String str = "cmd:"REMOTE_NAME":drive:";
  str+=String(vy);
  str+=";";
  str+=String(vx);
  str+="\r";

  if(vx!=0.0 || vy!=0.0)
    Serial.println(str);
    
  sendData(str);
}

void processButton()
{
  if(digitalRead(BUTTON_PIN) != LOW)
    return;

  // read X and Y analog values
  int x = analogRead(VRX_PIN);
  int y = analogRead(VRY_PIN);

  float vx = convert(x,central_minx,central_maxx);
  float vy = convert(y,central_miny,central_maxy);

  if(vx!=0.0 || vy!=0.0)
    return;

  //Serial.print("vx=");
  //Serial.print(vx);
  //Serial.print(" vy=");
  //Serial.println(vy);

  String str = "cmd:"REMOTE_NAME":block:0\r";

  Serial.println(str);
  sendData(str);
  delay(1000);
}

void loop()
{
  processJoystick();
  processButton();
  delay(50);
}
