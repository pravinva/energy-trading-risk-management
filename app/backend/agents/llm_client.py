"""
Databricks Foundation Model API Client
Integrates with Databricks FM API to use Claude Sonnet 4.5
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import httpx
from databricks.sdk import WorkspaceClient
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message"""
    role: str  # 'user', 'assistant', 'system'
    content: str


class Tool(BaseModel):
    """Tool definition for function calling"""
    name: str
    description: str
    input_schema: Dict[str, Any]


class ToolCall(BaseModel):
    """Tool call from LLM"""
    id: str
    name: str
    input: Dict[str, Any]


class LLMResponse(BaseModel):
    """LLM response"""
    content: str
    role: str = 'assistant'
    tool_calls: Optional[List[ToolCall]] = None
    stop_reason: Optional[str] = None
    tokens_used: int = 0
    model: str = ''


class DatabricksLLMClient:
    """
    Client for Databricks Foundation Model API
    Uses Claude Sonnet 4.5 via Databricks serving endpoints
    """

    def __init__(
        self,
        model: str = 'databricks-meta-llama-3-1-405b-instruct',  # Default model
        temperature: float = 0.7,
        max_tokens: int = 4096,
        endpoint_name: Optional[str] = None,
    ):
        """
        Initialize Databricks LLM client

        Args:
            model: Model name (will use Sonnet 4.5 when available)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            endpoint_name: Optional custom endpoint name
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.endpoint_name = endpoint_name or self._get_default_endpoint()

        # Initialize Databricks client
        self.workspace_client = WorkspaceClient()
        self.host = os.environ.get('DATABRICKS_HOST', '').strip()
        if self.host and not self.host.startswith('http'):
            self.host = f'https://{self.host}'
        self.host = self.host.rstrip('/')

        # Get authentication token
        self.token = self._get_auth_token()

    def _get_default_endpoint(self) -> str:
        """Get default endpoint for model"""
        # Map model names to Databricks FM API endpoints
        # TODO: Update when Sonnet 4.5 is available
        endpoint_map = {
            'claude-sonnet-4-5': 'databricks-claude-sonnet-4-5',  # Future
            'databricks-meta-llama-3-1-405b-instruct': 'databricks-meta-llama-3-1-405b-instruct',
        }
        return endpoint_map.get(self.model, self.model)

    def _get_auth_token(self) -> str:
        """Get Databricks authentication token"""
        token = os.environ.get('DATABRICKS_TOKEN', '')
        if not token:
            # Use workload identity
            auth_headers = self.workspace_client.config.authenticate()
            bearer = auth_headers.get('Authorization', '')
            if bearer.startswith('Bearer '):
                token = bearer[7:]
        if not token:
            raise RuntimeError('Databricks authentication not configured')
        return token

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Send chat completion request to Databricks FM API

        Args:
            messages: List of chat messages
            tools: Optional list of tools for function calling
            system_prompt: Optional system prompt

        Returns:
            LLM response
        """
        # Prepare request payload
        payload: Dict[str, Any] = {
            'messages': [{'role': m.role, 'content': m.content} for m in messages],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
        }

        # Add system prompt if provided
        if system_prompt:
            payload['system'] = system_prompt

        # Add tools if provided
        if tools:
            payload['tools'] = [
                {
                    'name': t.name,
                    'description': t.description,
                    'input_schema': t.input_schema,
                }
                for t in tools
            ]

        # Make request to Databricks FM API
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f'{self.host}/serving-endpoints/{self.endpoint_name}/invocations',
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

        # Parse response
        return self._parse_response(result)

    def _parse_response(self, result: Dict[str, Any]) -> LLMResponse:
        """Parse FM API response"""
        choices = result.get('choices', [])
        if not choices:
            raise ValueError('No choices in LLM response')

        choice = choices[0]
        message = choice.get('message', {})
        content = message.get('content', '')
        tool_calls_raw = message.get('tool_calls', [])

        # Parse tool calls if present
        tool_calls = None
        if tool_calls_raw:
            tool_calls = [
                ToolCall(
                    id=tc.get('id', ''),
                    name=tc.get('function', {}).get('name', ''),
                    input=json.loads(tc.get('function', {}).get('arguments', '{}')),
                )
                for tc in tool_calls_raw
            ]

        # Extract usage info
        usage = result.get('usage', {})
        tokens_used = usage.get('total_tokens', 0)

        return LLMResponse(
            content=content,
            role='assistant',
            tool_calls=tool_calls,
            stop_reason=choice.get('finish_reason'),
            tokens_used=tokens_used,
            model=result.get('model', self.model),
        )

    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Stream chat completion (for future use)
        Not implemented yet
        """
        raise NotImplementedError('Streaming not yet implemented')


class SonnetAgent:
    """
    Wrapper for Claude Sonnet 4.5 agent via Databricks FM API
    Provides high-level interface for agent interactions
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        system_prompt: str,
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize Sonnet agent

        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            system_prompt: Agent's core instructions
            tools: Available tools for this agent
            temperature: LLM temperature
            max_tokens: Max response tokens
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.llm_client = DatabricksLLMClient(
            model='databricks-meta-llama-3-1-405b-instruct',  # TODO: Update to Sonnet 4.5
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.conversation_history: List[Message] = []

    async def chat(self, user_message: str) -> LLMResponse:
        """
        Send message to agent and get response

        Args:
            user_message: User's message

        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append(Message(role='user', content=user_message))

        # Get response from LLM
        response = await self.llm_client.chat(
            messages=self.conversation_history,
            tools=self.tools if self.tools else None,
            system_prompt=self.system_prompt,
        )

        # Add assistant response to history
        self.conversation_history.append(Message(role='assistant', content=response.content))

        return response

    async def chat_with_tools(
        self, user_message: str, tool_executor: Any
    ) -> LLMResponse:
        """
        Chat with tool execution loop

        Args:
            user_message: User's message
            tool_executor: Function to execute tools

        Returns:
            Final response after tool execution
        """
        # Add user message
        self.conversation_history.append(Message(role='user', content=user_message))

        max_iterations = 10
        for _ in range(max_iterations):
            # Get response
            response = await self.llm_client.chat(
                messages=self.conversation_history,
                tools=self.tools if self.tools else None,
                system_prompt=self.system_prompt,
            )

            # If no tool calls, return response
            if not response.tool_calls:
                self.conversation_history.append(
                    Message(role='assistant', content=response.content)
                )
                return response

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_result = await tool_executor(
                    tool_name=tool_call.name, tool_input=tool_call.input
                )

                # Add tool result to conversation
                self.conversation_history.append(
                    Message(
                        role='user',
                        content=f'Tool {tool_call.name} result: {json.dumps(tool_result)}',
                    )
                )

        # Max iterations reached
        return LLMResponse(
            content='Max iterations reached in tool execution loop',
            role='assistant',
        )

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

    def get_conversation_history(self) -> List[Message]:
        """Get conversation history"""
        return self.conversation_history
