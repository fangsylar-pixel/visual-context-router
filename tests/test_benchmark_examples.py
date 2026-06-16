import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_examples_outputs_sample_case() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/benchmark_examples.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    sample = payload["benchmarks"][0]

    assert sample["name"] == "Sample dialog UI"
    assert sample["strategy"] == "wireframe_plus_roi"
    assert sample["saved_tokens"] > 0

