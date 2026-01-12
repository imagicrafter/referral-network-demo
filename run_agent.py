#!/usr/bin/env python3
"""
Unified launcher for Referral Network Agent.
Supports both Azure OpenAI and Gradient (DigitalOcean) backends.

Set AGENT_PROVIDER in .env to switch:
  - "azure" for Azure OpenAI
  - "gradient" for DigitalOcean Gradient

Usage:
  python run_agent.py           # Uses AGENT_PROVIDER from .env
  python run_agent.py --azure   # Force Azure OpenAI
  python run_agent.py --gradient # Force Gradient
"""
import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

load_dotenv()


def run_azure_agent():
    """Run the Azure OpenAI agent."""
    import json
    import time
    from openai import AzureOpenAI, RateLimitError
    import agent_tools

    # Configuration
    AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        print("\nERROR: Missing Azure OpenAI configuration!")
        print("Please check your .env file has:")
        print("  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("  AZURE_OPENAI_API_KEY=your-key")
        return

    client = AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION
    )

    TOOL_FUNCTIONS = {
        "find_hospital": agent_tools.find_hospital,
        "get_referral_sources": agent_tools.get_referral_sources,
        "get_referral_destinations": agent_tools.get_referral_destinations,
        "get_network_statistics": agent_tools.get_network_statistics,
        "find_referral_path": agent_tools.find_referral_path,
        "get_providers_by_specialty": agent_tools.get_providers_by_specialty,
        "get_hospitals_by_service": agent_tools.get_hospitals_by_service,
        "analyze_rural_access": agent_tools.analyze_rural_access,
    }

    SYSTEM_PROMPT = """You are a healthcare analytics assistant with access to a referral network
database for children's hospitals. You can query information about hospitals, providers,
referral patterns, and service lines.

When asked questions about the network, use the available tools to find accurate information.
Summarize your findings in a clear, professional manner suitable for healthcare administrators.

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

    def get_tools():
        tools = []
        for tool_def in agent_tools.TOOL_DEFINITIONS:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"]
                }
            })
        return tools

    def call_with_retry(func, max_retries=3, initial_wait=60):
        for attempt in range(max_retries):
            try:
                return func()
            except RateLimitError:
                if attempt == max_retries - 1:
                    raise
                wait_time = initial_wait * (2 ** attempt)
                print(f"\n  [Rate limited. Waiting {wait_time}s before retry {attempt + 2}/{max_retries}...]")
                time.sleep(wait_time)
        return None

    def run_agent(user_message: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        tools = get_tools()

        response = call_with_retry(lambda: client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        ))

        assistant_message = response.choices[0].message

        while assistant_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
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
                tool_input = json.loads(tool_call.function.arguments)

                tool_function = TOOL_FUNCTIONS.get(tool_name)
                if tool_function:
                    try:
                        tool_result = tool_function(**tool_input)
                        result_content = json.dumps(tool_result, indent=2)
                    except Exception as e:
                        result_content = f"Error: {str(e)}"
                else:
                    result_content = f"Unknown tool: {tool_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_content
                })

            response = call_with_retry(lambda: client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            ))

            assistant_message = response.choices[0].message

        return assistant_message.content or "No response generated."

    # Interactive loop
    print(f" Model: {DEPLOYMENT_NAME}")
    print(f" Endpoint: {AZURE_ENDPOINT}")

    while True:
        print()
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = run_agent(user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            import traceback
            print(f"\nError: {e}")
            traceback.print_exc()


def run_gradient_agent():
    """Run the Gradient (DigitalOcean) agent."""
    import json
    from gradient import AsyncGradient
    import agent_tools

    GRADIENT_MODEL = os.getenv("GRADIENT_MODEL", "openai-gpt-oss-120b")
    GRADIENT_MODEL_ACCESS_KEY = os.getenv("GRADIENT_MODEL_ACCESS_KEY")

    if not GRADIENT_MODEL_ACCESS_KEY or GRADIENT_MODEL_ACCESS_KEY == "your-gradient-model-access-key":
        print("\nERROR: Missing Gradient configuration!")
        print("Please check your .env file has:")
        print("  GRADIENT_MODEL_ACCESS_KEY=your-actual-key")
        return

    TOOL_FUNCTIONS = {
        "find_hospital": agent_tools.find_hospital,
        "get_referral_sources": agent_tools.get_referral_sources,
        "get_referral_destinations": agent_tools.get_referral_destinations,
        "get_network_statistics": agent_tools.get_network_statistics,
        "find_referral_path": agent_tools.find_referral_path,
        "get_providers_by_specialty": agent_tools.get_providers_by_specialty,
        "get_hospitals_by_service": agent_tools.get_hospitals_by_service,
        "analyze_rural_access": agent_tools.analyze_rural_access,
    }

    SYSTEM_PROMPT = """You are a healthcare analytics assistant with access to a referral network
