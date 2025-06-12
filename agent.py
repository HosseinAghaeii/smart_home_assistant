import json
import re
import codecs
from llm_client import get_llm_response
from device_controller import turn_on_device, turn_off_device
from data_connectors import get_current_weather, get_current_time, get_current_date, get_news_headlines

# This list should be defined before TOOLS
real_device_ids = [
    "kitchen_lamp", "bathroom_lamp", "room1_lamp", "room2_lamp",
    "room1_ac", "kitchen_ac", "living_room_tv"
]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "turn_on_device",
            "description": "Turns on a specific device like a lamp, AC unit, or TV.",
            "parameters": {
                "type": "object",
                "properties": {"device_id": {"type": "string", "enum": real_device_ids,
                                             "description": "Unique identifier for the hardware device."}},
                "required": ["device_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "turn_off_device",
            "description": "Turns off a specific device like a lamp, AC unit, or TV.",
            "parameters": {
                "type": "object",
                "properties": {"device_id": {"type": "string", "enum": real_device_ids,
                                             "description": "Unique identifier for the hardware device."}},
                "required": ["device_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Retrieves current weather information for a specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The name of the city, e.g., Tehran"},
                    "unit": {"type": "string", "enum": ["metric", "imperial"], "description": "Temperature unit. Default is metric (Celsius)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Gets the precise, real-time current time. Use this for any questions about the current time.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "Gets the precise, real-time current date. Use this for any questions about the current date.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_headlines",
            "description": "Retrieves recent news headlines for a given category and country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["business", "entertainment", "general", "health", "science", "sports", "technology"], "description": "The category of news to retrieve."},
                    "country": {"type": "string", "enum": ["us", "gb", "de", "ir"], "description": "The two-letter ISO 3166-1 code of the country."}
                }
            }
        }
    }
]

AVAILABLE_FUNCTIONS = {
    "turn_on_device": turn_on_device,
    "turn_off_device": turn_off_device,
    "get_current_weather": get_current_weather,
    "get_current_time": get_current_time,
    "get_current_date": get_current_date,
    "get_news_headlines": get_news_headlines,
}


def execute_tool(function_name: str, arguments: dict):
    print(f"\n--- Calling tool: {function_name} with args: {arguments} ---")
    function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
    if not function_to_call:
        return f"Unknown function: {function_name}"
    try:
        return function_to_call(**arguments)
    except Exception as e:
        return f"Error executing function {function_name}: {e}"


