"""
Referral Network Agent using Gradient ADK.
Uses DigitalOcean's Gradient platform for LLM inference.
Calls Azure Functions backend API for tool execution.

Refactored to use shared modules from src/.
"""
import sys
import os

# Add parent directory to path for src/ imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import httpx
from typing import Dict, List, Any

from dotenv import load_dotenv
from gradient import AsyncGradient
from gradient_adk import entrypoint

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Import from core modules
from src.core.tool_registry import ToolRegistry
from src.prompts.system_prompts import SYSTEM_PROMPT

# Initialize registry
_registry = None


def get_registry():
    """Get or create the tool registry singleton."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load_domains()
    return _registry

# Configuration
GRADIENT_MODEL = os.getenv("GRADIENT_MODEL", "openai-gpt-oss-120b")
GRADIENT_MODEL_ACCESS_KEY = os.getenv("GRADIENT_MODEL_ACCESS_KEY")

# Backend API configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "")


def get_tools_schema() -> List[Dict]:
    """Get tool definitions in OpenAI-compatible function calling format."""
    return get_registry().get_openai_tools()


async def execute_tool(tool_name: str, tool_args: Dict) -> str:
    """Execute a tool by calling the backend API."""
    if not BACKEND_API_URL:
        return json.dumps({"error": "BACKEND_API_URL not configured"})

    url = f"{BACKEND_API_URL.rstrip('/')}/api/tools/{tool_name}"

    headers = {
        "Content-Type": "application/json"
    }

    # Add API key if configured (for Azure Functions with function-level auth)
    if BACKEND_API_KEY:
        headers["x-functions-key"] = BACKEND_API_KEY

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=tool_args, headers=headers)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"API error: {e.response.status_code} - {e.response.text}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def process_with_tools(
    inference_client: AsyncGradient,
    messages: List[Dict],
    tools: List[Dict],
    max_iterations: int = 5
) -> str:
    """Process a conversation with tool calling support."""

    for iteration in range(max_iterations):
        response = await inference_client.chat.completions.create(
            messages=messages,
            model=GRADIENT_MODEL,
            max_tokens=2048,
            temperature=0.7,
            tools=tools if tools else None
        )

        assistant_message = response.choices[0].message

        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # Call the backend API
                tool_result = await execute_tool(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
        else:
            return assistant_message.content or "No response generated."

    return "Max iterations reached without final response."


@entrypoint
async def main(body: Dict, context: Dict) -> str:
    """
    Main entry point for Referral Network Agent.
    Handles both deployment format (input.messages) and direct format (messages).
    """
    # Extract messages - handle both formats
    if "input" in body:
        input_data = body.get("input", {})
        messages = input_data.get("messages", [])
    else:
        messages = body.get("messages", [])

    # Handle empty messages
    if not messages:
        prompt = body.get("prompt", "")
        if prompt:
            messages = [{"role": "user", "content": prompt}]
        else:
            return "Hello! I'm the Referral Network Analytics Assistant. I can help you query information about children's hospital referral patterns, providers, and service lines. What would you like to know?"

    # Prepare messages with system prompt
    formatted_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    formatted_messages.extend(messages)

    # Initialize Gradient client
    inference_client = AsyncGradient(
        model_access_key=GRADIENT_MODEL_ACCESS_KEY
    )

    # Get tools schema
    tools = get_tools_schema()

    # Process with tool support
    try:
        result = await process_with_tools(
            inference_client,
            formatted_messages,
            tools
        )
        return result
    except Exception as e:
        return f"Error processing request: {str(e)}"


# For local testing
if __name__ == "__main__":
    async def test():
        test_body = {
            "messages": [
                {"role": "user", "content": "Give me an overview of the referral network"}
            ]
        }
        result = await main(test_body, {})
        print(result)

    asyncio.run(test())
