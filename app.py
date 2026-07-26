from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

SEASONAL_DATA = {
    "lilongwe": {1: {"t":24,"h":75,"r":180,"cr":5,"s":"Rainy season - heavy rains"}, 2: {"t":24,"h":78,"r":160,"cr":4,"s":"Rainy season"}, 3: {"t":23,"h":72,"r":100,"cr":3,"s":"End rainy season"}, 4: {"t":22,"h":65,"r":30,"cr":1,"s":"Cool dry - irrigation needed"}, 5: {"t":20,"h":60,"r":10,"cr":0,"s":"Cool dry - minimal rain"}, 6: {"t":18,"h":58,"r":5,"cr":0,"s":"Cold dry - protect crops"}, 7: {"t":19,"h":60,"r":3,"cr":0,"s":"Cold dry - irrigation essential"}, 8: {"t":21,"h":62,"r":2,"cr":0,"s":"Warming up - prepare planting"}, 9: {"t":24,"h":65,"r":5,"cr":0,"s":"Hot dry - early planting"}, 10: {"t":27,"h":68,"r":20,"cr":1,"s":"Hot dry - first rains soon"}, 11: {"t":27,"h":72,"r":80,"cr":3,"s":"Rainy starts - plant now"}, 12: {"t":25,"h":74,"r":150,"cr":4,"s":"Rainy season - active growing"}},
    "blantyre": {1: {"t":26,"h":78,"r":200,"cr":6,"s":"Rainy - heavy rains"}, 2: {"t":26,"h":80,"r":180,"cr":5,"s":"Rainy season"}, 3: {"t":25,"h":75,"r":120,"cr":4,"s":"End rainy season"}, 4: {"t":24,"h":68,"r":40,"cr":1,"s":"Cool dry"}, 5: {"t":22,"h":62,"r":15,"cr":0,"s":"Cool dry"}, 6: {"t":20,"h":60,"r":8,"cr":0,"s":"Cold dry"}, 7: {"t":21,"h":62,"r":5,"cr":0,"s":"Cold dry"}, 8: {"t":23,"h":64,"r":4,"cr":0,"s":"Warming up"}, 9: {"t":26,"h":68,"r":8,"cr":0,"s":"Hot dry"}, 10: {"t":29,"h":70,"r":25,"cr":1,"s":"Hot dry"}, 11: {"t":28,"h":74,"r":90,"cr":3,"s":"Rainy starts"}, 12: {"t":27,"h":76,"r":170,"cr":5,"s":"Rainy season"}},
    "mzuzu": {1: {"t":22,"h":82,"r":220,"cr":7,"s":"Rainy - very wet"}, 2: {"t":22,"h":84,"r":200,"cr":6,"s":"Rainy season"}, 3: {"t":21,"h":80,"r":150,"cr":5,"s":"End rainy"}, 4: {"t":20,"h":75,"r":50,"cr":2,"s":"Cool dry"}, 5: {"t":18,"h":70,"r":20,"cr":0,"s":"Cool dry"}, 6: {"t":16,"h":68,"r":10,"cr":0,"s":"Cold dry"}, 7: {"t":17,"h":70,"r":8,"cr":0,"s":"Cold dry"}, 8: {"t":19,"h":72,"r":6,"cr":0,"s":"Warming up"}, 9: {"t":22,"h":75,"r":10,"cr":0,"s":"Hot dry"}, 10: {"t":25,"h":78,"r":30,"cr":1,"s":"Hot dry"}, 11: {"t":24,"h":80,"r":100,"cr":4,"s":"Rainy starts"}, 12: {"t":23,"h":82,"r":190,"cr":6,"s":"Rainy season"}},
}

def get_coordinates(location):
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": location, "count": 1, "language": "en", "format": "json", "countryCode": "MW"}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        if "results" not in data or not data["results"]:
            return None
        result = data["results"][0]
        return {"name": result["name"], "latitude": result["latitude"], "longitude": result["longitude"]}
    except Exception:
        return None

def get_weather(latitude, longitude):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude, "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code",
            "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
            "timezone": "auto", "forecast_days": 7
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None

def get_fallback_weather(location):
    location_lower = location.lower().strip()
    current_month = datetime.now().month
    
    if location_lower in SEASONAL_DATA:
        data = SEASONAL_DATA[location_lower][current_month]
        return {"temperature": data["t"], "humidity": data["h"], "rainfall": data["r"], "current_rain": data["cr"], "season_note": data["s"], "fallback": True, "source": f"Seasonal data for {datetime.now().strftime('%B')}"}
    
    for district, monthly_data in SEASONAL_DATA.items():
        if district in location_lower or location_lower in district:
            data = monthly_data[current_month]
            return {"temperature": data["t"], "humidity": data["h"], "rainfall": data["r"], "current_rain": data["cr"], "season_note": data["s"], "fallback": True, "source": f"Seasonal data for {datetime.now().strftime('%B')}"}
    
    data = SEASONAL_DATA["lilongwe"][current_month]
    return {"temperature": data["t"], "humidity": data["h"], "rainfall": data["r"], "current_rain": data["cr"], "season_note": data["s"], "fallback": True, "source": f"Average seasonal data for {datetime.now().strftime('%B')}"}