def run_agent(user_message: str):
    """
    Runs the agent with Chain of Thought (CoT) prompting.
    This version includes more robust parsing to handle malformed LLM responses.
    """

    system_prompt = f"""You are a helpful and proactive smart home assistant.
Your goal is to understand the user's intent and use the available tools to help them.

You MUST follow this process strictly:
1.  **Think**: First, analyze the user's request and explain your reasoning inside a <thinking> tag.
2.  **Act**: Second, based on your thinking, generate the action inside an <action> tag. The action can be:
    a) One or more tool calls, formatted as JSON objects inside a ```json ... ``` block. Each JSON object must be on a new line.
    b) A direct text response to the user if no tool is needed.

IMPORTANT: Your final output must be a single block of text. The <thinking> tag must be completely closed before the <action> tag begins. Do not nest tags.

Here are the available tools for you:
{json.dumps(TOOLS, indent=2)}

--- EXAMPLES ---

**Example 1: Intent-based request requiring multiple tools**
User: I want to sleep
Assistant:
<thinking>
The user wants to sleep. This implies they want a dark and quiet environment. I should turn off all the lights (kitchen, bathroom, room1, room2) and the TV. This requires multiple calls to the `turn_off_device` tool.
</thinking>
<action>
```json
{{"name": "turn_off_device", "parameters": {{"device_id": "kitchen_lamp"}}}}
{{"name": "turn_off_device", "parameters": {{"device_id": "bathroom_lamp"}}}}
{{"name": "turn_off_device", "parameters": {{"device_id": "room1_lamp"}}}}
{{"name": "turn_off_device", "parameters": {{"device_id": "room2_lamp"}}}}
{{"name": "turn_off_device", "parameters": {{"device_id": "living_room_tv"}}}}
&lt;/action>

Example 2: No tool needed
User: Hello
Assistant:
&lt;thinking>
The user is just saying hello. This is a simple greeting and does not require any tools. I should respond with a friendly greeting.
&lt;/thinking>
&lt;action>
Hello! How can I help you today?
&lt;/action>
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response_content = get_llm_response(json.dumps(messages), preferred_service="togetherai")
    print(f"--- Raw response from LLM ---\n{response_content}\n--------------------")

    # --- NEW ROBUST PARSING LOGIC ---
    thought_match = re.search(r"<thinking>(.*?)</thinking>", response_content, re.DOTALL)
    if thought_match:
        print(f"--- Assistant's Thought Process ---\n{thought_match.group(1).strip()}\n---------------------------------")

    # Find content that looks like a tool call, regardless of wrapping tags.
    # This regex looks for '{"name": ...}' which is the start of our tool calls.
    json_blobs = re.findall(r'\{\s*"name":\s*".*?"(?:,\s*"parameters":\s*\{.*?\})?\s*\}', response_content, re.DOTALL)

    if json_blobs:
        tool_results = []
        for blob in json_blobs:
            try:
                tool_call = json.loads(blob)
                function_name = tool_call.get("name") or tool_call.get("fname")
                arguments = tool_call.get("parameters", {})
                if function_name:
                    result = execute_tool(function_name=function_name, arguments=arguments)
                    tool_results.append(str(result))
            except json.JSONDecodeError as e:
                print(f"--- Warning: Could not parse a JSON blob: {e} ---")
                print(f"--- Malformed blob: {blob} ---")
                continue # Skip to the next blob

        if tool_results:
            return "\n".join(tool_results)

# --- Fallback for text responses if no tools are called ---
    action_match = re.search(r"<action>(.*?)</action>", response_content, re.DOTALL)
    if action_match:
        action_content = action_match.group(1).strip()
        # If the action content is not JSON, return it as a text response.
        if not json_blobs:
            json_wrapper_match = re.search(r"```json\s*(.*?)\s*```", action_content, re.DOTALL)
            if not json_wrapper_match:
                return action_content

# Final fallback if parsing fails completely
    print("--- Warning: Could not parse a clear tool call or text action. Returning raw content. ---")
    return response_content
if __name__ == "__main__":
    print("Testing the agent with Chain of Thought...")

    # print("\n--- Test 1: Intent 'I want to sleep.' ---")
    # print(f"Agent Response: {run_agent('I want to sleep.')}")
    print(f"Agent Response: {run_agent('I want go out.')}")

    # print("\n--- Test 2: Intent 'My favorite movie is about to start.' ---")
    # print(f"Agent Response: {run_agent('My favorite movie is about to start.')}")

    # print("\n--- Test 3: Direct command 'What time is it?' ---")
    # print(f"Agent Response: {run_agent('What time is it?')}")

    # print("\n--- Test 4: Simple conversation 'Hello' ---")
    # print(f"Agent Response: {run_agent('Hello, who are you')}")

    # print(f"Agent Response: {run_agent('''What is today's date?''')}")

    # print("\n--- Test 3: Asking about weather ---")
    # print(f"Agent Response: {run_agent('What is the weather like in Isfahan?')}")


    # print(f"Agent Response: {run_agent('Turn off the TV please?')}")

    # print(f"Agent Response: {run_agent('Turn off room 1 lamp please?')}")

    # print("\n--- Test 5: Complex request with two commands ---")
    # print(f"Agent Response: {run_agent('Turn on the light in room 1 and tell me the weather in Tehran and what time is it?.')}")