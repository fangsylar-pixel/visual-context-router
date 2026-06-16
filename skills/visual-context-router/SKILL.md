---
name: visual-context-router
description: Use when Codex needs to inspect screenshots, UI captures, browser images, or desktop automation state while minimizing visual token usage through screenshot diffing, wireframe prompts, and region-of-interest crops.
---

# Visual Context Router

Use this skill when a task involves image or screen understanding and the user cares about token cost, speed, or repeated UI observations.

## Workflow

1. Prefer structured state over full screenshots.
2. Run `vcr observe <image>` to create a compact wireframe prompt.
3. When a previous screenshot exists, run `vcr observe <image> --previous <previous>` and skip image analysis if `changed` is false.
4. Use `vcr crop <image> --bbox x1,y1,x2,y2 --out roi.png` when the next model step only needs a local region.
5. Include the wireframe text and only the needed ROI image in the model context.

## Commands

```bash
vcr observe current.png --previous previous.png --json --token-budget
vcr crop current.png --bbox 0.70,0.05,0.98,0.30 --out roi.png
```

## Agent Guidance

- Use the full screenshot for initial global orientation.
- Use wireframe output for repeated state tracking.
- Use ROI crops for confirmation, small text, dialogs, menus, and ambiguous icons.
- Request a fresh screenshot when the action log and visual state disagree.