database for children's hospitals. You can query information about hospitals, providers,
referral patterns, and service lines.

When asked questions about the network, use the available tools to find accurate information.
Summarize your findings in a clear, professional manner suitable for healthcare administrators.

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

    def get_tools():
        tools = []
        for tool_def in agent_tools.TOOL_DEFINITIONS:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"]
                }
            })
        return tools

    async def run_agent_async(user_message: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        tools = get_tools()

        inference_client = AsyncGradient(
            model_access_key=GRADIENT_MODEL_ACCESS_KEY
        )

        max_iterations = 5
        for _ in range(max_iterations):
            response = await inference_client.chat.completions.create(
                messages=messages,
                model=GRADIENT_MODEL,
                max_tokens=2048,
                temperature=0.7,
                tools=tools
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

                    tool_function = TOOL_FUNCTIONS.get(tool_name)
                    if tool_function:
                        try:
                            # Run sync tool in thread to avoid event loop conflicts
                            tool_result = await asyncio.to_thread(tool_function, **tool_args)
                            result_content = json.dumps(tool_result, indent=2)
                        except Exception as e:
                            result_content = json.dumps({"error": str(e)})
                    else:
                        result_content = json.dumps({"error": f"Unknown tool: {tool_name}"})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_content
                    })
            else:
                return assistant_message.content or "No response generated."

        return "Max iterations reached."

    def run_agent(user_message: str) -> str:
        return asyncio.run(run_agent_async(user_message))

    # Interactive loop
    print(f" Model: {GRADIENT_MODEL}")

    while True:
        print()
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        try:
            response = run_agent(user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            import traceback
            print(f"\nError: {e}")
            traceback.print_exc()


def test_database():
    """Test the database connection."""
    import agent_tools
    print("\n--- Testing Database Connection ---")
    try:
        stats = agent_tools.get_network_statistics()
        print(f"Total hospitals: {stats.get('total_hospitals', 'N/A')}")
        print(f"Total providers: {stats.get('total_providers', 'N/A')}")
        print(f"Total referral relationships: {stats.get('total_referral_relationships', 'N/A')}")
        print("Database connection: OK")
        return True
    except Exception as e:
        print(f"Database connection FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Referral Network Agent - supports Azure OpenAI and Gradient backends"
    )
    parser.add_argument(
        "--azure", action="store_true",
        help="Force use of Azure OpenAI backend"
    )
    parser.add_argument(
        "--gradient", action="store_true",
        help="Force use of Gradient (DigitalOcean) backend"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Test database connection only"
    )
    args = parser.parse_args()

    print("=" * 60)
    print(" Referral Network Analytics Agent")
    print(" Type 'quit' to exit")
    print("=" * 60)

    # Test database connection
    if args.test:
        test_database()
        return

    test_database()

    # Determine provider
    if args.azure:
        provider = "azure"
    elif args.gradient:
        provider = "gradient"
    else:
        provider = os.getenv("AGENT_PROVIDER", "azure").lower()

    print(f" Provider: {provider.upper()}")
    print("=" * 60)

    if provider == "gradient":
        run_gradient_agent()
    else:
        run_azure_agent()


if __name__ == "__main__":
    main()
