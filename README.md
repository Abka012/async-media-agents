# miniature-parakeet

Async Multi-Agent POC using LangGraph + FastMCP

## Overview

This project demonstrates a lightweight async multi-agent system in Python using:
- **LangGraph** - For building agent workflows
- **FastMCP** - For Model Context Protocol integration
- **asyncio** - For asynchronous orchestration

## Architecture

```
                User Request
                      |
              SupervisorAgent
                      |
      --------------------------------
      |              |              |
  ImageAgent     AudioAgent     VideoAgent
      |              |              |
  MCP Tool      MCP Tool       MCP Tool 
      \              |             /
       -------------Shared State----
                      |
               Final Aggregator
```

## Features

- ✅ MCP (Model Context Protocol) integration
- ✅ FastMCP tools
- ✅ Async orchestration with asyncio
- ✅ Deep Agents with specialized capabilities
- ✅ Sub-agents under supervisor
- ✅ Shared memory/context for coordination
- ✅ Agent coordination and routing
- ✅ Parallel execution of agents

## Installation

```bash
pip install -r requirements.txt
```

### Requirements

```
langgraph
langchain
fastmcp
```

## Project Structure

```
project/
├── app/
│   ├── agents/
│   │   ├── image_agent.py
│   │   ├── audio_agent.py
│   │   ├── video_agent.py
│   │   └── supervisor.py
│   │
│   ├── tools/
│   │   ├── mcp_server.py
│   │   ├── image_tool.py
│   │   ├── audio_tool.py
│   │   └── video_tool.py
│   │
│   ├── graph/
│   │   └── workflow.py
│   │
│   ├── state/
│   │   ├── state.py
│   │   └── shared_memory.py
│   │
│   ├── utils/
│   │   └── requirements.py
│   │
│   └── __init__.py
│
├── main.py
├── requirements.txt
└── README.md
```

## Usage

### Run the Multi-Agent System

```bash
python main.py
```

### Example Outputs

1. **Text-based task routing** - Automatically routes image/audio/video tasks based on user input analysis
2. **Parallel media processing** - Processes multiple media types simultaneously
3. **Supervisor agent workflow** - Orchestrates sub-agents for complex tasks

### Using the Workflow

```python
from app.graph.workflow import Workflow

workflow = Workflow()

# Run with text input (auto-detects task type)
result = await workflow.run("Analyze this image")

# Run with specific media data (parallel processing)
result = await workflow.run_parallel(
    image_data="base64_data",
    audio_data="base64_data", 
    video_data="base64_data"
)
```

### Using the Supervisor

```python
from app.agents.supervisor import SupervisorAgent

supervisor = SupervisorAgent()
result = await supervisor.run("Process an audio file")
```

## Agents

### SupervisorAgent
- Orchestrates all sub-agents
- Routes tasks based on content analysis
- Coordinates parallel execution
- Aggregates results

### ImageAgent
- Processes images (base64 encoded)
- Extracts metadata (dimensions, format)
- Identifies objects, scenes, or people

### AudioAgent
- Processes audio files (base64 encoded)
- Extracts metadata (duration, sample rate)
- Detects audio content characteristics

### VideoAgent
- Processes video files (base64 encoded)
- Extracts metadata (duration, resolution, FPS)
- Analyzes video content

## Tools (MCP)

All agents use MCP (Model Context Protocol) tools for processing:
- `process_image` - Image processing
- `process_audio` - Audio processing
- `process_video` - Video processing

## State Management

The system uses a shared `AgentState` that is passed between agents:
- `messages` - Conversation history
- `task_type` - Current task type (image/audio/video)
- `task_data` - Input data for processing
- `results` - Aggregated results from all agents
- `metadata` - Additional context information
- `current_agent` - Track which agent is running
- `error` - Error tracking
