# llm_client.py (Final Corrected Version)

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# <<< KEY CHANGE IS IN THIS FUNCTION DEFINITION >>>
def get_llm_response(messages: list, tools: list = None, preferred_service: str = "togetherai", temperature: float = 0.7):
    """
    Calls an LLM API using an OpenAI-compatible interface, supporting tool calls and temperature setting.
    Args:
        messages: A list of message objects.
        tools: An optional list of tool schemas.
        preferred_service: The API service to use ('togetherai' or 'groq').
        temperature: The sampling temperature for the model.
    Returns:
        The full JSON response from the API as a dictionary, or None on failure.
    """
    if preferred_service == "togetherai":
        api_key = TOGETHER_API_KEY
        url = "https://api.together.xyz/v1/chat/completions"
        model = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo" # The model you confirmed works well
    elif preferred_service == "groq":
        api_key = GROQ_API_KEY
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama3-70b-8192" # Groq works well with the 70B model
    else:
        raise ValueError("Invalid preferred_service. Must be 'groq' or 'togetherai'.")

    if not api_key:
        raise ValueError(f"API Key for '{preferred_service}' not set in .env file.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature, # Now uses the temperature passed to the function
        "max_tokens": 1024,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling {preferred_service} API: {e}")
        if e.response:
             print(f"Response body: {e.response.text}")
        return None