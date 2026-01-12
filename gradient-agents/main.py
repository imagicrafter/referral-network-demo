"""
Referral Network Agent using Gradient ADK.
Uses DigitalOcean's Gradient platform for LLM inference.
Calls Azure Functions backend API for tool execution.
"""
import os
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

# Configuration
GRADIENT_MODEL = os.getenv("GRADIENT_MODEL", "openai-gpt-oss-120b")
GRADIENT_MODEL_ACCESS_KEY = os.getenv("GRADIENT_MODEL_ACCESS_KEY")

# Backend API configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "")

# Tool definitions for the LLM
TOOL_DEFINITIONS = [
    {
        "name": "find_hospital",
        "description": "Search for hospitals by name, state, type, or rural status. Use partial names like 'Children's Mercy' to find matches.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Hospital name (partial match supported)"},
                "state": {"type": "string", "description": "State abbreviation (e.g., 'MO', 'KS')"},
                "hospital_type": {"type": "string", "enum": ["tertiary", "community", "regional", "specialty"]},
                "rural": {"type": "boolean", "description": "Whether the hospital is in a rural area"}
            }
        }
    },
    {
        "name": "get_referral_sources",
        "description": "Find all hospitals that refer patients to a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the receiving hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_referral_destinations",
        "description": "Find all hospitals that receive referrals from a specific hospital",
        "parameters": {
            "type": "object",
            "properties": {
                "hospital_name": {"type": "string", "description": "Exact name of the referring hospital"}
            },
            "required": ["hospital_name"]
        }
    },
    {
        "name": "get_network_statistics",
        "description": "Get overall statistics about the referral network",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "find_referral_path",
        "description": "Find referral paths between two hospitals",
        "parameters": {
            "type": "object",
            "properties": {
                "from_hospital": {"type": "string", "description": "Starting hospital name"},
                "to_hospital": {"type": "string", "description": "Destination hospital name"},
                "max_hops": {"type": "integer", "description": "Maximum intermediate hospitals", "default": 3}
            },
            "required": ["from_hospital", "to_hospital"]
        }
    },
    {
        "name": "get_providers_by_specialty",
        "description": "Find providers by medical specialty",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {"type": "string", "description": "Medical specialty name"}
            },
            "required": ["specialty"]
        }
    },
    {
        "name": "get_hospitals_by_service",
        "description": "Find hospitals offering a specific service line",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the service line"}
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "analyze_rural_access",
        "description": "Analyze how rural hospitals connect to specialized services",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the specialized service"}
            },
            "required": ["service_name"]
        }
    }
]

SYSTEM_PROMPT = """You are a healthcare analytics assistant with access to a referral network
database for children's hospitals. You can query information about hospitals, providers,
referral patterns, and service lines.

When asked questions about the network, use the available tools to find accurate information.
Summarize your findings in a clear, professional manner suitable for healthcare administrators.

Available data includes:
- Hospital information (name, location, type, bed count, rural status)
- Provider information (name, specialty, hospital affiliations)
- Referral relationships between hospitals (volume, acuity)
- Service lines and which hospitals offer them

The hospitals in the database include:
- Children's Mercy Kansas City (tertiary, MO)
- Children's Hospital Colorado (tertiary, CO)
- St. Louis Children's Hospital (tertiary, MO)
- Regional Medical Center (community, rural, MO)
- Prairie Community Hospital (community, rural, KS)
- Heartland Pediatrics (specialty, KS)
- Ozark Regional Medical (regional, MO)
- Nebraska Children's (tertiary, NE)

Always base your answers on actual data from the tools, not assumptions.
When searching for a hospital, use the exact name as listed above."""


def get_tools_schema() -> List[Dict]:
    """Convert tool definitions to OpenAI-compatible function calling format."""
    tools = []
    for tool_def in TOOL_DEFINITIONS:
        tools.append({
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["parameters"]
            }
        })
    return tools


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
