# agent.py (Final Hybrid Architecture to handle API inconsistencies)

import json
import re
from llm_client import get_llm_response
from device_controller import turn_on_device, turn_off_device
from data_connectors import get_current_weather, get_current_time, get_current_date, get_news_headlines
from tools_definition import get_tools_schema

# Maps the function names from the tool schema to the actual Python functions.
AVAILABLE_FUNCTIONS = {
    "call_turn_on_device": turn_on_device,
    "call_turn_off_device": turn_off_device,
    "call_get_current_weather": get_current_weather,
    "call_get_current_time": get_current_time,
    "call_get_current_date": get_current_date,
    "call_get_news_headlines": get_news_headlines,
}


def parse_tool_calls_from_content(content: str) -> list:
    """
    Parses tool call JSON from a markdown code block in the LLM's text response.
    This is a fallback for when the API doesn't use the native tool_calls feature correctly.
    """
    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if not json_match:
        return None

    json_string = json_match.group(1)
    try:
        # The LLM might return a single JSON object or a list of them
        data = json.loads(json_string)
        if isinstance(data, list):
            # If it's a list, assume it's a list of tool calls and return it
            return data
        elif isinstance(data, dict):
            # If it's a single object, wrap it in a list
            return [data]
        else:
            return None
    except json.JSONDecodeError:
        print(f"[Agent] Warning: Found a JSON block, but it was malformed: {json_string}")
        return None


def run_agent(user_message: str):
    """
    Runs the agent using a hybrid architecture that first tries native Tool Calling,
    and falls back to parsing JSON from the text content if native calling fails.
    """
    print(f"\n[Agent] Received query: '{user_message}'")

    # This prompt asks for JSON in a code block as a fallback.
    system_prompt = f"""
    You are a helpful and proactive smart home assistant. Your goal is to use the provided tools to fulfill the user's requests.

    **Primary Method**: Use the `tool_calls` feature to call tools.

    **Fallback Method**: If for any reason you cannot use the `tool_calls` feature, you MUST respond with a JSON object inside a ```json markdown block.
    The JSON should be a list of tool call objects. Each object must have a `name` and an `arguments` key.

    Example of a fallback response:
    ```json
    [
        {{
            "name": "call_turn_on_device",
            "arguments": {{"device_id": "room1_lamp"}}
        }},
        {{
            "name": "call_get_current_weather",
            "arguments": {{"city": "London"}}
        }}
    ]
    ```
    Only respond with conversational text if no tool is suitable.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    tools_schema = get_tools_schema()

    print("[Agent] Sending query, system prompt, and tool definitions to LLM...")
    response = get_llm_response(messages, tools=tools_schema)

    if not response or "choices" not in response or not response["choices"]:
        return "Sorry, I couldn't get a valid response from the assistant's brain."

    response_message = response["choices"][0]["message"]
    tool_calls = response_message.get("tool_calls")

    # If native tool calling fails, try to parse from the text content as a fallback
    if not tool_calls:
        print("[Agent] Native `tool_calls` not found. Attempting to parse JSON from text content...")
        content = response_message.get("content", "")
        parsed_calls = parse_tool_calls_from_content(content)
        if parsed_calls:
            # Reformat the parsed JSON to match the expected native structure
            tool_calls = [{"type": "function", "function": call} for call in parsed_calls]

    if tool_calls:
        print(f"[Agent] Successfully identified {len(tool_calls)} tool(s) to call.")
        all_results = []
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]

            # Arguments can be a string (from native call) or a dict (from fallback parse)
            function_args = tool_call["function"]["arguments"]
            if isinstance(function_args, str):
                try:
                    function_args = json.loads(function_args)
                except json.JSONDecodeError:
                    error_message = f"Error: The model returned invalid JSON for arguments: {function_args}"
                    print(f"[Agent] {error_message}")
                    all_results.append(error_message)
                    continue

            print(f"[Agent] Executing: {function_name} with arguments: {function_args}")

            function_to_call = AVAILABLE_FUNCTIONS.get(function_name)

            if function_to_call:
                try:
                    result = function_to_call(**function_args)
                    all_results.append(str(result))
                except Exception as e:
                    all_results.append(f"Error executing function '{function_name}': {e}")
            else:
                all_results.append(f"Error: Unknown function '{function_name}'")

        return "\n".join(all_results)
    else:
        print("[Agent] LLM decided to respond with text and no valid tools were found.")
        return response_message.get("content", "I couldn't process that request.")


if __name__ == "__main__":
    print("--- Starting Agent Test ---")
    # response1 = run_agent("Turn on the lamp in room 1")
    # response1 = run_agent("Turn on all ac units")
    # response1 = run_agent("Hello how are you?")
    response1 = run_agent("What is today's date?")
    # response1 = run_agent("What is the weather like in Isfahan?")
    # response1 = run_agent("Turn on the light in room 1 and tell me the weather in Tehran and what time is it?")
    # response1 = run_agent("I want to sleep.")
    # response1 = run_agent("I want to sleep. I need a dark and quiet environment.")
    # response1 = run_agent("Tell me some news from china.")
    # response1 = run_agent("I want see football on tv")
    print("\n--- Final Response 1 ---\n", response1)