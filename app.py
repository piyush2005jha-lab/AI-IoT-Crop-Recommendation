from flask import Flask, render_template, jsonify, request, send_from_directory
import serial, threading, time, csv, re, os
from datetime import datetime
import requests
from weather_service import get_weather_for_district
import pandas as pd
import matplotlib.pyplot as plt
import io, base64
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for Flask
import matplotlib.pyplot as plt
from recommender import generate_recommendations



app = Flask(__name__)
CSV_FILE = "iot_data.csv"


# ------------------- Arduino Setup -------------------
try:
    ser = serial.Serial('COM7', 9600, timeout=1)
    time.sleep(2)
except:
    ser = None
    print("Arduino not connected. CSV will not update.")

# ------------------- Parse Arduino Line -------------------
def parse_line(line):
    try:
        # Take part after colon
        part = line.split(":")[1].strip()
        # Extract first number
        match = re.search(r"[-+]?\d*\.\d+|\d+", part)
        if match:
            return match.group()
    except IndexError:
        return None

# ------------------- Latest Data -------------------
latest_data = {}

def write_csv():
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Timestamp","Sensor","Value","Unit"])
        writer.writeheader()
        for sensor, item in latest_data.items():
            writer.writerow(item)

def read_sensors():
    if not ser:
        return
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue

            sensor_key = None
            value = parse_line(line)
            unit = ""

            # Determine sensor type and unit
            if line.startswith("DHT11 - Temperature"):
                sensor_key = "Temperature"
                unit = "°C"
            elif line.startswith("DHT11 - Humidity"):
                sensor_key = "Humidity"
                unit = "%"
            elif line.startswith("Soil Moisture"):
                sensor_key = "Soil Moisture"
                unit = ""
            elif line.startswith("LDR (Analog)"):
                sensor_key = "LDR"
                unit = ""
            elif line.startswith("MPL3115A2 - Pressure"):
                sensor_key = "Pressure"
                unit = "hPa"
            elif line.startswith("MPL3115A2 - Altitude"):
                sensor_key = "Altitude"
                unit = "m"

            if sensor_key and value:
                latest_data[sensor_key] = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Sensor": sensor_key,
                    "Value": value,
                    "Unit": unit
                }
                write_csv()  # overwrite CSV with latest values

        except Exception as e:
            print("Error reading/writing sensor:", e)
        time.sleep(0.1)

