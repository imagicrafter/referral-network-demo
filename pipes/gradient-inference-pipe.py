"""
title: Gradient Serverless Inference Pipe
description: Pipe for connecting Open WebUI to Gradient Serverless Inference with tool calling
author: Referral Network Demo
version: 1.0.0
license: MIT
"""

import json
import re
import httpx
from typing import List, Union, Dict, Any
from pydantic import BaseModel, Field


class Pipe:
    """
    Open WebUI Pipe for Gradient Serverless Inference.

    This pipe:
    1. Sends chat requests to Gradient Serverless Inference
    2. Handles tool calls by forwarding them to Azure Functions backend
    3. Returns the final response to Open WebUI

    Endpoint: https://inference.do-ai.run/v1/chat/completions
    Auth: Bearer token (Model Access Key)
    """

    class Valves(BaseModel):
        """Configuration options shown in Open WebUI admin panel."""

        GRADIENT_MODEL_ACCESS_KEY: str = Field(
            default="",
            description="Your Gradient Model Access Key (starts with sk-do-)"
        )
        GRADIENT_MODEL: str = Field(
            default="llama3.3-70b-instruct",
            description="Model to use (e.g., llama3.3-70b-instruct, openai-gpt-oss-120b)"
        )
        BACKEND_API_URL: str = Field(
            default="https://referral-network-api.azurewebsites.net",
            description="Azure Functions backend URL"
        )
        BACKEND_API_KEY: str = Field(
            default="",
            description="Azure Functions key (x-functions-key)"
        )
        REQUEST_TIMEOUT: int = Field(
            default=120,
            description="Request timeout in seconds"
        )
        MAX_TOOL_ITERATIONS: int = Field(
            default=5,
            description="Maximum tool call iterations"
        )
        DEBUG_MODE: bool = Field(
            default=False,
            description="Enable debug logging"
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "gradient_inference"
        self.name = "Gradient Inference"
        self.valves = self.Valves()

        # Tool definitions for the referral network
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "find_hospital",
                    "description": "Search for hospitals by name, state, type, or rural status. Use partial names like 'Children' to find matches.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Hospital name (partial match supported)"},
                            "state": {"type": "string", "description": "State abbreviation (e.g., 'MO', 'KS')"},
                            "hospital_type": {"type": "string", "enum": ["tertiary", "community", "regional", "specialty"]},
                            "rural": {"type": "boolean", "description": "Whether the hospital is in a rural area"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_referral_sources",
                    "description": "Find all hospitals that refer patients to a specific hospital",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "hospital_name": {"type": "string", "description": "Exact name of the receiving hospital"}
                        },
                        "required": ["hospital_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_referral_destinations",
                    "description": "Find all hospitals that receive referrals from a specific hospital",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "hospital_name": {"type": "string", "description": "Exact name of the referring hospital"}
                        },
                        "required": ["hospital_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_network_statistics",
                    "description": "Get overall statistics about the referral network",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_referral_path",
                    "description": "Get RAW DATA about referral paths (returns JSON list). Use ONLY for data analysis, NOT for visualization. For diagrams, use generate_path_diagram instead.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_hospital": {"type": "string", "description": "Starting hospital name"},
                            "to_hospital": {"type": "string", "description": "Destination hospital name"},
                            "max_hops": {"type": "integer", "description": "Maximum intermediate hospitals", "default": 3}
                        },
                        "required": ["from_hospital", "to_hospital"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_providers_by_specialty",
                    "description": "Find providers by medical specialty",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "specialty": {"type": "string", "description": "Medical specialty name"}
                        },
                        "required": ["specialty"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_hospitals_by_service",
                    "description": "Find hospitals offering a specific service line",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Name of the service line"}
                        },
                        "required": ["service_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
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
            },
            # Diagram generation tools
            {
                "type": "function",
                "function": {
                    "name": "generate_referral_network_diagram",
                    "description": "Generate a Mermaid diagram showing hospital referral relationships. Use this when asked to visualize or show a diagram of the referral network.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "hospital_name": {"type": "string", "description": "Optional: Focus on a specific hospital's connections"},
                            "include_volumes": {"type": "boolean", "description": "Show referral counts on edges", "default": True},
                            "direction": {"type": "string", "enum": ["LR", "TB", "RL", "BT"], "description": "Diagram direction", "default": "LR"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_path_diagram",
                    "description": "REQUIRED for path visualization. Returns a complete Mermaid diagram showing referral paths between hospitals. Always use this (not find_referral_path) when asked to show, visualize, diagram, or draw paths.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_hospital": {"type": "string", "description": "Starting hospital name"},
                            "to_hospital": {"type": "string", "description": "Destination hospital name"},
                            "max_hops": {"type": "integer", "description": "Maximum intermediate hospitals", "default": 3}
                        },
                        "required": ["from_hospital", "to_hospital"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_service_network_diagram",
                    "description": "Generate a Mermaid diagram showing hospitals that provide a specific service. Use this when asked to visualize which hospitals offer a service.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "service_name": {"type": "string", "description": "Name of service line (e.g., 'Cardiac Surgery', 'NICU')"},
                            "include_rankings": {"type": "boolean", "description": "Show hospital rankings", "default": True}
                        },
                        "required": ["service_name"]
                    }
                }
            }
        ]

        self.system_prompt = """You are a healthcare analytics assistant with access to a referral network database for children's hospitals.

IMPORTANT: You MUST use the available tools to answer questions about the network. NEVER make up or assume data - always call the appropriate tool first.

Available tools:

DATA QUERY TOOLS (return raw JSON data for analysis):
- get_network_statistics: Get overall network stats
- find_hospital: Search for hospitals by name, state, type, or rural status
- get_referral_sources: Find hospitals that refer TO a specific hospital
- get_referral_destinations: Find hospitals that receive referrals FROM a hospital
- find_referral_path: Raw path data ONLY - do NOT use for visualization
- get_providers_by_specialty: Find providers by medical specialty
- get_hospitals_by_service: Find hospitals offering a specific service
- analyze_rural_access: Analyze rural hospital access patterns

DIAGRAM TOOLS (return ready-to-display Mermaid diagrams):
- generate_referral_network_diagram: Diagram of hospital referral relationships
- generate_path_diagram: Diagram of paths between two hospitals
- generate_service_network_diagram: Diagram of hospitals offering a service

TOOL SELECTION RULES:
- If user says "show", "visualize", "diagram", "draw", or "display" → Use a DIAGRAM tool
- For paths between hospitals with visualization → Use generate_path_diagram (NOT find_referral_path)
- For referral network visualization → Use generate_referral_network_diagram
- For service network visualization → Use generate_service_network_diagram

The hospitals in the database include:
- Children's Mercy Kansas City (tertiary, MO)
- Children's Hospital Colorado (tertiary, CO)
- St. Louis Children's Hospital (tertiary, MO)
- Regional Medical Center (community, rural, MO)
- Prairie Community Hospital (community, rural, KS)
- Heartland Pediatrics (specialty, KS)
- Ozark Regional Medical (regional, MO)
- Nebraska Children's (tertiary, NE)

Service lines include: Cardiac Surgery, NICU, Oncology, Neurology, Orthopedics

After receiving tool results, summarize the findings clearly for healthcare administrators.

CRITICAL RULES FOR DIAGRAMS:
1. Diagram tools return a complete Mermaid code block (starting with ```mermaid). Output it EXACTLY as returned - do not modify, rewrite, or regenerate it.
2. NEVER write your own Mermaid code. The tools return working diagrams with proper styling.
3. AFTER outputting the diagram verbatim, add a **Color Key** in plain text:
   - Referral network: Green = Tertiary, Blue = Community, Purple = Regional, Pink = Specialty, Orange = Rural
   - Path diagrams: Green border = Start, Red border = End
   - Service diagrams: Gold = #1 ranked, Silver = Top 3, Bronze = Other"""

    def pipes(self) -> List[dict]:
        """Return available models/pipes."""
        return [
            {
                "id": "referral-network-agent",
                "name": "Referral Network Agent (Gradient)",
                "description": "Healthcare referral network analytics using Gradient Serverless Inference"
            }
        ]

    def pipe(
        self,
        body: dict,
        __user__: dict = None,
        __event_emitter__=None,
        __task__=None,
    ) -> Union[str, None]:
        """Process chat request with tool calling support."""

        if self.valves.DEBUG_MODE:
            print(f"[Gradient Pipe] Task: {__task__}")

        # Skip for title generation
        if __task__ == "title_generation":
            return ""

        # Validate configuration
        if not self.valves.GRADIENT_MODEL_ACCESS_KEY:
            return "Error: Please configure GRADIENT_MODEL_ACCESS_KEY in the pipe settings."

        if not self.valves.BACKEND_API_URL:
            return "Error: Please configure BACKEND_API_URL in the pipe settings."

        messages = body.get("messages", [])
        if not messages:
            return "Hello! I'm the Referral Network Analytics Assistant. Ask me about hospital referral patterns, providers, or services."

        # Add system prompt
        formatted_messages = [{"role": "system", "content": self.system_prompt}]
        formatted_messages.extend(messages)

        try:
            return self._process_with_tools(formatted_messages)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if self.valves.DEBUG_MODE:
                print(f"[Gradient Pipe] {error_msg}")
                import traceback
                traceback.print_exc()
            return error_msg

    # Diagram tool names for special handling
    DIAGRAM_TOOLS = {
        "generate_referral_network_diagram",
        "generate_path_diagram",
        "generate_service_network_diagram"
    }

    def _process_with_tools(self, messages: List[Dict]) -> str:
        """Process conversation with tool calling loop."""

        url = "https://inference.do-ai.run/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.valves.GRADIENT_MODEL_ACCESS_KEY.strip()}",
            "Content-Type": "application/json",
        }

        # Track diagram outputs for direct injection
        diagram_outputs = []

        for iteration in range(self.valves.MAX_TOOL_ITERATIONS):
            if self.valves.DEBUG_MODE:
                print(f"[Gradient Pipe] Iteration {iteration + 1}")

            payload = {
                "model": self.valves.GRADIENT_MODEL,
                "messages": messages,
                "tools": self.tools,
                "tool_choice": "auto",
                "temperature": 0.7,
                "max_tokens": 2048,
            }

            with httpx.Client(timeout=self.valves.REQUEST_TIMEOUT) as client:
                response = client.post(url, json=payload, headers=headers)

                if self.valves.DEBUG_MODE:
                    print(f"[Gradient Pipe] Response status: {response.status_code}")

                response.raise_for_status()
                data = response.json()

            if self.valves.DEBUG_MODE:
                print(f"[Gradient Pipe] Response: {json.dumps(data, indent=2)[:1000]}")

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            finish_reason = choice.get("finish_reason", "")

            if self.valves.DEBUG_MODE:
                print(f"[Gradient Pipe] Finish reason: {finish_reason}")
                print(f"[Gradient Pipe] Message content: {message.get('content', 'None')[:200] if message.get('content') else 'None'}")

            # Check for tool calls
            tool_calls = message.get("tool_calls", [])

            if self.valves.DEBUG_MODE:
                print(f"[Gradient Pipe] Tool calls count: {len(tool_calls) if tool_calls else 0}")

            # If finish_reason is "stop" or no tool calls, return the response
            if finish_reason == "stop" or not tool_calls:
                content = message.get("content", "")
                if content:
                    # Inject diagram outputs if the LLM didn't include them correctly
                    return self._ensure_diagrams_included(content, diagram_outputs)
                else:
                    return "No response generated. The model did not return any content."

            # Process tool calls
            if tool_calls:
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls
                })

                # Execute each tool call
                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name", "")
                    tool_args_str = tool_call.get("function", {}).get("arguments", "{}")
                    tool_call_id = tool_call.get("id", "")

                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {}

                    if self.valves.DEBUG_MODE:
                        print(f"[Gradient Pipe] Calling tool: {tool_name}({tool_args})")

                    # Call the backend API
                    tool_result = self._execute_tool(tool_name, tool_args)

                    if self.valves.DEBUG_MODE:
                        print(f"[Gradient Pipe] Tool result: {tool_result[:500]}...")

                    # Capture diagram outputs for direct injection
                    if tool_name in self.DIAGRAM_TOOLS:
                        if tool_result.startswith("```mermaid"):
                            diagram_outputs.append({
                                "tool": tool_name,
                                "diagram": tool_result,
                                "args": tool_args,
                                "error": None
                            })
                            if self.valves.DEBUG_MODE:
                                print(f"[Gradient Pipe] Captured diagram from {tool_name}")
                        else:
                            # Diagram tool returned an error or unexpected result
                            diagram_outputs.append({
                                "tool": tool_name,
                                "diagram": None,
                                "args": tool_args,
                                "error": tool_result
                            })
                            if self.valves.DEBUG_MODE:
                                print(f"[Gradient Pipe] Diagram tool {tool_name} returned error: {tool_result[:200]}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": tool_result
                    })

        return "Maximum iterations reached. Please try a simpler query."

    def _ensure_diagrams_included(self, content: str, diagram_outputs: List[Dict]) -> str:
        """
        Ensure diagram tool outputs are correctly included in the response.

        LLMs often generate their own diagrams instead of using tool outputs.
        This method validates and injects the correct diagrams.
        """
        if not diagram_outputs:
            return content

        # Check for diagram errors first - if all diagrams failed, add error message
        errors = [d for d in diagram_outputs if d.get("error")]
        valid_diagrams = [d for d in diagram_outputs if d.get("diagram")]

        if errors and not valid_diagrams:
            # All diagram tools failed - add clear error message
            error_msg = "\n\n⚠️ **Diagram Generation Failed**\n\n"
            error_msg += "The system was unable to generate the requested diagram. "
            error_msg += "This may be due to:\n"
            error_msg += "- No matching data found in the database\n"
            error_msg += "- Invalid hospital names or parameters\n"
            error_msg += "- A temporary service issue\n\n"
            error_msg += "Please verify the hospital names and try again, or contact support if the issue persists."

            # Remove any LLM-generated mermaid blocks
            content = self._remove_invalid_mermaid(content)
            return content + error_msg

        # Check if the response contains valid mermaid from our tools
        # A valid diagram from our tools will have our specific node ID format (e.g., CMKC_xxxx)
        has_valid_diagram = False
        if "```mermaid" in content:
            # Our diagrams have patterns like: CMKC_1234["Hospital Name"]
            if re.search(r'\b[A-Z]{2,}[A-Z]*_[a-f0-9]{4}\b', content):
                has_valid_diagram = True

        if has_valid_diagram:
            if self.valves.DEBUG_MODE:
                print("[Gradient Pipe] Response contains valid diagram from tool")
            return content

        # The LLM generated its own diagram or omitted it - inject the correct one
        if self.valves.DEBUG_MODE:
            print("[Gradient Pipe] Injecting correct diagram(s) into response")

        # Remove any malformed mermaid blocks the LLM generated
        content = self._remove_invalid_mermaid(content)

        # Build the correct diagram section (only valid diagrams)
        diagram_section = "\n\n"
        for diagram_info in valid_diagrams:
            diagram_section += diagram_info["diagram"] + "\n\n"

        # Add color key based on diagram type
        if valid_diagrams:
            tool_name = valid_diagrams[0]["tool"]
            if tool_name == "generate_referral_network_diagram":
                diagram_section += """**Color Key:**
- 🟢 Green = Tertiary hospitals
- 🔵 Blue = Community hospitals
- 🟣 Purple = Regional hospitals
- 🩷 Pink = Specialty hospitals
- 🟠 Orange = Rural hospitals
"""
            elif tool_name == "generate_path_diagram":
                diagram_section += """**Color Key:**
- 🟢 Green (thick border) = Start hospital
- 🔴 Red (thick border) = End hospital
"""
            elif tool_name == "generate_service_network_diagram":
                diagram_section += """**Color Key:**
- 🥇 Gold = #1 ranked
- 🥈 Silver = Top 3
- 🥉 Bronze = Other providers
"""

        # Insert diagram after the first paragraph or at the start
        lines = content.split('\n\n', 1)
        if len(lines) > 1:
            return lines[0] + diagram_section + lines[1]
        else:
            return content + diagram_section

    def _remove_invalid_mermaid(self, text: str) -> str:
        """Remove mermaid code blocks that weren't generated by our tools."""
        pattern = r'```mermaid\n[\s\S]*?```'
        matches = list(re.finditer(pattern, text))
        for match in reversed(matches):
            block = match.group()
            # Check if this block has our node ID pattern (initials + underscore + hash)
            if not re.search(r'\b[A-Z]{2,}[A-Z]*_[a-f0-9]{4}\b', block):
                text = text[:match.start()] + text[match.end():]
        return text

    def _execute_tool(self, tool_name: str, tool_args: Dict) -> str:
        """Execute a tool by calling the Azure Functions backend."""

        url = f"{self.valves.BACKEND_API_URL.strip().rstrip('/')}/api/tools/{tool_name}"

        headers = {"Content-Type": "application/json"}
        if self.valves.BACKEND_API_KEY:
            # Strip whitespace to prevent "Illegal header value" errors
            headers["x-functions-key"] = self.valves.BACKEND_API_KEY.strip()

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=tool_args, headers=headers)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            return json.dumps({"error": f"API error: {e.response.status_code}"})
        except Exception as e:
            return json.dumps({"error": str(e)})
