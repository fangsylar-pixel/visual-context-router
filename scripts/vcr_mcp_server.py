from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import ImageGrab  # noqa: E402

from visual_context_router import crop_roi, observe, route_observation  # noqa: E402


SERVER_INFO = {"name": "visual-context-router", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"


TOOLS = [
    {
        "name": "vcr_route",
        "description": "Analyze a screenshot and decide whether an agent should skip, send wireframe text, send ROI crops, or send the full image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to the current screenshot."},
                "previous_path": {"type": "string", "description": "Optional previous screenshot path."},
                "threshold": {"type": "number", "default": 0.003},
                "ocr": {"type": "boolean", "default": False},
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "vcr_observe",
        "description": "Convert a screenshot into a compact wireframe observation with optional token estimate.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string"},
                "previous_path": {"type": "string"},
                "threshold": {"type": "number", "default": 0.003},
                "ocr": {"type": "boolean", "default": False},
                "include_route": {"type": "boolean", "default": True},
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "vcr_crop",
        "description": "Crop a normalized region of interest from a screenshot.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string"},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                    "description": "Normalized bbox [x1, y1, x2, y2].",
                },
                "out_path": {"type": "string", "description": "Output path for the crop."},
                "padding": {"type": "number", "default": 0.0},
            },
            "required": ["image_path", "bbox", "out_path"],
        },
    },
    {
        "name": "vcr_capture_route",
        "description": "Capture the current screen locally, then return a low-token routing decision for Codex or another agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "previous_path": {"type": "string", "description": "Optional previous captured screenshot."},
                "out_path": {"type": "string", "description": "Optional output screenshot path."},
                "threshold": {"type": "number", "default": 0.003},
                "ocr": {"type": "boolean", "default": False},
            },
        },
    },
    {
        "name": "vcr_watch",
        "description": "Capture the current screen, compare it with the previous saved capture, update state, and return a low-token route decision.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state_dir": {
                    "type": "string",
                    "description": "Directory used to store previous/current screenshots.",
                },
                "threshold": {"type": "number", "default": 0.003},
                "ocr": {"type": "boolean", "default": False},
            },
        },
    },
]


def main() -> int:
    while True:
        message = _read_message()
        if message is None:
            return 0
        response = _handle_message(message)
        if response is not None:
            _write_message(response)


def _handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    try:
        if method == "initialize":
            return _result(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                },
            )
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return _result(request_id, {})
        if method == "tools/list":
            return _result(request_id, {"tools": TOOLS})
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments") or {}
            return _result(request_id, _call_tool(tool_name, arguments))
        return _error(request_id, -32601, f"Method not found: {method}")
    except Exception as exc:
        return _error(request_id, -32000, str(exc))


def _call_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "vcr_route":
        observation = observe(
            image_path=arguments["image_path"],
            previous_path=arguments.get("previous_path"),
            change_threshold=float(arguments.get("threshold", 0.003)),
            ocr=bool(arguments.get("ocr", False)),
        )
        payload = asdict(route_observation(observation))
        return _tool_text(payload)

    if tool_name == "vcr_observe":
        observation = observe(
            image_path=arguments["image_path"],
            previous_path=arguments.get("previous_path"),
            change_threshold=float(arguments.get("threshold", 0.003)),
            ocr=bool(arguments.get("ocr", False)),
        )
        payload = observation.to_dict(
            include_token_estimate=True,
            include_route=bool(arguments.get("include_route", True)),
        )
        return _tool_text(payload)

    if tool_name == "vcr_crop":
        out_path = crop_roi(
            image_path=arguments["image_path"],
            bbox=arguments["bbox"],
            out_path=arguments["out_path"],
            padding=float(arguments.get("padding", 0.0)),
        )
        return _tool_text({"out_path": str(out_path)})

    if tool_name == "vcr_capture_route":
        out_path = Path(arguments.get("out_path") or _default_capture_path())
        out_path.parent.mkdir(parents=True, exist_ok=True)
        image = ImageGrab.grab()
        image.save(out_path)
        observation = observe(
            image_path=out_path,
            previous_path=arguments.get("previous_path"),
            change_threshold=float(arguments.get("threshold", 0.003)),
            ocr=bool(arguments.get("ocr", False)),
        )
        payload = asdict(route_observation(observation))
        payload["captured_path"] = str(out_path)
        return _tool_text(payload)

    if tool_name == "vcr_watch":
        state_dir = Path(arguments.get("state_dir") or ROOT / ".vcr")
        state_dir.mkdir(parents=True, exist_ok=True)
        previous = state_dir / "previous-screen.png"
        current = state_dir / "current-screen.png"
        image = ImageGrab.grab()
        image.save(current)
        observation = observe(
            image_path=current,
            previous_path=previous if previous.exists() else None,
            change_threshold=float(arguments.get("threshold", 0.003)),
            ocr=bool(arguments.get("ocr", False)),
        )
        payload = asdict(route_observation(observation))
        current.replace(previous)
        payload["captured_path"] = str(previous)
        payload["used_previous"] = observation.change_score is not None
        return _tool_text(payload)

    raise ValueError(f"Unknown tool: {tool_name}")


def _default_capture_path() -> str:
    captures = ROOT / ".vcr" / "captures"
    return str(captures / f"screen-{int(time.time() * 1000)}.png")


def _tool_text(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ],
        "structuredContent": payload,
    }


def _read_message() -> dict[str, Any] | None:
    first = sys.stdin.buffer.readline()
    if not first:
        return None

    stripped = first.strip()
    if stripped.startswith(b"{"):
        return json.loads(stripped.decode("utf-8"))

    headers: dict[str, str] = {}
    line = first
    while line and line.strip():
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.lower()] = value.strip()
        line = sys.stdin.buffer.readline()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(message: dict[str, Any]) -> None:
    body = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


if __name__ == "__main__":
    raise SystemExit(main())
