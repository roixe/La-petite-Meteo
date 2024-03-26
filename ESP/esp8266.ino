#include <Wire.h>
#include <Adafruit_SSD1327.h>
#include <Adafruit_Sensor.h>
#include <BME280I2C.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <errno.h> 
 
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 128
#define SERVER_IP "192.168.5.34" // a changer le cas echeant 
#ifndef STASSID
//#define STASSID "SFR_6E78" // a changer le cas echeant 
//#define STAPSK "2ixen2fqf83wvdy5svi8" // a changer le cas echeant 
//#define STASSID "Iphone de Louis" // a changer le cas echeant 
//#define STAPSK "ProjetCube" // a changer le cas echeant 
#define STASSID "Gaellou" // a changer le cas echeant 
#define STAPSK "connexion56!" // a changer le cas echeant 
//#define STASSID "NOVA_D6B0" // a changer le cas echeant 
//#define STAPSK "think8696" // a changer le cas echeant 
//#define STASSID "NotreProjet" // a changer le cas echeant 
//#define STAPSK "wvnt0858" // a changer le cas echeant 
#define FLOAT_TO_INT(x) ((x)>=0?(int)((x)+0.5):(int)((x)-0.5))
#endif
 
const unsigned char epd_bitmap_temperature [] PROGMEM = {
	0x00, 0x00, 0x00, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0xff, 0x80, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x07, 0xff, 0xe0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xf0, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x1f, 0x03, 0xf8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3e, 0x00, 0xf8, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x7c, 0x00, 0x7c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x78, 0x00, 0x3c, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x78, 0x00, 0x3c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x70, 0x00, 0x3e, 0x7f, 0x80, 0x00, 
	0x00, 0x00, 0xf0, 0x00, 0x1e, 0xff, 0xc0, 0x00, 0x00, 0x00, 0xf0, 0x00, 0x1e, 0xff, 0xc0, 0x00, 
	0x00, 0x00, 0xf0, 0x00, 0x1e, 0x7f, 0x80, 0x00, 0x00, 0x00, 0xf0, 0x00, 0x1e, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0xf0, 0x00, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0x00, 0x1e, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0xf0, 0x00, 0x1e, 0x7f, 0xf0, 0x00, 0x00, 0x00, 0xf0, 0x00, 0x1e, 0xff, 0xf8, 0x00, 
	0x00, 0x00, 0xf0, 0x00, 0x1e, 0x7f, 0xf0, 0x00, 0x00, 0x00, 0xf0, 0x00, 0x1e, 0x1f, 0xe0, 0x00, 
	0x00, 0x00, 0xf0, 0x00, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0x00, 0x1e, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0xf0, 0x00, 0x1e, 0x7f, 0x80, 0x00, 0x00, 0x00, 0xf0, 0x00, 0x1e, 0xff, 0xc0, 0x00, 
	0x00, 0x00, 0xf0, 0x38, 0x1e, 0xff, 0xc0, 0x00, 0x00, 0x00, 0xf0, 0x7e, 0x1e, 0x7f, 0x80, 0x00, 
	0x00, 0x00, 0xf0, 0xff, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf1, 0xff, 0x1e, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0xf1, 0xff, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf1, 0xff, 0x1e, 0x7f, 0xf0, 0x00, 
	0x00, 0x00, 0xf1, 0xff, 0x1e, 0xff, 0xf8, 0x00, 0x00, 0x00, 0xf1, 0xff, 0x1e, 0xff, 0xf8, 0x00, 
	0x00, 0x00, 0xf1, 0xff, 0x1e, 0x7f, 0xf0, 0x00, 0x00, 0x00, 0xf1, 0xff, 0x1e, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0xf1, 0xff, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf1, 0xff, 0x1e, 0x00, 0x00, 0x00, 
	0x00, 0x01, 0xf1, 0xff, 0x1f, 0x00, 0x00, 0x00, 0x00, 0x01, 0xe1, 0xff, 0x1f, 0x80, 0x00, 0x00, 
	0x00, 0x03, 0xc1, 0xff, 0x0f, 0xc0, 0x00, 0x00, 0x00, 0x07, 0xc3, 0xff, 0x87, 0xc0, 0x00, 0x00, 
	0x00, 0x07, 0x87, 0xff, 0xe3, 0xe0, 0x00, 0x00, 0x00, 0x0f, 0x0f, 0xff, 0xe3, 0xe0, 0x00, 0x00, 
	0x00, 0x0f, 0x1f, 0xff, 0xf1, 0xe0, 0x00, 0x00, 0x00, 0x0e, 0x1f, 0xff, 0xf9, 0xf0, 0x00, 0x00, 
	0x00, 0x0e, 0x3f, 0xff, 0xf8, 0xf0, 0x00, 0x00, 0x00, 0x1e, 0x3f, 0xff, 0xf8, 0xf0, 0x00, 0x00, 
	0x00, 0x1e, 0x3f, 0xff, 0xf8, 0xf0, 0x00, 0x00, 0x00, 0x1e, 0x3f, 0xff, 0xf8, 0xf0, 0x00, 0x00, 
	0x00, 0x1e, 0x3f, 0xff, 0xf8, 0xf0, 0x00, 0x00, 0x00, 0x1e, 0x3f, 0xff, 0xf8, 0xf0, 0x00, 0x00, 
	0x00, 0x1e, 0x3f, 0xff, 0xf8, 0xf0, 0x00, 0x00, 0x00, 0x0f, 0x1f, 0xff, 0xf0, 0xf0, 0x00, 0x00, 
	0x00, 0x0f, 0x0f, 0xff, 0xf1, 0xe0, 0x00, 0x00, 0x00, 0x0f, 0x8f, 0xff, 0xe1, 0xe0, 0x00, 0x00, 
	0x00, 0x07, 0x87, 0xff, 0xc3, 0xe0, 0x00, 0x00, 0x00, 0x07, 0xc1, 0xff, 0x87, 0xc0, 0x00, 0x00, 
	0x00, 0x03, 0xe0, 0x7c, 0x0f, 0xc0, 0x00, 0x00, 0x00, 0x01, 0xf0, 0x00, 0x1f, 0x80, 0x00, 0x00, 
	0x00, 0x00, 0xfc, 0x00, 0x7f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7f, 0x01, 0xfe, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x3f, 0xff, 0xfc, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0xff, 0xf0, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x07, 0xff, 0xe0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00, 0x00
};
 
