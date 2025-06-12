# data_connectors.py (Updated to return structured data)
import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_current_weather(city: str = "Tehran", unit: str = "metric"):
    if not OPENWEATHER_API_KEY: return {"success": False, "error": "Weather API Key not set."}
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": unit, "lang": "en"}
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("cod") != 200: return {"success": False, "error": data.get('message')}

        return {
            "success": True,
            "city": city,
            "temperature": f"{data['main']['temp']}°C",
            "condition": data["weather"][0]["description"],
            "humidity": f"{data['main']['humidity']}%",
            "windSpeed": f"{data['wind']['speed']} m/s",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_current_time():
    now = datetime.datetime.now()
    return {"success": True, "time": now.strftime('%H:%M:%S')}

def get_current_date():
    today = datetime.datetime.now()
    return {
        "success": True,
        "fullDate": today.strftime('%A, %B %d, %Y'),
        "dayOfWeek": today.strftime('%A'),
        "month": today.strftime('%B'),
        "day": today.day,
        "year": today.year,
    }

def get_news_headlines(category: str = "general", country: str = "us"):
    if not NEWS_API_KEY: return {"success": False, "error": "News API Key not set."}
    base_url = "https://newsapi.org/v2/top-headlines"
    params = {"apiKey": NEWS_API_KEY, "category": category, "country": country, "pageSize": 3}
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        if not articles: return {"success": False, "error": f"No news found."}

        return {
            "success": True,
            "headlines": [article['title'] for article in articles]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test data connectors
    print("Testing data connectors...")
    print(get_current_weather("Tehran"))
    print(get_current_time())
    print(get_current_date())
    print(get_news_headlines())