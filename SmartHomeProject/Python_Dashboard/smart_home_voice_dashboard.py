import requests
import speech_recognition as sr
from flask import Flask
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import threading
import datetime
import json

# ---------------- NODEMCU CONFIG ----------------
NODEMCU_IP = "http://192.168.1.8"  # Change to your NodeMCU IP address

# ---------------- DASH APP SETUP ----------------
app = dash.Dash(__name__)
server = app.server

# Global data for plotting
temp_data, hum_data, time_data = [], [], []

# ---------------- CUSTOM DARK STYLE ----------------
dark_style = {
    'backgroundColor': '#0e1117',
    'color': '#e0e0e0',
    'fontFamily': 'Segoe UI, sans-serif',
    'padding': '20px'
}

button_style = {
    'padding': '12px 25px',
    'borderRadius': '10px',
    'border': 'none',
    'color': 'white',
    'fontWeight': 'bold',
    'fontSize': '16px',
    'cursor': 'pointer',
    'boxShadow': '0px 0px 8px rgba(0,255,200,0.6)',
    'transition': '0.3s',
}

# ---------------- DASH LAYOUT ----------------
app.layout = html.Div(style=dark_style, children=[
    html.H1("💡 Smart Home Dashboard",
            style={'textAlign': 'center', 'color': '#00FFFF', 'marginBottom': '25px'}),

    html.Div([
        html.Button("Light ON", id="light_on", n_clicks=0,
                    style={**button_style, 'background': '#00C853'}),
        html.Button("Light OFF", id="light_off", n_clicks=0,
                    style={**button_style, 'background': '#FF1744'}),
        html.Button("Fan ON", id="fan_on", n_clicks=0,
                    style={**button_style, 'background': '#2979FF'}),
        html.Button("Fan OFF", id="fan_off", n_clicks=0,
                    style={**button_style, 'background': '#9E9E9E'}),
        html.Button("🎤 Speak", id="voice_btn", n_clicks=0,
                    style={**button_style, 'background': '#FFEA00', 'color': '#212121'}),
    ], style={'display': 'flex', 'gap': '15px', 'justifyContent': 'center', 'marginBottom': '35px'}),

    html.Div(id="sensor_data", style={'textAlign': 'center', 'fontSize': '20px', 'marginBottom': '20px'}),

    html.Div([
        dcc.Graph(id='temp_graph', style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(id='hum_graph', style={'width': '48%', 'display': 'inline-block'}),
    ], style={'textAlign': 'center'}),

    html.H4("💬 Send Message to LCD",
            style={'textAlign': 'center', 'color': '#00E5FF', 'marginTop': '40px'}),
    html.Div([
        dcc.Input(id="lcd_text", type="text", placeholder="Enter text for LCD",
                  style={'width': '50%', 'padding': '10px', 'borderRadius': '8px',
                         'border': '1px solid #00FFFF', 'background': '#1c1f26', 'color': '#fff'}),
        html.Button("Send", id="send_lcd", n_clicks=0,
                    style={**button_style, 'background': '#00BCD4', 'marginLeft': '10px'}),
    ], style={'textAlign': 'center', 'marginTop': '10px'}),

    html.Div(id="lcd_status", style={'textAlign': 'center', 'color': '#00E676',
                                     'marginTop': '10px', 'fontWeight': 'bold'}),

    html.H4("🎙️ Voice Command Output",
            style={'marginTop': '40px', 'textAlign': 'center', 'color': '#FFAB40'}),
    html.Div(id="voice_output",
             style={'fontSize': '20px', 'textAlign': 'center', 'color': '#E0E0E0'}),

    dcc.Interval(id='interval', interval=5000, n_intervals=0)
])

# ---------------- SENSOR DATA UPDATE ----------------
@app.callback(
    [Output("sensor_data", "children"),
     Output("temp_graph", "figure"),
     Output("hum_graph", "figure")],
    Input("interval", "n_intervals")
)
def update_sensor(n):
    global temp_data, hum_data, time_data
    try:
        res = requests.get(f"{NODEMCU_IP}/get_data", timeout=3)
        data_text = res.text.strip()

        temp, hum = None, None

        # Handle multiple possible formats:
        try:
            # If JSON like {"temperature":28.5,"humidity":60}
            parsed = json.loads(data_text)
            temp = float(parsed.get("temperature", 0))
            hum = float(parsed.get("humidity", 0))
        except:
            # Try plain text formats
            if ',' in data_text:
                parts = data_text.replace('°C', '').replace('%', '').split(',')
                temp = float(parts[0])
                hum = float(parts[1])
            elif 'Temperature' in data_text:
                for part in data_text.split(','):
                    if "Temperature" in part:
                        temp = float(part.split(':')[1].replace('°C', '').strip())
                    if "Humidity" in part:
                        hum = float(part.split(':')[1].replace('%', '').strip())

        if temp is not None and hum is not None:
            temp_data.append(temp)
            hum_data.append(hum)
            time_data.append(datetime.datetime.now().strftime("%H:%M:%S"))

            # Limit history to 20 points
            if len(temp_data) > 20:
                temp_data.pop(0)
                hum_data.pop(0)
                time_data.pop(0)

        temp_fig = {
            'data': [{'x': time_data, 'y': temp_data, 'type': 'line',
                      'name': 'Temperature (°C)', 'line': {'color': '#00E5FF', 'width': 3}}],
            'layout': {'paper_bgcolor': '#0e1117', 'plot_bgcolor': '#0e1117',
                       'font': {'color': '#E0E0E0'}, 'title': '🌡️ Temperature Monitor'}
        }

        hum_fig = {
            'data': [{'x': time_data, 'y': hum_data, 'type': 'line',
                      'name': 'Humidity (%)', 'line': {'color': '#FF9100', 'width': 3}}],
            'layout': {'paper_bgcolor': '#0e1117', 'plot_bgcolor': '#0e1117',
                       'font': {'color': '#E0E0E0'}, 'title': '💧 Humidity Monitor'}
        }

        return f"Temperature: {temp}°C | Humidity: {hum}%", temp_fig, hum_fig

    except Exception as e:
        print("Error reading NodeMCU:", e)
        return "⚠️ NodeMCU not responding", dash.no_update, dash.no_update

# ---------------- LCD TEXT SENDER ----------------
@app.callback(Output("lcd_status", "children"),
              Input("send_lcd", "n_clicks"),
              State("lcd_text", "value"),
              prevent_initial_call=True)
def send_lcd_text(n_clicks, text):
    if not text:
        return "❌ Please enter text!"
    try:
        requests.get(f"{NODEMCU_IP}/lcd", params={"text": text})
        return f"✅ Sent to LCD: {text}"
    except Exception as e:
        return f"⚠️ Error: {e}"

# ---------------- DEVICE + VOICE CONTROL ----------------
@app.callback(
    Output("voice_output", "children"),
    [Input("light_on", "n_clicks"),
     Input("light_off", "n_clicks"),
     Input("fan_on", "n_clicks"),
     Input("fan_off", "n_clicks"),
     Input("voice_btn", "n_clicks")],
    prevent_initial_call=True
)
def control_devices(l_on, l_off, f_on, f_off, voice):
    import dash
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""
    button = ctx.triggered[0]['prop_id'].split('.')[0]

    try:
        if button == "light_on":
            requests.get(f"{NODEMCU_IP}/light_on")
            return "🟢 Light turned ON"
        elif button == "light_off":
            requests.get(f"{NODEMCU_IP}/light_off")
            return "🔴 Light turned OFF"
        elif button == "fan_on":
            requests.get(f"{NODEMCU_IP}/fan_on")
            return "🌀 Fan turned ON"
        elif button == "fan_off":
            requests.get(f"{NODEMCU_IP}/fan_off")
            return "🌀 Fan turned OFF"
        elif button == "voice_btn":
            threading.Thread(target=voice_control).start()
            return "🎤 Listening..."
    except Exception as e:
        return f"⚠️ Error: {e}"

# ---------------- VOICE CONTROL ----------------
def voice_control():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎧 Listening for voice command...")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio).lower()
            print("You said:", text)

            if "light on" in text:
                requests.get(f"{NODEMCU_IP}/light_on")
                requests.get(f"{NODEMCU_IP}/lcd", params={"text": "Light ON"})
            elif "light off" in text:
                requests.get(f"{NODEMCU_IP}/light_off")
                requests.get(f"{NODEMCU_IP}/lcd", params={"text": "Light OFF"})
            elif "fan on" in text:
                requests.get(f"{NODEMCU_IP}/fan_on")
                requests.get(f"{NODEMCU_IP}/lcd", params={"text": "Fan ON"})
            elif "fan off" in text:
                requests.get(f"{NODEMCU_IP}/fan_off")
                requests.get(f"{NODEMCU_IP}/lcd", params={"text": "Fan OFF"})
            elif "temperature" in text or "humidity" in text:
                data = requests.get(f"{NODEMCU_IP}/get_data").text
                requests.get(f"{NODEMCU_IP}/lcd", params={"text": data})
                print(data)
            else:
                requests.get(f"{NODEMCU_IP}/lcd", params={"text": "Unknown Cmd"})
                print("Command not recognized.")
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
        except Exception as e:
            print("⚠️ Error:", e)

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app.run(debug=True)
