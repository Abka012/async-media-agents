#!/usr/bin/env python3
"""Main entry point for the multi-agent system."""

import asyncio

from app.agents.supervisor import SupervisorAgent
from app.graph.workflow import Workflow


async def main():
    """Run the multi-agent system."""
    print("=" * 60)
    print("Multi-Agent POC: Async Image/Audio/Video Processing")
    print("=" * 60)

    # Example 1: Text-based workflow
    print("\n[Example 1] Text-based task routing")
    print("-" * 40)
    workflow = Workflow()

    user_input = "Can you analyze this image for me?"
    print(f"User input: '{user_input}'")
    result = await workflow.run(user_input)
    print(f"Result: {result.get('results', {})}")

    # Example 2: Parallel media processing
    print("\n[Example 2] Parallel media processing")
    print("-" * 40)
    result = await workflow.run_parallel(
        image_data="base64_image_data_placeholder",
        audio_data="base64_audio_data_placeholder",
        video_data="base64_video_data_placeholder",
    )
    print(f"Parallel processing result: {result.get('results', {})}")

    # Example 3: Supervisor workflow
    print("\n[Example 3] Supervisor agent workflow")
    print("-" * 40)
    supervisor = SupervisorAgent()

    supervisor_input = "Process an audio file and extract metadata"
    print(f"Supervisor input: '{supervisor_input}'")
    result = await supervisor.run(supervisor_input)
    print(f"Supervisor result: {result}")

    print("\n" + "=" * 60)
    print("Multi-agent system completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
