# 🏠 Smart Home Automation Project (NodeMCU + Python Dashboard + Voice Control)

## 📦 Components
- NodeMCU ESP8266
- DHT11 Sensor
- 2-Channel Relay (for Light/Fan)
- LCD 16x2 (I2C)
- Python Dashboard with Voice Control

## ⚙️ Setup
### 1️⃣ Arduino
- Open `Arduino_Code/SmartHome_NodeMCU.ino` in Arduino IDE
- Install libraries: ESP8266WiFi, ESP8266WebServer, DHT, LiquidCrystal_I2C
- Upload to NodeMCU
- Note down the IP shown in Serial Monitor

### 2️⃣ Python Dashboard
```bash
pip install -r requirements.txt
python Python_Dashboard/smart_home_voice_dashboard.py
```
- Open browser at http://127.0.0.1:8050
- Click buttons or use **🎤 Speak Command** to control devices

Enjoy controlling your home with **your voice and browser!**
