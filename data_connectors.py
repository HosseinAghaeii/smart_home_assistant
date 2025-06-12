import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# For OpenWeatherMap API
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def get_current_weather(city: str = "Tehran", unit: str = "metric"):
    """
    Retrieves current weather information for a specified city.
    Unit can be 'metric' (Celsius) or 'imperial' (Fahrenheit).
    """
    if not OPENWEATHER_API_KEY:
        return "Error: Weather API Key not set."

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": unit,
        "lang": "en"  # For English descriptions
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        if data.get("cod") != 200:
            return f"Error getting weather data: {data.get('message', 'Unknown error')}"

        main_weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return (f"Current weather in {city}: {main_weather}. "
                f"Temperature: {temp}°C (feels like: {feels_like}°C). "
                f"Humidity: {humidity}%. Wind speed: {wind_speed} m/s.")

    except requests.exceptions.RequestException as e:
        return f"Error connecting to Weather API: {e}"
    except KeyError:
        return "Error: Weather information not found for the specified city or invalid response format."


def get_current_time():
    """Retrieves current time."""
    now = datetime.datetime.now()
    return f"Current time: {now.strftime('%H:%M:%S')}."


def get_current_date():
    """Retrieves current date."""
    today = datetime.date.today()
    # Format date for better English readability
    return f"Today's date: {today.strftime('%Y/%m/%d')}."


def get_news_headlines(category: str = "general", country: str = "us"):
    """
    Retrieves news headlines.
    """
    if not NEWS_API_KEY:
        return "Error: News API Key not set."

    base_url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWS_API_KEY,
        "category": category,
        "country": country,
        "pageSize": 3  # Number of news headlines to retrieve
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            return f"No news found in category {category} for country {country}."
        headlines = [f"- {article['title']}" for article in articles]
        return "\n" + "Latest news for " + country + " is as follows:" + "\n" + "\n".join(headlines)
    except requests.exceptions.RequestException as e:
        return f"Error connecting to News API: {e}"
    except KeyError:
        return "Error: Invalid News API response format."


if __name__ == "__main__":
    # Test data connectors
    print("Testing data connectors...")
    print(get_current_weather("Tehran"))
    print(get_current_time())
    print(get_current_date())
    print(get_news_headlines())