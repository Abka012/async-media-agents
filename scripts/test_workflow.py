#!/usr/bin/env python3
"""
Step 1: Core Payload Verification.

Validates that the pipeline can transport real base64-encoded payloads
without choking on data size or parsing. Uses only stdlib to generate
minimal valid media files.

Usage:
    python scripts/test_workflow.py
"""

import asyncio
import base64
import io
import logging
import os
import struct
import sys
import wave
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.audio_agent import AudioAgent
from app.agents.image_agent import ImageAgent
from app.agents.video_agent import VideoAgent
from app.graph.workflow import Workflow
from app.state.state import AgentState
from app.tools.mcp_client import mcp_client

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PASS = "✓"
FAIL = "✗"


def make_tiny_png_bytes() -> bytes:
    """Minimal 1x1 red PNG using only stdlib (zlib + struct)."""
    signature = b"\x89PNG\r\n\x1a\n"

    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc)

    raw = b"\x00\xff\x00\x00"
    compressed = zlib.compress(raw)
    idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc)

    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    return signature + ihdr + idat + iend


def make_tiny_wav_bytes() -> bytes:
    """Minimal valid WAV: 1 sec, 8 kHz, mono, 8-bit unsigned."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(8000)
        wav.writeframes(b"\x80" * 8000)
    return buf.getvalue()


def make_tiny_mp4_bytes() -> bytes:
    """Minimal valid MP4 skeleton (ftyp + mdat boxes)."""
    ftyp = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41"
    mdat_data = b"\x00" * 100
    mdat = struct.pack(">I", 8 + len(mdat_data)) + b"mdat" + mdat_data
    return ftyp + mdat


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


async def test_run_parallel() -> bool:
    """Feed all three real payloads through workflow.run_parallel()."""
    logger.info("── test_run_parallel ──────────────────────────")

    wf = Workflow()
    img, aud, vid = b64(make_tiny_png_bytes()), b64(make_tiny_wav_bytes()), b64(make_tiny_mp4_bytes())

    logger.info(f"  image payload: {len(img):>8} chars  ({len(make_tiny_png_bytes())} raw bytes)")
    logger.info(f"  audio payload: {len(aud):>8} chars  ({len(make_tiny_wav_bytes())} raw bytes)")
    logger.info(f"  video payload: {len(vid):>8} chars  ({len(make_tiny_mp4_bytes())} raw bytes)")

    try:
        result = await wf.run_parallel(image_data=img, audio_data=aud, video_data=vid)
        # After the graph run, task_data survives in the returned state
        td = result.get("task_data", {})
        assert td.get("image_data") == img, "image_data mismatch after transport"
        assert td.get("audio_data") == aud, "audio_data mismatch after transport"
        assert td.get("video_data") == vid, "video_data mismatch after transport"
        assert result.get("error") is None, f"error field set: {result['error']}"
        logger.info(f"  {PASS} payloads preserved in final state ({len(td)} keys)")
        logger.info(f"  {PASS} no errors")
        return True
    except Exception as e:
        logger.error(f"  {FAIL} {e}")
        return False


async def test_individual_agents() -> bool:
    """Each agent called directly with a real base64 payload."""
    logger.info("── test_individual_agents ─────────────────────")
    ok = True

    for name, AgentCls, data_key, result_key, payload_fn in [
        ("ImageAgent", ImageAgent, "image_data", "image_agent", make_tiny_png_bytes),
        ("AudioAgent", AudioAgent, "audio_data", "audio_agent", make_tiny_wav_bytes),
        ("VideoAgent", VideoAgent, "video_data", "video_agent", make_tiny_mp4_bytes),
    ]:
        try:
            agent = AgentCls()
            state: AgentState = {
                "messages": [],
                "task_type": result_key,
                "task_data": {data_key: b64(payload_fn())},
                "results": {},
                "metadata": {},
                "current_agent": "",
                "error": None,
            }
            result = await agent.run(state)
            r = result.get("results", {}).get(result_key, {})
            assert r.get("status") == "completed", f"status not completed: {r}"
            logger.info(f"  {PASS} {name}: status={r['status']} result={r.get('processing_result', '<none>')}")
        except Exception as e:
            logger.error(f"  {FAIL} {name}: {e}")
            ok = False
    return ok


async def test_mcp_client_batch() -> bool:
    """MCPClient.batch_process with all three payloads."""
    logger.info("── test_mcp_client_batch ──────────────────────")
    try:
        results = await mcp_client.batch_process(
            image_data=b64(make_tiny_png_bytes()),
            audio_data=b64(make_tiny_wav_bytes()),
            video_data=b64(make_tiny_mp4_bytes()),
        )
        assert "process_image" in results, "missing process_image"
        assert "process_audio" in results, "missing process_audio"
        assert "process_video" in results, "missing process_video"
        for name, r in results.items():
            assert r["status"] == "success", f"{name} status not success: {r}"
        logger.info(f"  {PASS} all 3 tools returned success")
        return True
    except Exception as e:
        logger.error(f"  {FAIL} {e}")
        return False


async def test_large_payload() -> bool:
    """~1 MB of random data through MCPClient to verify no truncation."""
    logger.info("── test_large_payload ─────────────────────────")
    size_kb = 1024
    raw = os.urandom(size_kb * 1024)
    large_b64 = b64(raw)
    logger.info(f"  payload: {len(large_b64)} chars (~{size_kb} KB raw)")
    try:
        result = await mcp_client.process_image(large_b64)
        assert result["status"] == "success"
        logger.info(f"  {PASS} processed without error")
        return True
    except Exception as e:
        logger.error(f"  {FAIL} {e}")
        return False


async def test_payload_integrity() -> bool:
    """Generate → base64 → decode → verify bytes match."""
    logger.info("── test_payload_integrity ─────────────────────")
    ok = True

    for label, make_fn in [
        ("PNG", make_tiny_png_bytes),
        ("WAV", make_tiny_wav_bytes),
        ("MP4", make_tiny_mp4_bytes),
    ]:
        original = make_fn()
        encoded = b64(original)
        decoded = base64.b64decode(encoded)
        if decoded == original:
            logger.info(f"  {PASS} {label}: {len(original)} B → {len(encoded)} chars → {len(decoded)} B  OK")
        else:
            logger.error(f"  {FAIL} {label}: integrity check failed")
            ok = False
    return ok


async def test_partial_payloads() -> bool:
    """run_parallel with only 1-2 payloads (None for others)."""
    logger.info("── test_partial_payloads ──────────────────────")
    wf = Workflow()
    ok = True

    for desc, kwargs in [
        ("only image", {"image_data": b64(make_tiny_png_bytes())}),
        ("only audio", {"audio_data": b64(make_tiny_wav_bytes())}),
        ("only video", {"video_data": b64(make_tiny_mp4_bytes())}),
        ("image+audio", {"image_data": b64(make_tiny_png_bytes()), "audio_data": b64(make_tiny_wav_bytes())}),
    ]:
        try:
            result = await wf.run_parallel(**kwargs)
            td = result.get("task_data", {})
            # Only the provided key(s) should appear
            for k in ("image_data", "audio_data", "video_data"):
                if k in kwargs:
                    assert td.get(k) == kwargs[k], f"{k} mismatch"
            logger.info(f"  {PASS} {desc}: task_data keys = {list(td.keys())}")
        except Exception as e:
            logger.error(f"  {FAIL} {desc}: {e}")
            ok = False
    return ok


async def main() -> bool:
    logger.info("")
    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║   Step 1: Core Payload Verification             ║")
    logger.info("╚══════════════════════════════════════════════════╝")
    logger.info("")

    tests = [
        ("payload_integrity", test_payload_integrity()),
        ("run_parallel (all 3)", test_run_parallel()),
        ("partial_payloads", test_partial_payloads()),
        ("individual_agents", test_individual_agents()),
        ("mcp_client_batch", test_mcp_client_batch()),
        ("large_payload (~1 MB)", test_large_payload()),
    ]

    results: dict[str, bool] = {}
    for name, coro in tests:
        results[name] = await coro
        logger.info("")

    logger.info("════════════════════════════════════════════════════")
    logger.info(" SUMMARY")
    logger.info("")
    all_pass = True
    for name, passed in results.items():
        sym = PASS if passed else FAIL
        logger.info(f"  {sym}  {name}")
        all_pass = all_pass and passed
    logger.info("")

    if all_pass:
        logger.info(f" {PASS} All payload verification tests passed.")
        logger.info("  The pipeline transports base64 payloads without issues.")
        logger.info("  Ready for Step 2: swap mocks for real processing.")
    else:
        logger.warning(f" {FAIL} Some tests failed. Review output above.")
    logger.info("")

    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
