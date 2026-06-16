# Visual Context Router

Token-aware visual context routing for Codex and AI agents.

Visual Context Router turns screenshots into compact, structured observations so an agent does not need to send a full image every time it wants to understand a UI. It combines screenshot diffing, region-of-interest crops, lightweight UI element detection, optional OCR, and wireframe-style prompts.

The goal is simple: **send pixels only when pixels are the best evidence**.

## Why This Exists

Vision-capable agents often waste tokens on:

- Unchanged screens.
- Full screenshots when only a dialog or button changed.
- Re-reading UI text that could be represented as structured state.
- Long screen recordings where most frames are redundant.

Visual Context Router sits before the model and decides what to forward:

```text
screen / frame
  -> visual diff
  -> optional OCR + UI element extraction
  -> compact wireframe prompt
  -> optional ROI crops
  -> model
```

## Features

- Screenshot diffing with MSE and normalized change score.
- Compact wireframe prompt generation.
- Region-of-interest cropping by normalized coordinates.
- Heuristic UI element detection with optional OpenCV enhancement.
- Optional OCR with `pytesseract`.
- JSON observations for easy agent integration.
- Routing decisions: `skip`, `wireframe_only`, `wireframe_plus_roi`, or `full_image`.
- Codex plugin metadata and skill instructions.

## Install

```bash
pip install -e .
```

Optional OCR and OpenCV support:

```bash
pip install -e ".[all]"
```

## Quick Start

Analyze a screenshot:

```bash
vcr observe examples/sample-screen.png
```

Compare two screenshots and emit JSON:

```bash
vcr observe examples/sample-screen-after.png --previous examples/sample-screen.png --json
```

Crop a region of interest using normalized coordinates:

```bash
vcr crop examples/sample-screen.png --bbox 0.70,0.05,0.98,0.30 --out roi.png
```

Estimate visual token savings:

```bash
vcr observe examples/sample-screen.png --json --token-budget
```

Ask the router what an agent should send next:

```bash
vcr route examples/sample-screen-after.png --previous examples/sample-screen.png --json
```

## Example Output

```json
{
  "changed": true,
  "change_score": 0.1842,
  "image": {
    "width": 1440,
    "height": 900
  },
  "elements": [
    {
      "id": 1,
      "type": "region",
      "text": "",
      "bbox": [0.1208, 0.1889, 0.4125, 0.2667],
      "confidence": 0.58
    }
  ],
  "wireframe": "Screen 1440x900. Changed: yes..."
}
```

## Routing Strategies

Visual Context Router can make an explicit routing decision for the next model call:

| Strategy | Meaning |
| --- | --- |
| `skip` | No meaningful visual change. Continue from action log or cached state. |
| `wireframe_only` | Send structured text state only. |
| `wireframe_plus_roi` | Send structured text plus a few local crops. |
| `full_image` | Send the full screenshot because the agent needs global reorientation. |

## Agent Pattern

Use the package as a router in front of a multimodal model:

```python
from visual_context_router import observe, route_observation

observation = observe(
    image_path="current.png",
    previous_path="previous.png",
    change_threshold=0.003,
)
decision = route_observation(observation)

if decision.strategy == "skip":
    prompt = "No semantic visual change. Continue from action log."
elif decision.include_wireframe:
    prompt = decision.model_payload
```

## Codex Plugin Usage

This repository includes `.codex-plugin/plugin.json` and a Codex skill under `skills/`.
After installing or sharing the plugin, ask Codex to use Visual Context Router when inspecting screenshots, browser captures, or UI automation state.

## Roadmap

- Accessibility tree adapters for browser and desktop automation.
- DOM change ingestion for browser agents.
- Better icon and control classification.
- Token savings benchmark suite.
- Model-facing observation cache.
- MCP server wrapper for direct tool calls.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Generate demo screenshots:

```bash
python scripts/make_demo_images.py
```

## GitHub Release Checklist

- Create a repository named `visual-context-router`.
- Push this folder as the repo root.
- Add screenshots from `examples/` to the README or project social preview.
- Tag the first release as `v0.1.0`.
- Share a short demo showing `full_image_tokens` vs `routed_text_tokens`.

## Commercial Angle

The open-source project is useful as a developer tool. Commercial value is likely in:

- Enterprise privacy-preserving local deployment.
- Higher-accuracy UI detection adapters.
- Token cost dashboards.
- Agent framework integrations.
- Browser and desktop automation SDKs.

## License

MIT
