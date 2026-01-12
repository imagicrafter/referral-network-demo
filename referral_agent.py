"""
AI agent for querying the referral network using Azure OpenAI.
"""
import os
import json
import time
from dotenv import load_dotenv
from openai import AzureOpenAI, RateLimitError
import agent_tools

load_dotenv()

# Get Azure OpenAI configuration
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

# Ensure endpoint has proper format (no trailing slash issues)
if AZURE_ENDPOINT and not AZURE_ENDPOINT.endswith("/"):
    AZURE_ENDPOINT = AZURE_ENDPOINT.rstrip("/")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    api_version=AZURE_API_VERSION
)

# Map tool names to functions
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


def get_tools_for_openai():
    """Convert tool definitions to OpenAI function calling format."""
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
    """Call a function with exponential backoff retry on rate limit errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = initial_wait * (2 ** attempt)
            print(f"\n  [Rate limited. Waiting {wait_time}s before retry {attempt + 2}/{max_retries}...]")
            time.sleep(wait_time)
    return None


def run_agent(user_message: str) -> str:
    """Run the agent with a user message and return the response."""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    tools = get_tools_for_openai()

    # Initial API call with retry
    response = call_with_retry(lambda: client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    ))

    assistant_message = response.choices[0].message
    
    # Handle tool calls loop
    while assistant_message.tool_calls:
        # Add assistant's response to messages (properly serialized)
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

        # Process each tool call
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)

            # Execute the tool
            tool_function = TOOL_FUNCTIONS.get(tool_name)
            if tool_function:
                try:
                    tool_result = tool_function(**tool_input)
                    result_content = json.dumps(tool_result, indent=2)
                except Exception as e:
                    result_content = f"Error: {str(e)}"
            else:
                result_content = f"Unknown tool: {tool_name}"
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_content
            })
        
        # Get next response with retry
        response = call_with_retry(lambda: client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        ))

        assistant_message = response.choices[0].message
    
    return assistant_message.content or "No response generated."


def test_connection():
    """Test the database connection and show available data."""
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
    """Interactive agent loop."""
    print("=" * 60)
    print(" Referral Network Analytics Agent (Azure OpenAI)")
    print(" Type 'quit' to exit, 'test' to check database")
    print("=" * 60)
    print(f" Model: {DEPLOYMENT_NAME}")
    print(f" Endpoint: {AZURE_ENDPOINT}")
    print(f" API Version: {AZURE_API_VERSION}")
    print("=" * 60)
    
    # Verify configuration
    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        print("\n ERROR: Missing Azure OpenAI configuration!")
        print(" Please check your .env file has:")
        print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("   AZURE_OPENAI_API_KEY=your-key")
        print("   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini")
        return
    
    # Test database on startup
    test_connection()
    
    while True:
        print()
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if user_input.lower() == 'test':
            test_connection()
            continue
        
        if not user_input:
            continue
        
        try:
            response = run_agent(user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            import traceback
            print(f"\nError: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()