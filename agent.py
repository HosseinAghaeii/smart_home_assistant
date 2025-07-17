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


def _get_intent(user_message: str, preferred_service: str) -> str:
    """
    Step 1: The Router.
    This function classifies the user's intent as either 'tool_use' or 'conversation'.
    """
    print("[Agent Router] Step 1: Classifying intent...")

    # A simple prompt to classify the intent.
    system_prompt = """
    You are an intent classification system. Your job is to determine if a user's query requires calling a tool or if it's a general conversational query.
    The user has access to tools for controlling home devices and getting information like weather, time, or news.

    - If the query is a command, a request for specific data, or implies an action the tools can perform, respond with the single word: 'tool_use'.
    - If the query is a simple greeting, a question about your identity or capabilities ('who are you'), or general small talk, respond with the single word: 'conversation'.

    Analyze the user query and provide your classification.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # We call the LLM without any tools for this classification step.
    # We use a low temperature for a more predictable classification.
    response = get_llm_response(messages, preferred_service=preferred_service, temperature=0)

    if response and "choices" in response and response["choices"]:
        intent = response["choices"][0]["message"]["content"].strip().lower()
        print(f"[Agent Router] Intent classified as: '{intent}'")
        if "tool_use" in intent:
            return "tool_use"
    # Default to conversation if classification is unclear
    return "conversation"


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


def run_agent(user_message: str, preferred_service: str = "groq"):
    """
    Runs the agent using the robust Router pattern with a final summarization instruction.
    """
    print(f"\n[Agent] Received query: '{user_message}'")
    print(f"[Agent] Using service provider: {preferred_service.upper()}")

    intent = _get_intent(user_message, preferred_service)

    if intent == "tool_use":
        print("[Agent Executor] Intent is 'tool_use'. Proceeding with tool calling logic...")
        system_prompt = "You are a smart home assistant. First, call the necessary tools to fulfill the user's request based on their query."
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
        tools_schema = get_tools_schema()

        response = get_llm_response(messages, tools=tools_schema, preferred_service=preferred_service)
        if not response or "choices" not in response or not response[
            "choices"]: return "Error getting tool call decision."

        response_message = response["choices"][0]["message"]
        if not response_message.get(
            "tool_calls"): return "I understand you want me to perform an action, but I couldn't determine which tool to use. Please rephrase."

        tool_calls = response_message.get("tool_calls")
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name, function_args = tool_call["function"]["name"], json.loads(tool_call["function"]["arguments"])
            function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
            if function_to_call:
                result = function_to_call(**function_args)
                messages.append({"role": "tool", "tool_call_id": tool_call['id'], "name": function_name,
                                 "content": json.dumps(result)})

        # <<< بخش کلیدی جدید: افزودن دستورالعمل نهایی برای تولید خلاصه >>>
        print("[Agent Summarizer] Adding final instruction for a comprehensive response...")
        final_instruction = """
        You have successfully executed all required tools and their results have been provided.
        Now, formulate a single, cohesive, natural-language response to the user.
        Your response MUST address all parts of the user's original query, including both confirming the actions you took AND answering any conversational questions.
        Synthesize all information into a friendly and complete answer.
        """
        messages.append({"role": "user", "content": final_instruction})

        # --- فراخوانی نهایی برای تولید خلاصه ---
        print("[Agent Summarizer] Generating final response...")
        final_response = get_llm_response(messages, preferred_service=preferred_service)  # No tools are passed here
        if not final_response or "choices" not in final_response or not final_response[
            "choices"]: return "Tasks executed, but summary failed."
        return final_response["choices"][0]["message"]["content"]

    else:  # intent == "conversation"
        print("[Agent Executor] Intent is 'conversation'. Proceeding with conversational logic...")
        system_prompt = "You are a friendly and helpful smart home assistant. Keep your answers concise and polite."
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]

        response = get_llm_response(messages, preferred_service=preferred_service)
        if not response or "choices" not in response or not response[
            "choices"]: return "I'm having trouble thinking of a response right now."
        return response["choices"][0]["message"]["content"]


# def run_agent(user_message: str, preferred_service: str = "groq"):  # I've set groq as default as it's often more stable
#     """
#     Runs the agent using the new Router architecture.
#     """
#
#     # Step 1: Classify intent using the new router function.
#     intent = _get_intent(user_message, preferred_service)
#
#     # Step 2: Execute the appropriate logic based on the intent.
#     if intent == "tool_use":
#         print("[Agent Executor] Intent is 'tool_use'. Proceeding with your proven tool-calling logic...")
#         # This part is YOUR existing, well-tested code for tool calling.
#         # I have just wrapped it inside this if-statement.
#
#         system_prompt = f"""
#         You are a helpful and proactive smart home assistant. Your goal is to use the provided tools to fulfill the user's requests.
#         **Primary Method**: Use the `tool_calls` feature to call tools.
#         **Fallback Method**: If for any reason you cannot use the `tool_calls` feature, you MUST respond with a JSON object inside a ```json markdown block.
#         The JSON should be a list of tool call objects. Each object must have a `name` and an `arguments` key.
#         Example of a fallback response:
#         ```json
#         [
#             {{ "name": "call_turn_on_device", "arguments": {{"device_id": "room1_lamp"}} }}
#         ]
#         ```
#         """
#         messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
#         tools_schema = get_tools_schema()
#         response = get_llm_response(messages, tools=tools_schema, preferred_service=preferred_service)
#
#         if not response or "choices" not in response or not response["choices"]:
#             return "Sorry, I couldn't get a valid response from the assistant's brain."
#
#         response_message = response["choices"][0]["message"]
#         tool_calls = response_message.get("tool_calls")
#
#         if not tool_calls:
#             content = response_message.get("content", "")
#             parsed_calls = parse_tool_calls_from_content(content)
#             if parsed_calls:
#                 tool_calls = [{"type": "function", "function": call} for call in parsed_calls]
#
#         if tool_calls:
#             all_results = []
#             for tool_call in tool_calls:
#                 function_name = tool_call["function"]["name"]
#                 function_args = tool_call["function"]["arguments"]
#                 if isinstance(function_args, str):
#                     try:
#                         function_args = json.loads(function_args)
#                     except json.JSONDecodeError:
#                         all_results.append(
#                             {function_name: {"success": False, "error": f"Invalid JSON args: {function_args}"}})
#                         continue
#                 function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
#                 if function_to_call:
#                     try:
#                         result = function_to_call(**function_args)
#                         all_results.append({function_name: result})
#                     except Exception as e:
#                         all_results.append({function_name: {"success": False, "error": str(e)}})
#                 else:
#                     all_results.append(
#                         {function_name: {"success": False, "error": f"Unknown function '{function_name}'"}})
#             return all_results
#         else:
#             return response_message.get("content", "I couldn't process the tool request.")
#
#     else:  # intent == "conversation"
#         print("[Agent Executor] Intent is 'conversation'. Proceeding with conversational logic...")
#         # This part handles conversational queries by calling the LLM WITHOUT tools.
#         system_prompt = "You are a friendly and helpful smart home assistant. Keep your answers concise and polite."
#         messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
#
#         response = get_llm_response(messages, preferred_service=preferred_service)  # Note: No 'tools' parameter is sent
#
#         if not response or "choices" not in response or not response["choices"]:
#             return "I'm having trouble thinking of a response right now."
#         return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    print("--- Starting Agent Test ---")
    print("--- Starting Agent Test ---")
    # response1 = run_agent("Turn on the lamp in room 1")
    # response1 = run_agent("Turn on all ac units")
    # response1 = run_agent("Hello how are you?")
    # response1 = run_agent("What is today's date?")
    response1 = run_agent("turn on all lamps and who are you?")
    # response1 = run_agent("What is the weather like in Isfahan?")
    # response1 = run_agent("Turn on the light in room 1 and tell me the weather in Tehran and what time is it?")
    # response1 = run_agent("I want to sleep.")
    # response1 = run_agent("I want to sleep. I need a dark and quiet environment.")
    # response1 = run_agent("Tell me some news from china.")
    # response1 = run_agent("I want see football on tv")
    # response1 = run_agent("What is today's date?")
    print("\n--- Final Response 1 ---\n", response1)