# weather_service.py
import requests
from collections import defaultdict

# ---- CONFIG ----
WIND_ALERT_THRESHOLD_MS = 15.0   # m/s (~54 km/h)
HEAVY_RAIN_THRESHOLD_MM_PER_H = 10.0
DAILY_RAIN_ALERT_THRESHOLD_MM = 50.0
SUNLIGHT_HOURS_MIN = 4
TEMP_TOO_HOT = 38.0
TEMP_TOO_COLD = 10.0

OPEN_METEO_ENDPOINT = "https://api.open-meteo.com/v1/forecast"

JHARKHAND_LOCATIONS = {
    "Ranchi": (23.344315, 85.296013),
    "Jamshedpur": (22.805618, 86.203110),
    "Dhanbad": (23.795399, 86.427040),
    "Bokaro": (23.669296, 86.151115),
    "Hazaribagh": (23.996620, 85.369110),
}

HOURLY_VARS = ["temperature_2m", "precipitation", "windspeed_10m",
               "shortwave_radiation", "cloudcover"]

# -----------------------------
# Fetch forecast JSON from API
# -----------------------------
def fetch_forecast(lat, lon, days=7):
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "Asia/Kolkata",
        "forecast_days": days
    }
    r = requests.get(OPEN_METEO_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# -----------------------------
# Aggregate daily weather and provide advice
# -----------------------------
def aggregate_daily(forecast_json):
    hourly = forecast_json.get("hourly", {})
    times = hourly.get("time", [])
    temp = hourly.get("temperature_2m", [])
    precip = hourly.get("precipitation", [])
    wind = hourly.get("windspeed_10m", [])
    sr = hourly.get("shortwave_radiation", [])
    cloud = hourly.get("cloudcover", [])

    daily_data = defaultdict(lambda: {"temps": [], "winds": [], "precips": [], "sunlight": 0, "clouds": []})
    alerts = []

    for i, tstr in enumerate(times):
        date = tstr.split("T")[0]
        vtemp = temp[i] if i < len(temp) else None
        vprec = precip[i] if i < len(precip) else 0.0
        vwind = wind[i] if i < len(wind) else None
        vsr = sr[i] if i < len(sr) else 0.0
        vcloud = cloud[i] if i < len(cloud) else None

        dd = daily_data[date]
        if vtemp is not None: dd["temps"].append(vtemp)
        if vwind is not None: dd["winds"].append(vwind)
        dd["precips"].append(vprec)
        if vcloud is not None: dd["clouds"].append(vcloud)
        if vsr > 20: dd["sunlight"] += 1

        # Hourly alerts
        if vprec >= HEAVY_RAIN_THRESHOLD_MM_PER_H:
            alerts.append((date, "Heavy Rain Hourly"))
        if vwind and vwind >= WIND_ALERT_THRESHOLD_MS:
            alerts.append((date, "High Wind Hourly"))

    # Prepare daily summary
    daily_summary = []
    for date, vals in sorted(daily_data.items()):
        max_temp = max(vals["temps"]) if vals["temps"] else None
        total_rain = sum(vals["precips"]) if vals["precips"] else 0.0
        max_wind = max(vals["winds"]) if vals["winds"] else None
        sunlight_hours = vals["sunlight"]
        avg_cloud = sum(vals["clouds"]) / len(vals["clouds"]) if vals["clouds"] else None

        risks, advice = [], []

        if max_temp:
            if max_temp > TEMP_TOO_HOT:
                risks.append("Too Hot")
                advice.append("High heat — avoid irrigation at noon.")
            elif max_temp < TEMP_TOO_COLD:
                risks.append("Too Cold")
                advice.append("Low temp — seed germination may slow down.")

        if total_rain > DAILY_RAIN_ALERT_THRESHOLD_MM:
            risks.append("Heavy Rainfall")
            advice.append("Avoid sowing/fertilizer; flooding possible.")
        elif total_rain < 5:
            advice.append("Irrigation may be needed.")

        if max_wind and max_wind > WIND_ALERT_THRESHOLD_MS:
            risks.append("Strong Winds")
            advice.append("Avoid pesticide spraying; protect tall crops.")

        if sunlight_hours < SUNLIGHT_HOURS_MIN:
            risks.append("Low Sunlight")
            advice.append("Low sunlight may slow growth.")
        else:
            advice.append("Good sunlight for crops.")

        if avg_cloud is not None and avg_cloud > 80:
            risks.append("High Cloud")
            advice.append("Very cloudy — less sunlight for crops.")

        if "Heavy Rainfall" in risks or "Strong Winds" in risks:
            safety = "Not Safe"
        elif risks:
            safety = "Caution"
        else:
            safety = "Safe"

        daily_summary.append({
            "date": date,
            "temp": max_temp,
            "rain": total_rain,
            "wind": max_wind,
            "sunlight": sunlight_hours,
            "cloud": avg_cloud,
            "risks": ", ".join(risks) if risks else "None",
            "safety": safety,
            "advice": " ".join(advice) if advice else "Good day for farming."
        })

    return daily_summary, alerts

# -----------------------------
# Public API to get weather for a district
# -----------------------------
def get_weather_for_district(district_name):
    district = district_name.strip().title()
    if district not in JHARKHAND_LOCATIONS:
        return {"error": f"District '{district}' not found."}

    lat, lon = JHARKHAND_LOCATIONS[district]
    forecast_json = fetch_forecast(lat, lon, days=7)
    daily_summary, alerts = aggregate_daily(forecast_json)
    return {"district": district, "daily_summary": daily_summary, "alerts": alerts}