const unsigned char epd_bitmap_humidite [] PROGMEM = {
	0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x38, 0x00, 0x00, 0x00, 0x7c, 0x00, 0x00, 0x00, 0xfc, 0x00, 
	0x00, 0x00, 0xfe, 0x00, 0x00, 0x01, 0xff, 0x00, 0x00, 0x03, 0xff, 0x00, 0x00, 0x43, 0xff, 0x80, 
	0x00, 0xe7, 0xff, 0x80, 0x01, 0xf7, 0xff, 0xc0, 0x03, 0xf3, 0xff, 0xe0, 0x03, 0xf9, 0xff, 0xe0, 
	0x07, 0xfd, 0xff, 0xf0, 0x0f, 0xfe, 0xff, 0xf0, 0x1f, 0xfe, 0x7f, 0xf8, 0x1f, 0xff, 0x7f, 0xf8, 
	0x3f, 0xff, 0x3f, 0xfc, 0x3f, 0xff, 0xbf, 0xfc, 0x3f, 0xff, 0xbf, 0xfc, 0x7f, 0xfd, 0x9f, 0xfe, 
	0x7f, 0xfd, 0x9f, 0xe6, 0x7f, 0xfd, 0x9f, 0xe6, 0x3f, 0xf9, 0xbf, 0xec, 0x3f, 0xf3, 0x3f, 0xec, 
	0x1f, 0xc7, 0x7f, 0xcc, 0x0f, 0x8e, 0x7f, 0xdc, 0x07, 0xfc, 0xff, 0x98, 0x01, 0xf1, 0xfe, 0x30, 
	0x00, 0x07, 0xf8, 0xe0, 0x00, 0x0f, 0xe3, 0xc0, 0x00, 0x03, 0xff, 0x80, 0x00, 0x00, 0xfe, 0x00
};
 
const char* ssid = STASSID;
const char* password = STAPSK;
 
const char* host = "http://127.0.0.1";
const uint16_t port = 5000;
 
BME280I2C bme;
 
Adafruit_SSD1327 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
 
void setup()
{
  Wire.begin(0,2);
 
  Serial.begin(9600);
 
  BME_280_init();
 
  display_init();
 
  Serial.print("Connecting to ");
  Serial.println(ssid);
 
  delay(4000);
 
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
 
  while (WiFi.status() != WL_CONNECTED) { // Wait for the Wi-Fi to connect
    delay(4000);
    display.clearDisplay();
    display.setTextSize(1.8);
    display.setTextColor(SSD1327_WHITE);
    display.setCursor(0, 0);
    display.println("Recherche du Wifi");
    display.display();
    Serial.println("Recherche de Wifi");
  }
 
  float temperature, humidite = 0;
 
  get_data_instant(&temperature, &humidite);
  delay(2000);
  get_data_instant(&temperature, &humidite);
  display_weather_info(&temperature, &humidite);
 
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
 
}
 
