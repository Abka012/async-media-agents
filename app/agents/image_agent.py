"""Image processing agent."""

from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from app.state.state import AgentState


class ImageAgent:
    """Agent specialized in image processing."""

    def __init__(self):
        self.name = "image_agent"
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("user", "{input}"),
            ]
        )

    system_prompt = """You are an image processing agent.

    Your role is to analyze and process images based on user requests.
    You can:
    - Extract image metadata
    - Identify objects, scenes, or people in images
    - Detect image properties (size, format, colors)
    - Apply filters or transformations

    Always use the available tools for processing images.
    """

    async def process_image(self, image_data: str, format: str = "png") -> str:
        """Process image data and return results."""
        from app.tools.mcp_client import mcp_client

        result = await mcp_client.process_image(image_data, format)
        return result["result"]

    async def extract_info(self, image_data: str) -> dict:
        """Extract metadata from image."""
        from app.tools.mcp_client import mcp_client

        return await mcp_client.process_image(image_data, "png")

    async def run(self, state: AgentState) -> dict[str, Any]:
        """Run the image agent."""
        task_data = state.get("task_data", {})

        # Get image data from task
        image_data = task_data.get("image_data", "")

        result = {
            "current_agent": self.name,
            "results": {
                "image_agent": {
                    "status": "completed",
                    "task_type": "image",
                },
            },
        }

        if image_data:
            # Process the image
            processed = await self.process_image(image_data, "png")
            result["results"]["image_agent"]["processing_result"] = processed

        return result

    async def process(self, image_data: str) -> dict[str, Any]:
        """Process image directly."""
        result = await self.process_image(image_data, "png")
        return {
            "status": "success",
            "agent": self.name,
            "result": result,
        }
