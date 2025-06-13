from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent import run_agent
import uvicorn
from typing import List, Dict, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _format_response(tool_call_name: str, tool_result: dict) -> dict:
    """Formats the raw tool result into the final JSON structure."""

    if not tool_result.get("success"):
        return {
            "type": "error",
            "content": f"An error occurred while executing {tool_call_name}.",
            "data": tool_result
        }

    if "weather" in tool_call_name:
        return {
            "type": "weather",
            "content": f"Current weather in {tool_result.get('city', 'your area')} is {tool_result.get('condition', 'unknown')}.",
            "data": tool_result
        }
    elif "time" in tool_call_name:
        return {
            "type": "time",
            "content": f"The current time is {tool_result.get('time', 'unknown')}.",
            "data": tool_result
        }
    elif "date" in tool_call_name:
        return {
            "type": "date",
            "content": f"Today is {tool_result.get('fullDate', 'unknown')}.",
            "data": tool_result
        }
    elif "news" in tool_call_name:
        return {
            "type": "news",
            "content": "Here are today's top headlines for you.",
            "data": tool_result
        }
    elif "device" in tool_call_name:
        return {
            "type": "device",
            "content": f"Alright, the {tool_result.get('deviceName')} was successfully {tool_result.get('action')}. ✨",
            "data": None
        }
    else:
        return {
            "type": "general",
            "content": "Your request has been processed successfully.",
            "data": tool_result
        }


@app.get("/data", response_model=List[Dict[str, Any]])
async def handle_agent_query(userInput: str):
    """
    This API endpoint receives a user query, processes it with the agent,
    and returns a list of structured JSON objects for each action taken.
    """
    if not userInput:
        raise HTTPException(status_code=400, detail="userInput parameter cannot be empty.")

    agent_results = run_agent(userInput)

    # --- KEY CHANGE STARTS HERE ---

    if isinstance(agent_results, list):
        final_responses = []
        for result_item in agent_results:
            tool_name = list(result_item.keys())[0]
            tool_data = list(result_item.values())[0]
            formatted_response = _format_response(tool_name, tool_data)
            final_responses.append(formatted_response)

        return final_responses

    return [{
        "type": "general",
        "content": agent_results,
        "data": None
    }]


if __name__ == "__main__":
    print("Starting FastAPI server at http://localhost:8090")
    uvicorn.run(app, host="0.0.0.0", port=8090)