void loop() 
{
  float temp_avg, hum_avg = 0;
 
  one_min_data(&temp_avg, &hum_avg);
  if (temp_avg >= -30  && temp_avg <=60 && hum_avg >= 0 && hum_avg <= 100)
  {
    if ((WiFi.status() == WL_CONNECTED)) {
      request_POST(temp_avg, hum_avg);
    }
    display_weather_info(&temp_avg, &hum_avg);
  }
}
 
void request_POST(float temp_avg, float hum_avg)
{
    WiFiClient client;
    HTTPClient http;
 
    int temp_avg_int = FLOAT_TO_INT(temp_avg);
    int hum_avg_int = FLOAT_TO_INT(hum_avg);
 
    Serial.print("[HTTP] begin...\n");
    // configure traged server and url
    //http.begin(client, "http://172.20.10.9:5000/releve");  // HTTP
    //http.begin(client, "http://lapetitemeteo/releve");
    http.begin(client, "http://192.168.43.134:5000/releve");
    http.addHeader("Content-Type", "application/json");
 
    char payload[100];
    sprintf(payload, "{\"temperature\":\%d,\"humidity\":\%d,\"MAC\":\"\%s\"}", temp_avg_int, hum_avg_int, WiFi.macAddress().c_str());
    Serial.println(payload);
    int httpCode = http.POST(payload);
    //int httpCode = http.GET();
 
    // httpCode will be negative on error
    if (httpCode > 0) {
      // HTTP header has been send and Server response header has been handled
      Serial.printf("[HTTP] POST... code: %d\n", httpCode);
 
      // file found at server
      if (httpCode == HTTP_CODE_OK)
      {
        const String& payload = http.getString();
        Serial.println("received payload:\n<<");
        Serial.println(payload);
        Serial.println(">>");
      }
    } 
    else {
      Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
    }
 
    http.end();
}
 
void get_data_instant(float* temperature, float* humidite)
{
  BME280::TempUnit tempUnit(BME280::TempUnit_Celsius);
  *temperature = bme.temp();
  *humidite = bme.hum();
}
 
void one_min_data(float* temp_avg, float* hum_avg)
{
  BME280::TempUnit tempUnit(BME280::TempUnit_Celsius);
  BME280::PresUnit presUnit(BME280::PresUnit_hPa);
 
  for(int count = 0; count < 5; count++)
  {
    float temp(NAN), hum(NAN);
    temp = bme.temp();
    hum = bme.hum();
    if (temp >= -30  && temp <=60 && hum >= 0 && hum <= 100)
    {
      *temp_avg += temp;
      *hum_avg += hum;
      delay(12000);
    }
    else
    {
      count--;
    }
  }
  *temp_avg /= 5;
  *hum_avg /= 5;
}
 
void display_weather_info(float *temp, float *hum)
{
 
   // Clear the OLED display
  display.clearDisplay();
 
  display.setTextSize(1);
  display.setTextColor(SSD1327_WHITE);
  display.drawBitmap(-5,0, epd_bitmap_temperature, 64, 64,SSD1327_WHITE);
  display.setTextSize(2);
  display.setCursor(55, 20);
  display.print(*temp, 2);
  display.println("C");
 
  display.drawBitmap(5,80, epd_bitmap_humidite, 32, 32,SSD1327_WHITE);
  display.setTextSize(1);
  display.setCursor(50, 90);
  display.setTextSize(2);
  display.print(*hum, 2);
  display.println("%");
 
  display.setCursor(15, 120);
  display.setTextSize(1);
  display.printf("IP: %s", WiFi.localIP().toString().c_str());
 
  if ((WiFi.status() != WL_CONNECTED)) {
    display.setTextSize(1);
    display.setCursor(0, 80);
    display.println("Not connected to wifi");
  }
 
  // Display on OLED
  display.display();
}
 
void BME_280_init()
{
  if (!bme.begin())
  {
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    delay(1000);
  }
 
  switch(bme.chipModel())
  {
     case BME280::ChipModel_BME280:
       Serial.println(F("Found BME280 sensor! Success."));
       break;
     default:
       Serial.println(F("Found UNKNOWN sensor! Error!"));
  }
}
 
void display_init()
{
  if (!display.begin(0x3D))
  {
    Serial.println(F("SSD1327 allocation failed"));
  }
  else
  {
    display.setTextSize(1.8);
    display.setTextColor(SSD1327_WHITE);
    display.setCursor(0, 0);
    display.println("Initialisation en cours ...");
  }
  display.display();
  return;
}