# Visual Context Router

Token-aware visual context routing for Codex and AI agents.

Visual Context Router turns screenshots into compact, structured observations so an agent does not need to send a full image every time it wants to understand a UI. It combines screenshot diffing, region-of-interest crops, lightweight UI element detection, optional OCR, and wireframe-style prompts.

The goal is simple: **send pixels only when pixels are the best evidence**.

## Reality Check

Visual Context Router is a callable routing tool, not a global Codex screenshot interceptor.

- It can reduce token use when Codex calls `vcr_capture_route`, `vcr_route`, or `vcr_observe`.
- It cannot force Codex to use those tools for every built-in screenshot request.
- After installing the plugin, start a new Codex thread so the MCP tools are loaded.
- If the tools are not visible, run `python scripts/doctor.py` to check the local install.
- For repeated UI work, use `vcr_watch` so each observation is compared with the previous screen.

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

For local CLI/SDK use:

```bash
pip install -e .
```

Optional OCR and OpenCV support:

```bash
pip install -e ".[all]"
```

## Install As A Codex Plugin

Clone this repository, then run:

```bash
python scripts/install_codex_plugin.py
```

The installer copies the plugin into your local Codex plugin directory, writes the personal marketplace entry, installs Python dependencies, and tries to run:

```bash
codex plugin add visual-context-router@personal
```

After installing, start a new Codex thread and ask:

```text
Use Visual Context Router to inspect my screen with vcr_capture_route.
```

See [docs/codex-install.md](docs/codex-install.md) for manual installation and troubleshooting.
See [docs/prompts.md](docs/prompts.md) for copy-paste Codex prompts.

Check the local install:

```bash
python scripts/doctor.py
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

Watch the current screen with saved previous-frame state:

```bash
vcr watch --json
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
It also includes an MCP server that exposes tools Codex can call directly after the plugin is installed:

- `vcr_capture_route`: capture the current screen and return a low-token routing decision.
- `vcr_watch`: capture the current screen, compare it with the previous saved capture, and return a low-token routing decision.
- `vcr_route`: route an existing screenshot.
- `vcr_observe`: return a compact wireframe observation.
- `vcr_crop`: crop a normalized region of interest.

Example prompt:

```text
Use Visual Context Router to inspect my current screen with vcr_capture_route before deciding whether you need a full screenshot.
```

For repeated UI tasks:

```text
Use Visual Context Router with vcr_watch before each screen observation. Only ask for a full screenshot if the route strategy is full_image or ambiguous.
```

Important: the plugin gives Codex callable tools, but it does not globally intercept every built-in screenshot path. Ask Codex to use `vcr_capture_route` when you want the low-token route. If the current thread cannot see the tool, start a new Codex thread after installation.

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
