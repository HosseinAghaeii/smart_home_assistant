import os
import requests
import json
from dotenv import load_dotenv


load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_together_ai_llama3(prompt: str, model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", temperature: float = 0.7, max_tokens: int = 150):
    """
    Calls the LLaMA 3 model via TogetherAI.
    Default model: Llama-3-8b-chat-hf (lighter for testing)
    Can be changed to Llama-3-70b-chat-hf.
    """
    if not TOGETHER_API_KEY:
        raise ValueError("TogetherAI API Key not set.")

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error calling TogetherAI API: {e}")
        return None

def call_groq_llama3(prompt: str, model: str = "llama3-8b-8192", temperature: float = 0.7, max_tokens: int = 150):
    """
    Calls the LLaMA 3 model via Groq.
    Default model: llama3-8b-8192 (lighter for testing)
    Can be changed to llama3-70b-8192.
    """
    if not GROQ_API_KEY:
        raise ValueError("Groq API Key not set.")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status() # Check for HTTP errors
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error calling Groq API: {e}")
        return None

# A function to choose between Groq and TogetherAI
def get_llm_response(prompt: str, preferred_service: str = "togetherai"):
    """
    Receives a response from the LLM.
    You can specify the preferred service ("groq" or "togetherai").
    """
    if preferred_service == "groq":
        response = call_groq_llama3(prompt)
        if response:
            return response
        else:
            print("Groq failed, trying TogetherAI...")
            return call_together_ai_llama3(prompt)
    elif preferred_service == "togetherai":
        response = call_together_ai_llama3(prompt)
        if response:
            return response
        else:
            print("TogetherAI failed, trying Groq...")
            return call_groq_llama3(prompt)
    else:
        raise ValueError("Invalid preferred_service. Must be 'groq' or 'togetherai'.")

if __name__ == "__main__":
    # Test LLM communication
    print("Testing LLM communication...")
    test_prompt = "Hello, who are you?"

    # Test with Groq
    print("\n--- Testing with Groq ---")
    response_groq = get_llm_response(test_prompt, preferred_service="groq")
    if response_groq:
        print(f"Groq Response: {response_groq}")
    else:
        print("Groq test failed.")

    # Test with TogetherAI
    print("\n--- Testing with TogetherAI ---")
    response_together = get_llm_response(test_prompt, preferred_service="togetherai")
    if response_together:
        print(f"TogetherAI Response: {response_together}")
    else:
        print("TogetherAI test failed.")