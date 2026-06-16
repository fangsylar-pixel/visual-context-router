import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mcp_server_lists_tools() -> None:
    request = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n'
    result = subprocess.run(
        [sys.executable, "scripts/vcr_mcp_server.py"],
        input=request,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=True,
    )

    payload = _decode_content_length_message(result.stdout)
    tools = {tool["name"] for tool in payload["result"]["tools"]}

    assert {"vcr_route", "vcr_observe", "vcr_crop", "vcr_capture_route"} <= tools


def _decode_content_length_message(output: str) -> dict:
    _, _, body = output.partition("\r\n\r\n")
    if not body:
        _, _, body = output.partition("\n\n")
    return json.loads(body)
