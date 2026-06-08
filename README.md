# async-media-agents

Async Multi-Agent POC using LangGraph + FastMCP + real media processing.

## Overview

A lightweight async multi-agent system that processes images, audio, and video via base64-encoded payloads. Uses LangGraph for workflow orchestration, FastMCP for tool registration, and real processing libraries (Pillow, OpenCV, stdlib `wave`).

## Architecture

```
                User Request
                      |
              SupervisorAgent
                      |
       Fan-out (parallel conditional edge)
      ┌──────────┼──────────┐
      |          |          |
  ImageAgent  AudioAgent VideoAgent
      |          |          |
  Pillow     stdlib wave  OpenCV
  processor   processor   processor
      |          |          |
      └──────────┼──────────┘
           Fan-in to Aggregator
```

## Features

- ✅ **Real media processing** — Powered by Pillow (Images), OpenCV (Video), and stdlib `wave` (Audio).
- ✅ **Parallel execution** — High-performance fan-out/fan-in orchestration using LangGraph.
- ✅ **MCP Integration** — Model Context Protocol support via FastMCP for tool registration.
- ✅ **Robust error handling** — Graceful recovery from corrupt base64 or invalid formats.
- ✅ **Shared state** — Concurrent-safe state management via `Annotated` reducers.
- ✅ **Type Safety** — Comprehensive static analysis with `basedpyright`.

## Requirements

```text
langgraph
langchain
fastmcp
Pillow
opencv-python-headless
numpy
pytest
pytest-asyncio
```

## Setup

### 1. Create and activate a virtual environment

```bash
# Create the virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows (cmd)
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Project Structure

```text
project/
├── async_media_agents/
│   ├── agents/
│   │   ├── image_agent.py         # Specialized image logic
│   │   ├── audio_agent.py         # Specialized audio logic
│   │   ├── video_agent.py         # Specialized video logic
│   │   └── supervisor.py          # Orchestration & routing
│   │
│   ├── tools/
│   │   ├── mcp_server.py          # FastMCP server registration
│   │   ├── mcp_client.py          # Async client interface
│   │   └── processors/            # Pure processing logic (decoupled)
│   │       ├── image_processor.py # Pillow-based
│   │       ├── audio_processor.py # stdlib wave
│   │       └── video_processor.py # OpenCV-based
│   │
│   ├── graph/
│   │   └── workflow.py            # LangGraph workflow definition
│   │
│   ├── state/
│   │   ├── state.py               # Shared AgentState with reducers
│   │   └── shared_memory.py       # Global shared context utilities
│   │
│   └── __init__.py
│
├── scripts/
│   └── test_workflow.py           # Integration & payload tests
│
├── main.py                         # CLI demo & examples
├── requirements.txt
├── pyproject.toml                  # Project & Tool configuration
└── README.md
```

## Usage

### Run the demo

```bash
python main.py
```

The demo demonstrates three core patterns:
1. **Text-based routing** — Auto-detects task type from user natural language.
2. **Parallel processing** — Simultaneously processes multiple media types via fan-out.
3. **Supervisor workflow** — Uses the Supervisor agent to route to a single target.

### Run tests

Tests can be executed directly or through `pytest`:

```bash
# Direct execution (includes payload generation logs)
python scripts/test_workflow.py

# Using pytest
pytest scripts/test_workflow.py
```

The test suite covers:
- Base64 payload integrity (PNG, WAV, MP4)
- Real metadata extraction via processors
- Parallel transport through the workflow
- Partial payload handling
- Robust error handling for corrupted data

### Programmatic use

```python
from async_media_agents.graph.workflow import Workflow

wf = Workflow()

# Text-based — auto-routes to image/audio/video agent
result = await wf.run("Analyze this image")

# Parallel — feeds base64 to all three agents
result = await wf.run_parallel(
    image_data="base64_encoded_png",
    audio_data="base64_encoded_wav",
    video_data="base64_encoded_mp4",
)
```

## Processing Pipeline

| Media   | Library               | Extracted Metadata                                    |
|---------|-----------------------|-------------------------------------------------------|
| Image   | Pillow                | width, height, format, mode, thumbnail                |
| Audio   | stdlib `wave`         | duration, sample rate, channels, sample width, frames |
| Video   | opencv-python-headless | duration, fps, resolution, frame count, dimensions    |

All processors return structured dicts: `{"status": "success", "metadata": {...}}` or `{"status": "error", "error": "..."}`.

## Static Analysis

The project uses `basedpyright` for type checking:

```bash
pip install basedpyright
basedpyright .
```

Configuration lives in `pyproject.toml` under `[tool.pyright]`.

## State Management

`AgentState` extends `MessagesState` with custom fields. Fields written concurrently during parallel fan-out use `Annotated` reducers for safe merging:

- `results` — `_merge_results` dict merge
- `metadata` — `_merge_results` dict merge
- `current_agent` — `_last_wins`
- `error` — `_last_wins`
