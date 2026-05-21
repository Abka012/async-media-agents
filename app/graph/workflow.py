"""Workflow definition using LangGraph."""

from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agents.audio_agent import AudioAgent
from app.agents.image_agent import ImageAgent
from app.agents.supervisor import SupervisorAgent
from app.agents.video_agent import VideoAgent
from app.state.state import AgentState


class Workflow:
    """Multi-agent workflow with parallel execution support."""

    def __init__(self):
        self.image_agent = ImageAgent()
        self.audio_agent = AudioAgent()
        self.video_agent = VideoAgent()
        self.supervisor = SupervisorAgent()
        self.checkpointer = MemorySaver()
        self._build_workflow()

    def _build_workflow(self):
        """Build the parallel workflow graph."""
        workflow = StateGraph(AgentState)

        # Add all agent nodes
        workflow.add_node("supervisor", self.supervisor._supervisor_node)
        workflow.add_node("image_agent", self.image_agent.run)
        workflow.add_node("audio_agent", self.audio_agent.run)
        workflow.add_node("video_agent", self.video_agent.run)
        workflow.add_node("aggregator", self._aggregator)

        # Supervisor routes to appropriate agents based on task type
        workflow.add_conditional_edges(
            "supervisor",
            self._determine_task_type,
            {
                "image": "image_agent",
                "audio": "audio_agent",
                "video": "video_agent",
                "all": "start_parallel",
            },
        )

        # Start parallel execution node
        workflow.add_node("start_parallel", self._start_parallel)

        # Each agent routes to aggregator
        workflow.add_edge("image_agent", "aggregator")
        workflow.add_edge("audio_agent", "aggregator")
        workflow.add_edge("video_agent", "aggregator")

        # Aggregator produces final output and ends
        workflow.add_edge("aggregator", END)

        workflow.set_entry_point("supervisor")

        self.graph = workflow.compile(checkpointer=self.checkpointer)

    def _determine_task_type(self, state: AgentState) -> str:
        """Determine which agents to invoke based on task type."""
        task_type = state.get("task_type", "")
        messages = state.get("messages", [])

        # If task type not set, infer from messages
        if not task_type and messages:
            content = str(messages[-1].content).lower()
            if "image" in content or "photo" in content:
                return "image"
            elif "audio" in content or "sound" in content:
                return "audio"
            elif "video" in content or "movie" in content:
                return "video"
            else:
                return "all"  # Process all if not specified

        return task_type

    def _start_parallel(self, state: AgentState) -> dict[str, Any]:
        """Trigger parallel execution of all agents."""
        return {
            "current_agent": "parallel_executor",
            "metadata": {"execution_mode": "parallel"},
        }

    def _aggregator(self, state: AgentState) -> dict[str, Any]:
        """Aggregate results from all agents."""
        return {
            "current_agent": "aggregator",
            "results": {
                "status": "all_completed",
                "agents_executed": ["image", "audio", "video"],
                "message": "Multi-agent workflow completed successfully",
            },
        }

    async def run(self, user_input: str) -> dict[str, Any]:
        """Run the workflow with user input."""
        config: RunnableConfig = {"configurable": {"thread_id": "workflow-1"}}

        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_input)],
            "task_type": "",
            "task_data": {},
            "results": {},
            "metadata": {},
            "current_agent": "",
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state, config=config)
        return result

    async def run_parallel(
        self,
        image_data: str | None = None,
        audio_data: str | None = None,
        video_data: str | None = None,
    ) -> dict[str, Any]:
        """Run agents in parallel with data."""
        config: RunnableConfig = {"configurable": {"thread_id": "parallel-1"}}

        task_data = {
            k: v
            for k, v in [
                ("image_data", image_data),
                ("audio_data", audio_data),
                ("video_data", video_data),
            ]
            if v is not None
        }

        initial_state: AgentState = {
            "messages": [HumanMessage(content="Process the provided media files")],
            "task_type": "all",
            "task_data": task_data,
            "results": {},
            "metadata": {},
            "current_agent": "",
            "error": None,
        }

        result = await self.graph.ainvoke(initial_state, config=config)
        return result
