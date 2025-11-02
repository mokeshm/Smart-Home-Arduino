#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------------- Pin Definitions ----------------
#define DHTPIN D4
#define DHTTYPE DHT11
#define RELAY1 D5     // Light
#define RELAY2 D6     // Fan
#define IRSENSOR D7   // IR Sensor

// ---------------- WiFi Credentials ----------------
const char* ssid = "Airtel_mokeshm";
const char* password = "Nobinobita@1";

// ---------------- Objects ----------------
ESP8266WebServer server(80);
DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ---------------- States ----------------
bool lightState = false;
bool fanState = false;
bool irDetected = false;
unsigned long lastSensorRead = 0;
float temperature = 0, humidity = 0;

// ---------------- LCD Update ----------------
void updateLCD() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("L:");
  lcd.print(lightState ? "ON " : "OFF");
  lcd.setCursor(7, 0);
  lcd.print("F:");
  lcd.print(fanState ? "ON" : "OFF");
  lcd.setCursor(0, 1);
  lcd.print(String(temperature, 1) + "C " + String(humidity, 0) + "%");
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(115200);

  lcd.init();
  lcd.backlight();
  lcd.print("Connecting WiFi");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.println(WiFi.localIP());
  lcd.clear();
  lcd.print("WiFi Connected");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP().toString());
  delay(1500);

  dht.begin();
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  pinMode(IRSENSOR, INPUT);
  digitalWrite(RELAY1, HIGH);
  digitalWrite(RELAY2, HIGH);
  updateLCD();

  // ---------------- Web Routes ----------------
  server.on("/", []() {
    String html = "<h2>Smart Home NodeMCU</h2>";
    html += "<p><a href='/light_on'>Light ON</a> | <a href='/light_off'>Light OFF</a></p>";
    html += "<p><a href='/fan_on'>Fan ON</a> | <a href='/fan_off'>Fan OFF</a></p>";
    html += "<p><a href='/get_data'>Get JSON Data</a></p>";
    server.send(200, "text/html", html);
  });

  server.on("/light_on", []() {
    digitalWrite(RELAY1, LOW);
    lightState = true;
    updateLCD();
    server.send(200, "text/plain", "Light ON");
  });

  server.on("/light_off", []() {
    digitalWrite(RELAY1, HIGH);
    lightState = false;
    updateLCD();
    server.send(200, "text/plain", "Light OFF");
  });

  server.on("/fan_on", []() {
    digitalWrite(RELAY2, LOW);
    fanState = true;
    updateLCD();
    server.send(200, "text/plain", "Fan ON");
  });

  server.on("/fan_off", []() {
    digitalWrite(RELAY2, HIGH);
    fanState = false;
    updateLCD();
    server.send(200, "text/plain", "Fan OFF");
  });

  server.on("/get_data", []() {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) {
      temperature = t;
      humidity = h;
    }
    String json = "{\"temperature\":" + String(temperature, 1) +
                  ",\"humidity\":" + String(humidity, 1) + "}";
    server.send(200, "application/json", json);
  });

  server.on("/lcd", []() {
    if (server.hasArg("text")) {
      String msg = server.arg("text");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print(msg.substring(0, 16));
      if (msg.length() > 16) {
        lcd.setCursor(0, 1);
        lcd.print(msg.substring(16, 32));
      }
      server.send(200, "text/plain", "LCD Updated");
    } else {
      server.send(400, "text/plain", "No text provided");
    }
  });

  server.begin();
  Serial.println("HTTP server started");
}

// ---------------- Loop ----------------
void loop() {
  server.handleClient();

  unsigned long currentMillis = millis();
  if (currentMillis - lastSensorRead > 3000) {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t) && !isnan(h)) {
      temperature = t;
      humidity = h;
    }
    lastSensorRead = currentMillis;
    updateLCD();
  }
}
