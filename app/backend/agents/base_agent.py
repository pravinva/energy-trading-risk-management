"""
BaseAgent Framework
Foundation for all trading agents with memory, tools, and reasoning
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.backend.agents.llm_client import DatabricksLLMClient, Message, Tool, ToolCall
from app.backend.agents.tools import AgentTools
from app.backend.database import execute_sql
from app.backend.config import get_settings


class AgentDecision(BaseModel):
    """Agent's trading decision"""

    decision_type: str  # 'BUY', 'SELL', 'HOLD', 'CLOSE', 'REBALANCE'
    instrument: str
    volume_mw: float
    price: Optional[float] = None
    reasoning: str
    confidence: float  # 0.0 to 1.0
    tool_calls: List[str] = []
    metadata: Dict[str, Any] = {}


class AgentState(BaseModel):
    """Agent's current state"""

    agent_id: str
    session_id: str
    conversation_history: List[Message] = []
    decisions_made: List[AgentDecision] = []
    current_objective: Optional[str] = None
    context: Dict[str, Any] = {}


class BaseAgent:
    """
    Base class for all trading agents
    Provides LLM integration, tool execution, and memory management
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        agent_name: str,
        description: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize base agent

        Args:
            agent_id: Unique agent identifier
            agent_type: Agent type (QUANT, RISK, EXECUTION, FORECAST)
            agent_name: Human-readable name
            description: Agent description
            system_prompt: Core instructions
            temperature: LLM temperature
            max_tokens: Max response tokens
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.description = description
        self.system_prompt = system_prompt
        self.catalog = get_settings().apex_catalog

        # Initialize LLM client
        self.llm_client = DatabricksLLMClient(
            temperature=temperature, max_tokens=max_tokens
        )

        # Initialize tools
        self.tools = AgentTools()
        self.available_tools = self._get_available_tools()

        # State management
        self.state = AgentState(
            agent_id=agent_id, session_id=str(uuid.uuid4())
        )

    def _get_available_tools(self) -> List[Tool]:
        """Get available tools for this agent"""
        tool_definitions = self.tools.get_tool_definitions()
        return [
            Tool(
                name=tool['name'],
                description=tool['description'],
                input_schema=tool['input_schema'],
            )
            for tool in tool_definitions
        ]

    async def think(self, objective: str) -> str:
        """
        Agent reasoning step - analyze objective and plan approach

        Args:
            objective: What the agent should think about

        Returns:
            Agent's thoughts/analysis
        """
        self.state.current_objective = objective

        # Add objective to conversation
        user_message = Message(
            role='user',
            content=f"Please analyze the following objective and explain your approach:\n\n{objective}",
        )
        self.state.conversation_history.append(user_message)

        # Get LLM response
        response = await self.llm_client.chat(
            messages=self.state.conversation_history,
            system_prompt=self.system_prompt,
        )

        # Add response to history
        assistant_message = Message(role='assistant', content=response.content)
        self.state.conversation_history.append(assistant_message)

        # Save to memory
        await self._save_to_memory(user_message)
        await self._save_to_memory(assistant_message)

        return response.content

    async def act(self, instruction: str) -> AgentDecision:
        """
        Agent action step - make a trading decision using tools

        Args:
            instruction: Trading instruction/objective

        Returns:
            Agent's trading decision
        """
        # Add instruction to conversation
        user_message = Message(
            role='user',
            content=f"Execute the following instruction and make a trading decision:\n\n{instruction}",
        )
        self.state.conversation_history.append(user_message)

        # Tool execution loop
        max_iterations = 10
        tool_calls_made: List[str] = []

        for iteration in range(max_iterations):
            # Get LLM response with tools
            response = await self.llm_client.chat(
                messages=self.state.conversation_history,
                tools=self.available_tools,
                system_prompt=self.system_prompt,
            )

            # If no tool calls, extract decision from response
            if not response.tool_calls:
                decision = self._parse_decision_from_text(
                    response.content, tool_calls_made
                )
                self.state.decisions_made.append(decision)

                # Save to memory
                await self._save_to_memory(user_message)
                await self._save_to_memory(
                    Message(role='assistant', content=response.content)
                )

                return decision

            # Execute tool calls
            for tool_call in response.tool_calls:
                try:
                    tool_result = await self.tools.execute_tool(
                        tool_name=tool_call.name, tool_input=tool_call.input
                    )
                    tool_calls_made.append(tool_call.name)

                    # Add tool result to conversation
                    tool_message = Message(
                        role='user',
                        content=f"Tool {tool_call.name} returned:\n{json.dumps(tool_result, indent=2, default=str)}",
                    )
                    self.state.conversation_history.append(tool_message)

                except Exception as e:
                    # Tool execution failed
                    error_message = Message(
                        role='user',
                        content=f"Tool {tool_call.name} failed: {str(e)}",
                    )
                    self.state.conversation_history.append(error_message)

        # Max iterations reached - return HOLD decision
        return AgentDecision(
            decision_type='HOLD',
            instrument='UNKNOWN',
            volume_mw=0.0,
            reasoning='Max iterations reached without clear decision',
            confidence=0.0,
            tool_calls=tool_calls_made,
        )

    def _parse_decision_from_text(
        self, text: str, tool_calls: List[str]
    ) -> AgentDecision:
        """
        Parse trading decision from LLM response text

        Args:
            text: LLM response
            tool_calls: Tools used

        Returns:
            Parsed decision
        """
        # Try to extract JSON decision from text
        try:
            # Look for JSON block in text
            import re

            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                decision_dict = json.loads(json_match.group(1))
                return AgentDecision(**decision_dict, tool_calls=tool_calls)
        except Exception:
            pass

        # Fallback: parse from text
        text_lower = text.lower()

        # Determine decision type
        if 'buy' in text_lower or 'purchase' in text_lower:
            decision_type = 'BUY'
            confidence = 0.5
        elif 'sell' in text_lower:
            decision_type = 'SELL'
            confidence = 0.5
        else:
            decision_type = 'HOLD'
            confidence = 0.7

        return AgentDecision(
            decision_type=decision_type,
            instrument='NSW1',  # Default
            volume_mw=100.0,  # Default
            reasoning=text,
            confidence=confidence,
            tool_calls=tool_calls,
        )

    async def collaborate(
        self, other_agent_id: str, message: str, message_type: str = 'QUERY'
    ) -> str:
        """
        Send message to another agent

        Args:
            other_agent_id: Target agent ID
            message: Message content
            message_type: Message type (QUERY, PROPOSAL, etc.)

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())

        # Save message to database
        sql = f"""
        INSERT INTO {self.catalog}.strategy.agent_messages
        (message_id, from_agent_id, to_agent_id, session_id, timestamp, message_type, subject, content, priority, status)
        VALUES (
            '{message_id}',
            '{self.agent_id}',
            '{other_agent_id}',
            '{self.state.session_id}',
            current_timestamp(),
            '{message_type}',
            'Agent Collaboration',
            '{json.dumps({"message": message})}',
            'MEDIUM',
            'SENT'
        )
        """
        await execute_sql(sql)

        return message_id

    async def _save_to_memory(self, message: Message):
        """Save message to agent memory"""
        try:
            sql = f"""
            INSERT INTO {self.catalog}.strategy.agent_memory
            (memory_id, agent_id, session_id, timestamp, role, content, metadata)
            VALUES (
                '{str(uuid.uuid4())}',
                '{self.agent_id}',
                '{self.state.session_id}',
                current_timestamp(),
                '{message.role}',
                '{message.content.replace("'", "''")}',
                '{"{}"}'
            )
            """
            await execute_sql(sql)
        except Exception as e:
            # Memory save failed, but don't break the agent
            print(f"Failed to save to memory: {e}")

    async def get_recent_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent memory"""
        try:
            sql = f"""
            SELECT timestamp, role, content
            FROM {self.catalog}.strategy.agent_memory
            WHERE agent_id = '{self.agent_id}'
              AND session_id = '{self.state.session_id}'
            ORDER BY timestamp DESC
            LIMIT {limit}
            """
            rows = await execute_sql(sql)
            return rows
        except Exception:
            return []

    def reset_session(self):
        """Reset agent session"""
        self.state = AgentState(
            agent_id=self.agent_id, session_id=str(uuid.uuid4())
        )

    def get_state(self) -> AgentState:
        """Get current agent state"""
        return self.state

    async def log_decision(self, decision: AgentDecision, strategy_id: str):
        """
        Log decision to database

        Args:
            decision: Agent's decision
            strategy_id: Strategy ID
        """
        try:
            sql = f"""
            INSERT INTO {self.catalog}.strategy.execution_log
            (execution_id, strategy_id, agent_id, timestamp, action, instrument, volume_mw, price, reasoning, confidence, tool_calls, execution_status)
            VALUES (
                '{str(uuid.uuid4())}',
                '{strategy_id}',
                '{self.agent_id}',
                current_timestamp(),
                '{decision.decision_type}',
                '{decision.instrument}',
                {decision.volume_mw},
                {decision.price if decision.price else 'NULL'},
                '{decision.reasoning.replace("'", "''")}',
                {decision.confidence},
                array({','.join([f"'{tc}'" for tc in decision.tool_calls])}),
                'PROPOSED'
            )
            """
            await execute_sql(sql)
        except Exception as e:
            print(f"Failed to log decision: {e}")
