"""Audio processing agent."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from app.state.state import AgentState


class AudioAgent:
    """Agent specialized in audio processing."""

    def __init__(self):
        self.name = "audio_agent"
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("user", "{input}"),
            ]
        )

    system_prompt = """You are an audio processing agent.

    Your role is to analyze and process audio based on user requests.
    You can:
    - Extract audio metadata (duration, sample rate, etc.)
    - Detect audio content (speech, music, noise)
    - Identify audio characteristics (volume, pitch)
    - Process audio streams

    Always use the available tools for processing audio.
    """

    async def process_audio(self, audio_data: str, format: str = "mp3") -> str:
        """Process audio data and return results."""
        from app.tools.mcp_client import mcp_client

        result = await mcp_client.process_audio(audio_data, format)
        return result["result"]

    async def extract_info(self, audio_data: str) -> dict:
        """Extract metadata from audio."""
        from app.tools.mcp_client import mcp_client

        return await mcp_client.process_audio(audio_data, "mp3")

    async def run(self, state: AgentState) -> dict[str, Any]:
        """Run the audio agent."""
        task_data = state.get("task_data", {})

        # Get audio data from task
        audio_data = task_data.get("audio_data", "")

        result = {
            "current_agent": self.name,
            "results": {
                "audio_agent": {
                    "status": "completed",
                    "task_type": "audio",
                },
            },
        }

        if audio_data:
            # Process the audio
            processed = await self.process_audio(audio_data, "mp3")
            result["results"]["audio_agent"]["processing_result"] = processed

        return result

    async def process(self, audio_data: str) -> dict[str, Any]:
        """Process audio directly."""
        result = await self.process_audio(audio_data, "mp3")
        return {
            "status": "success",
            "agent": self.name,
            "result": result,
        }
