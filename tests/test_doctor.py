import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts" / "doctor.py"


def _load_doctor():
    spec = importlib.util.spec_from_file_location("doctor", DOCTOR)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_decode_content_length_message() -> None:
    doctor = _load_doctor()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})
    message = f"Content-Length: {len(body)}\r\n\r\n{body}"

    assert doctor.decode_content_length_message(message)["result"]["ok"] is True