sensor_thread = threading.Thread(target=read_sensors, daemon=True)
sensor_thread.start()
# ------------------- CSV Utilities -------------------
def read_csv_data():
    data = []
    if os.path.isfile(CSV_FILE):
        try:
            with open(CSV_FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except Exception as e:
            print("Error reading CSV:", e)
    return data

def get_latest_sensor_value(sensor_name):
    data = read_csv_data()
    for row in reversed(data):
        if row["Sensor"] == sensor_name:
            try:
                return float(row["Value"])
            except:
                return None
    return None

# ------------------- Weather API -------------------
OPEN_METEO_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARS = ["temperature_2m", "precipitation", "windspeed_10m", "cloudcover"]
LAT, LON = 23.344315, 85.296013

def fetch_weather(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "Asia/Kolkata",
        "forecast_days": 1
    }
    r = requests.get(OPEN_METEO_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    rain = hourly.get("precipitation", [])
    wind = hourly.get("windspeed_10m", [])
    cloud = hourly.get("cloudcover", [])
    if not times: return {"rain": 0, "wind": 0, "cloud": 0}
    first_date = times[0].split("T")[0]
    rain_day, wind_day, cloud_day = [], [], []
    for i, t in enumerate(times):
        if t.startswith(first_date):
            rain_day.append(rain[i])
            wind_day.append(wind[i])
            cloud_day.append(cloud[i])
    return {
        "rain": sum(rain_day),
        "wind": max(wind_day) if wind_day else 0,
        "cloud": sum(cloud_day)/len(cloud_day) if cloud_day else 0
    }

# ------------------- Crop Recommendation -------------------
STATIC_VALUES = {
    "Nitrogen": 18.49,
    "Phosphorous": 18.37,
    "Potassium": 3.98,
    "Ph": 5.71,
    "Zn": 1.90,
    "S": 12.21
}

def recommend_crop(top_n=2):
    # Get IoT values
    temp = get_latest_sensor_value("Temperature") or 25
    humidity = get_latest_sensor_value("Humidity") or 60
    moisture = get_latest_sensor_value("Soil Moisture") or 50
    pressure = get_latest_sensor_value("Pressure") or 1013

    # Get weather values
    weather = fetch_weather(LAT, LON)
    rainfall = weather["rain"]
    wind = weather["wind"]
    cloud = weather["cloud"]

    # Static soil values
    soil = STATIC_VALUES

    # Collect all inputs for display
    input_values = {
        "Temperature": temp,
        "Humidity": humidity,
        "Moisture": moisture,
        "Pressure": pressure,
        "Rainfall": rainfall,
        "Wind": wind,
        "Cloud": cloud,
        **soil
    }

    # Simple rule-based scoring for crops
    scores = {"Rice": 0, "Wheat": 0, "Cotton": 0}

    if temp > 28 and moisture > 40 and soil["Nitrogen"] > 15:
        scores["Rice"] += 3
    if temp > 25 and humidity < 70 and rainfall < 5:
        scores["Wheat"] += 3
    if soil["Potassium"] < 5 or humidity > 70:
        scores["Cotton"] += 2
    if moisture < 40:
        scores["Wheat"] += 1
    if rainfall > 50:
        scores["Rice"] += 1

    # Sort crops by score descending
    sorted_crops = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_crops = [c[0] for c in sorted_crops[:top_n]]

    return top_crops, input_values


# ------------------- Flask Routes -------------------
@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/manual", methods=["GET", "POST"])
def manual():
    crops = []
    inputs = {}
    if request.method == "POST":
        # Read manual values from form
        temp = float(request.form.get("Temparature"))
        humidity = float(request.form.get("Humidity"))
        moisture = float(request.form.get("Moisture"))
        pressure = float(request.form.get("PS"))
        rainfall = float(request.form.get("Rainfall"))
        wind = float(request.form.get("Wind Speed"))
        cloud = float(request.form.get("CLOUD_AMT"))

        # Soil static values
        soil = STATIC_VALUES

        # Collect all inputs
        inputs = {
            "Temperature": temp,
            "Humidity": humidity,
            "Moisture": moisture,
            "Pressure": pressure,
            "Rainfall": rainfall,
            "Wind": wind,
            "Cloud": cloud,
            **soil
        }

        # Use same scoring logic as recommend_crop
        scores = {"Rice": 0, "Wheat": 0, "Cotton": 0}
        if temp > 28 and moisture > 40 and soil["Nitrogen"] > 15:
            scores["Rice"] += 3
        if temp > 25 and humidity < 70 and rainfall < 5:
            scores["Wheat"] += 3
        if soil["Potassium"] < 5 or humidity > 70:
            scores["Cotton"] += 2
        if moisture < 40:
            scores["Wheat"] += 1
        if rainfall > 50:
            scores["Rice"] += 1

        sorted_crops = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        crops = [c[0] for c in sorted_crops[:2]]

    return render_template("manual.html", crops=crops, inputs=inputs)


@app.route("/recommend_crop")
def recommend_crop_page():
    lang = request.args.get('lang', 'en')
    crops, inputs = recommend_crop(top_n=2)
    translations = {
        'en': {
            'title': 'Crop Recommendation',
            'recommended': '🌱 Recommended Crops',
            'top2': 'Top 2 Crops:',
            'input_values': 'Input Values Used',
            'parameter': 'Parameter',
            'value': 'Value',
            'back': '⬅ Back to Dashboard',
        },
        'hi': {
            'title': 'फसल सिफारिश',
            'recommended': '🌱 अनुशंसित फसलें',
            'top2': 'शीर्ष 2 फसलें:',
            'input_values': 'प्रयुक्त इनपुट मान',
            'parameter': 'पैरामीटर',
            'value': 'मान',
            'back': '⬅ डैशबोर्ड पर वापस जाएं',
        }
    }
    t = translations.get(lang, translations['en'])
    return render_template("recommend_crop.html", crops=crops, inputs=inputs, t=t, lang=lang)


@app.route("/iot")
def iot():
    return jsonify(list(latest_data.values()))

@app.route("/iot_data")
def iot_data():
    return jsonify(read_csv_data())
@app.route("/weather_dashboard")
def weather_dashboard():
    weather = get_weather_for_district("Ranchi")  # you can make district dynamic later
    return render_template("weather.html", data=weather)

@app.route("/fertilizer", methods=["GET", "POST"])
def fertilizer():
    recommendations = {}
    symptoms = []
    if request.method == "POST":
        raw = request.form.get("symptoms", "")
        symptoms = [s.strip() for s in raw.split(",") if s.strip()]
        recommendations = generate_recommendations(symptoms)
    return render_template("fertilizer.html", recs=recommendations, symptoms=symptoms)

@app.route("/market", methods=["GET", "POST"])
def market():
    selected_crops = []
    price_chart = None
    demand_chart = None
    profit_crop = None

    df = pd.read_csv("market_data.csv")
    crops_list = ["Wheat","Maize","Niger Seed","Paddy","Pea","Potato","Pulses","Sugarcane","Cotton"]

    if request.method == "POST":
        selected_crops = request.form.getlist("crops")
        if 0 < len(selected_crops) <= 3:
            df_filtered = df[df["Crop"].isin(selected_crops)]

            # --- Price Line Chart ---
            plt.figure(figsize=(8,4))
            for crop in selected_crops:
                crop_data = df_filtered[df_filtered["Crop"]==crop].sort_values("Date")
                plt.plot(crop_data["Date"], crop_data["Price"], marker='o', label=crop)
            plt.title("Crop Price Trend (₹/kg)")
            plt.xlabel("Date")
            plt.ylabel("Price (₹)")
            plt.xticks(rotation=45)
            plt.legend()
            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            price_chart = base64.b64encode(buf.getvalue()).decode()
            plt.close()

            # --- Demand Bar Chart ---
            plt.figure(figsize=(8,4))
            width = 0.3
            dates = sorted(df_filtered["Date"].unique())
            for i, crop in enumerate(selected_crops):
                crop_data = df_filtered[df_filtered["Crop"]==crop].sort_values("Date")
                plt.bar([x + i*width for x in range(len(dates))], crop_data["MarketDemand"], width=width, label=crop)
            plt.title("Crop Market Demand (tons)")
            plt.xlabel("Date")
            plt.ylabel("Demand")
            plt.xticks([x + width for x in range(len(dates))], dates, rotation=45)
            plt.legend()
            plt.tight_layout()
            buf2 = io.BytesIO()
            plt.savefig(buf2, format="png")
            buf2.seek(0)
            demand_chart = base64.b64encode(buf2.getvalue()).decode()
            plt.close()

            # --- Calculate Profit ---
            df_filtered["Revenue"] = df_filtered["Price"] * df_filtered["MarketDemand"]
            profit = df_filtered.groupby("Crop")["Revenue"].sum()
            profit_crop = profit.idxmax()
        else:
            selected_crops = []
            profit_crop = "Select 1 to 3 crops only!"

    return render_template("market.html",
                           crops_list=crops_list,
                           selected_crops=selected_crops,
                           price_chart=price_chart,
                           demand_chart=demand_chart,
                           profit_crop=profit_crop)


# ------------------- Run Flask -------------------
@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(app.root_path, filename)

@app.route("/static/<path:filename>")
def static_files(filename):
    # Serve from project root so /static/images/bg.jpg maps to images/bg.jpg
    return send_from_directory(app.root_path, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
