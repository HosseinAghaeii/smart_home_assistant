# tools_definition.py (Final and Complete Version)

from pydantic import BaseModel, Field
from typing import Literal


# -----------------------------------------------------------------------------
# بخش ۱: تعریف مدل آرگومان‌ها برای هر تابع با استفاده از Pydantic
# -----------------------------------------------------------------------------

class DeviceControlArgs(BaseModel):
    """Arguments for turning a device on or off."""
    device_id: Literal[
        "kitchen_lamp", "bathroom_lamp", "room1_lamp", "room2_lamp",
        "room1_ac", "kitchen_ac", "living_room_tv"
    ] = Field(..., description="The unique identifier for the hardware device.")


class WeatherArgs(BaseModel):
    """Arguments for getting the current weather."""
    city: str = Field(..., description="The name of the city, for example, Tehran.")
    unit: Literal["metric", "imperial"] = Field("metric",
                                                description="The unit for temperature. Can be 'metric' (Celsius) or 'imperial' (Fahrenheit).")


class NewsArgs(BaseModel):
    """Arguments for getting news headlines."""
    category: Literal[
        "business", "entertainment", "general", "health", "science", "sports", "technology"
    ] = Field("general", description="The category of news to retrieve.")
    country: Literal[
        'ae', 'ar', 'at', 'au', 'be', 'bg', 'br', 'ca', 'ch', 'cn', 'co', 'cu', 'cz',
        'de', 'eg', 'fr', 'gb', 'gr', 'hk', 'hu', 'id', 'ie', 'il', 'in', 'it', 'jp',
        'kr', 'lt', 'lv', 'ma', 'mx', 'my', 'ng', 'nl', 'no', 'nz', 'ph', 'pl', 'pt',
        'ro', 'rs', 'ru', 'sa', 'se', 'sg', 'si', 'sk', 'th', 'tr', 'tw', 'ua', 'us',
        've', 'za'
    ] = Field("us", description="The two-letter ISO 3166-1 code for the country.")


class EmptyArgs(BaseModel):
    """An empty model for functions that take no arguments."""
    pass


# -----------------------------------------------------------------------------
# بخش ۲: تابع کمکی برای تبدیل مدل Pydantic به JSON Schema
# -----------------------------------------------------------------------------

def pydantic_to_json_schema(model: BaseModel, function_name: str, function_description: str) -> dict:
    """
    A helper function to convert a Pydantic model into the JSON Schema format
    required for LLM Tool Calling.
    """
    schema = model.model_json_schema()
    # The function name is prefixed to avoid potential conflicts with other function names.
    prefixed_name = "call_" + function_name

    # For models with no properties (like EmptyArgs), we don't need the properties part.
    parameters = {"type": "object", "properties": {}}
    if schema.get("properties"):
        parameters["properties"] = schema["properties"]
        if schema.get("required"):
            parameters["required"] = schema.get("required", [])

    return {
        "type": "function",
        "function": {
            "name": prefixed_name,
            "description": function_description,
            "parameters": parameters,
        },
    }


# -----------------------------------------------------------------------------
# بخش ۳: تابع اصلی برای دریافت لیست کامل ابزارها
# -----------------------------------------------------------------------------

def get_tools_schema() -> list:
    """
    Returns a complete list of all defined tools in the required JSON Schema format.
    This is the list that will be sent to the LLM API.
    """
    tools = [
        pydantic_to_json_schema(
            model=DeviceControlArgs,
            function_name="turn_on_device",
            function_description="Turns on a specific device like a lamp, AC unit, or TV."
        ),
        pydantic_to_json_schema(
            model=DeviceControlArgs,
            function_name="turn_off_device",
            function_description="Turns off a specific device like a lamp, AC unit, or TV."
        ),
        pydantic_to_json_schema(
            model=WeatherArgs,
            function_name="get_current_weather",
            function_description="Retrieves current weather information for a specified city."
        ),
        pydantic_to_json_schema(
            model=EmptyArgs,
            function_name="get_current_time",
            function_description="Gets the precise, real-time current time."
        ),
        pydantic_to_json_schema(
            model=EmptyArgs,
            function_name="get_current_date",
            function_description="Gets the precise, real-time current date."
        ),
        pydantic_to_json_schema(
            model=NewsArgs,
            function_name="get_news_headlines",
            function_description="Retrieves recent news headlines for a given category and country."
        ),
    ]
    return tools