def generate_advice(crop, weather_data, is_fallback=False):
    temperature = weather_data["temperature"]
    humidity = weather_data["humidity"]
    rainfall = weather_data["rainfall"]
    current_rain = weather_data["current_rain"]
    advice = []
    if is_fallback:
        advice.append("Weather service is currently unavailable. Using typical seasonal data for this area.")
    if temperature < 10:
        advice.append("The current temperature is low. Monitor crops for cold stress.")
    elif temperature <= 30:
        advice.append("The current temperature is generally suitable for many crops.")
    else:
        advice.append("The current temperature is high. Monitor crops for heat stress and water loss.")
    if rainfall == 0:
        advice.append("No significant rainfall is forecast for today. Check soil moisture and consider irrigation if necessary.")
    elif rainfall < 10:
        advice.append("Light rainfall is expected today. Monitor soil moisture carefully.")
    elif rainfall <= 50:
        advice.append("Moderate rainfall is expected today. Conditions may be favorable for crop growth.")
    else:
        advice.append("Heavy rainfall is expected. Watch for waterlogging, soil erosion, and fungal diseases.")
    if humidity > 80:
        advice.append("Humidity is high. Monitor crops for fungal diseases, especially if leaves remain wet.")
    if current_rain > 0:
        advice.append("Rain is currently being detected. Avoid unnecessary irrigation.")
    crop_lower = crop.lower()
    if "maize" in crop_lower:
        advice.append("For maize, monitor soil moisture carefully during critical growth stages such as flowering and grain filling.")
    elif "bean" in crop_lower or "beans" in crop_lower:
        advice.append("For beans, monitor excessive moisture because prolonged wet conditions can increase disease risk.")
    elif "groundnut" in crop_lower or "peanut" in crop_lower:
        advice.append("For groundnuts, maintain adequate moisture while avoiding prolonged waterlogging.")
    elif "rice" in crop_lower:
        advice.append("For rice, water management depends on the production system and variety. Monitor field water levels.")
    elif "cassava" in crop_lower:
        advice.append("For cassava, monitor moisture conditions and inspect plants regularly for pests and diseases.")
    elif "tobacco" in crop_lower:
        advice.append("For tobacco, ensure proper curing conditions and monitor leaf moisture levels.")
    elif "soya" in crop_lower or "soybean" in crop_lower:
        advice.append("For soya beans, maintain consistent moisture during pod filling stage.")
    elif "sorghum" in crop_lower:
        advice.append("For sorghum, it is drought-tolerant but benefits from moisture during heading and grain filling.")
    elif "sweet potato" in crop_lower:
        advice.append("For sweet potatoes, avoid waterlogging and ensure well-drained soil.")
    elif "mil" in crop_lower:
        advice.append("For millet, it is highly drought-tolerant but monitor during early establishment.")
    else:
        advice.append(f"Continue monitoring your {crop} crop and consider local soil, pest, disease, and weather conditions.")
    return {"temperature": temperature, "humidity": humidity, "rainfall": rainfall, "current_rain": current_rain, "advice": advice}

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None
    if request.method == "POST":
        location = request.form["location"]
        crop = request.form["crop"]
        try:
            coordinates = get_coordinates(location)
            if coordinates is None:
                weather_data = get_fallback_weather(location)
                agricultural_advice = generate_advice(crop, weather_data, is_fallback=True)
                result = {"location": location.title(), "crop": crop, "weather": agricultural_advice}
            else:
                weather = get_weather(coordinates["latitude"], coordinates["longitude"])
                if weather is None:
                    weather_data = get_fallback_weather(location)
                    agricultural_advice = generate_advice(crop, weather_data, is_fallback=True)
                    result = {"location": coordinates["name"], "crop": crop, "weather": agricultural_advice}
                else:
                    current = weather["current"]
                    daily = weather["daily"]
                    weather_data = {
                        "temperature": current["temperature_2m"],
                        "humidity": current["relative_humidity_2m"],
                        "rainfall": daily["precipitation_sum"][0],
                        "current_rain": current["rain"],
                        "fallback": False
                    }
                    agricultural_advice = generate_advice(crop, weather_data, is_fallback=False)
                    result = {"location": coordinates["name"], "crop": crop, "weather": agricultural_advice}
        except Exception as e:
            error = f"An unexpected error occurred: {e}"
    return render_template("index.html", result=result, error=error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
