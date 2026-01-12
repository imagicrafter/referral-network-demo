"""
title: DO ADK Agent Pipe
description: Pipe for connecting Open WebUI to a DigitalOcean ADK Agent
author: Referral Network Demo
version: 1.1.0
license: MIT
"""

import json
import httpx
from typing import Iterator, List, Union
from pydantic import BaseModel, Field


class Pipe:
    """
    Open WebUI Pipe for DigitalOcean ADK Agents.

    This pipe forwards chat requests to a deployed DO ADK agent.

    DO ADK agents use a different endpoint format than OpenAI:
    - Endpoint: POST to the agent URL directly (no /api/v1/chat/completions)
    - Request: {"messages": [...]} or {"input": {"messages": [...]}}
    - Response: Plain text string (not OpenAI format)
    """

    class Valves(BaseModel):
        """Configuration options shown in Open WebUI admin panel."""

        DIGITALOCEAN_AGENT_URL: str = Field(
            default="https://agents.do-ai.run/YOUR-UUID/YOUR-ENVIRONMENT/run",
            description="The full URL of your deployed DO ADK agent (ends with /run)"
        )
        DIGITALOCEAN_API_KEY: str = Field(
            default="",
            description="Your Gradient Model Access Key (starts with sk-do-)"
        )
        REQUEST_TIMEOUT: int = Field(
            default=120,
            description="Request timeout in seconds"
        )
        DEBUG_MODE: bool = Field(
            default=False,
            description="Enable debug logging"
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "do_adk_agent"
        self.name = "DO ADK Agent"
        self.valves = self.Valves()

    def pipes(self) -> List[dict]:
        """Return available models/pipes."""
        return [
            {
                "id": "referral-network-agent",
                "name": "Referral Network Agent",
                "description": "Healthcare referral network analytics agent"
            }
        ]

    def pipe(
        self,
        body: dict,
        __user__: dict = None,
        __event_emitter__=None,
        __task__=None,
    ) -> Union[str, Iterator[str]]:
        """
        Process chat request and forward to DO ADK agent.

        Args:
            body: The request body containing messages
            __user__: User information from Open WebUI
            __event_emitter__: Event emitter for status updates
            __task__: Task type (e.g., "title_generation")

        Returns:
            Response string
        """

        if self.valves.DEBUG_MODE:
            print(f"[DO ADK Pipe] Request body: {json.dumps(body, indent=2)}")
            print(f"[DO ADK Pipe] Task: {__task__}")

        # Skip for title generation tasks - let Open WebUI handle it
        if __task__ == "title_generation":
            return ""

        # Validate configuration
        if not self.valves.DIGITALOCEAN_AGENT_URL or "YOUR-UUID" in self.valves.DIGITALOCEAN_AGENT_URL:
            return "Error: Please configure DIGITALOCEAN_AGENT_URL in the pipe settings. The URL should look like: https://agents.do-ai.run/UUID/ENVIRONMENT/run"

        if not self.valves.DIGITALOCEAN_API_KEY:
            return "Error: Please configure DIGITALOCEAN_API_KEY in the pipe settings."

        # Use the agent URL directly - DO ADK doesn't use /api/v1/chat/completions
        url = self.valves.DIGITALOCEAN_AGENT_URL.rstrip('/')

        headers = {
            "Authorization": f"Bearer {self.valves.DIGITALOCEAN_API_KEY}",
            "Content-Type": "application/json",
        }

        # Build payload in DO ADK format
        # The agent handles both {"messages": [...]} and {"input": {"messages": [...]}}
        messages = body.get("messages", [])

        payload = {
            "input": {
                "messages": messages
            }
        }

        if self.valves.DEBUG_MODE:
            print(f"[DO ADK Pipe] Sending to: {url}")
            print(f"[DO ADK Pipe] Payload: {json.dumps(payload, indent=2)}")

        try:
            return self._make_request(url, headers, payload)
        except Exception as e:
            error_msg = f"Error connecting to DO ADK agent: {str(e)}"
            if self.valves.DEBUG_MODE:
                print(f"[DO ADK Pipe] {error_msg}")
            return error_msg

    def _make_request(self, url: str, headers: dict, payload: dict) -> str:
        """Make request to DO ADK agent and return the response."""
        with httpx.Client(timeout=self.valves.REQUEST_TIMEOUT) as client:
            response = client.post(url, json=payload, headers=headers)

            if self.valves.DEBUG_MODE:
                print(f"[DO ADK Pipe] Response status: {response.status_code}")
                print(f"[DO ADK Pipe] Response headers: {dict(response.headers)}")

            response.raise_for_status()

            # DO ADK agents return plain text or JSON with the result
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                data = response.json()
                if self.valves.DEBUG_MODE:
                    print(f"[DO ADK Pipe] JSON Response: {json.dumps(data, indent=2)}")

                # Handle different response formats
                if isinstance(data, str):
                    return data
                elif isinstance(data, dict):
                    # Check common response fields
                    if "output" in data:
                        return data["output"]
                    elif "result" in data:
                        return data["result"]
                    elif "response" in data:
                        return data["response"]
                    elif "content" in data:
                        return data["content"]
                    elif "message" in data:
                        return data["message"]
                    else:
                        return json.dumps(data, indent=2)
                else:
                    return str(data)
            else:
                # Plain text response
                text = response.text
                if self.valves.DEBUG_MODE:
                    print(f"[DO ADK Pipe] Text Response: {text[:500]}...")
                return text
