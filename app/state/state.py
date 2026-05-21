"""Agent state management for shared context across agents."""

from typing import Any

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """
    Shared state for the multi-agent system.

    This state is shared across all agents and the supervisor.
    It contains:
    - messages: Conversation history
    - task_type: Type of request (image/audio/video)
    - task_data: Input data for processing
    - results: Aggregated results from all agents
    - metadata: Additional context information
    """

    # Base MessagesState already has 'messages'
    # We add our custom fields below
    task_type: str
    task_data: dict[str, Any]
    results: dict[str, Any]
    metadata: dict[str, Any]
    current_agent: str
    error: str | None
