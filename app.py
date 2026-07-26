from flask import Flask, render_template, request
import requests

app = Flask(__name__)


def get_coordinates(location):
    """Find latitude and longitude for a location in Malawi."""

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": location,
        "count": 1,
        "language": "en",
        "format": "json",
        "countryCode": "MW"
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return None

    data = response.json()

    if "results" not in data or not data["results"]:
        return None

    result = data["results"][0]

    return {
        "name": result["name"],
        "latitude": result["latitude"],
        "longitude": result["longitude"]
    }


def get_weather(latitude, longitude):
    """Get current weather and today's rainfall."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code",
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": 7
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return None

    return response.json()


def generate_advice(crop, weather):
    """Generate basic agricultural advice."""

    current = weather["current"]
    daily = weather["daily"]

    temperature = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    current_rain = current["rain"]

    today_rainfall = daily["precipitation_sum"][0]

    advice = []

    # Temperature
    if temperature < 10:
        advice.append(
            "The current temperature is low. Monitor crops for cold stress."
        )
    elif temperature <= 30:
        advice.append(
            "The current temperature is generally suitable for many crops."
        )
    else:
        advice.append(
            "The current temperature is high. Monitor crops for heat stress and water loss."
        )

    # Rainfall
    if today_rainfall == 0:
        advice.append(
            "No significant rainfall is forecast for today. Check soil moisture and consider irrigation if necessary."
        )
    elif today_rainfall < 10:
        advice.append(
            "Light rainfall is expected today. Monitor soil moisture carefully."
        )
    elif today_rainfall <= 50:
        advice.append(
            "Moderate rainfall is expected today. Conditions may be favorable for crop growth."
        )
    else:
        advice.append(
            "Heavy rainfall is expected. Watch for waterlogging, soil erosion, and fungal diseases."
        )

    # Humidity
    if humidity > 80:
        advice.append(
            "Humidity is high. Monitor crops for fungal diseases, especially if leaves remain wet."
        )

    # Current rain
    if current_rain > 0:
        advice.append(
            "Rain is currently being detected. Avoid unnecessary irrigation."
        )

    # Crop-specific basic advice
    crop_lower = crop.lower()

    if "maize" in crop_lower:
        advice.append(
            "For maize, monitor soil moisture carefully during critical growth stages such as flowering and grain filling."
        )

    elif "bean" in crop_lower or "beans" in crop_lower:
        advice.append(
            "For beans, monitor excessive moisture because prolonged wet conditions can increase disease risk."
        )

    elif "groundnut" in crop_lower or "peanut" in crop_lower:
        advice.append(
            "For groundnuts, maintain adequate moisture while avoiding prolonged waterlogging."
        )

    elif "rice" in crop_lower:
        advice.append(
            "For rice, water management depends on the production system and variety. Monitor field water levels."
        )

    elif "cassava" in crop_lower:
        advice.append(
            "For cassava, monitor moisture conditions and inspect plants regularly for pests and diseases."
        )

    else:
        advice.append(
            f"Continue monitoring your {crop} crop and consider local soil, pest, disease, and weather conditions."
        )

    return {
        "temperature": temperature,
        "humidity": humidity,
        "rainfall": today_rainfall,
        "current_rain": current_rain,
        "advice": advice
    }


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
                error = f"Could not find the location '{location}'. Try another district or town."

            else:

                weather = get_weather(
                    coordinates["latitude"],
                    coordinates["longitude"]
                )

                if weather is None:
                    error = "Could not retrieve weather information. Please try again."

                else:

                    agricultural_advice = generate_advice(
                        crop,
                        weather
                    )

                    result = {
                        "location": coordinates["name"],
                        "crop": crop,
                        "weather": agricultural_advice
                    }

        except requests.RequestException:
            error = "Unable to connect to the weather service. Check your internet connection."

        except Exception as e:
            error = f"An unexpected error occurred: {e}"

    return render_template(
        "index.html",
        result=result,
        error=error
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
