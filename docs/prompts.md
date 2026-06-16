# Prompt Recipes

Use these prompts in a new Codex thread after installing the plugin.

## Quick Screen Check

```text
[@visual-context-router](plugin://visual-context-router@personal) Low-token inspect my current screen.
Use vcr_capture_route first. Tell me only the strategy, savings_ratio, and what you can infer.
```

## Repeated Screen Work

```text
[@visual-context-router](plugin://visual-context-router@personal) For this task, use vcr_watch before every screen observation.
Only request a full screenshot if the route strategy is full_image or the wireframe is ambiguous.
```

## UI Automation

```text
[@visual-context-router](plugin://visual-context-router@personal) Use vcr_watch to track screen changes.
If the strategy is wireframe_plus_roi, reason from the wireframe first and crop only the needed ROI.
```

## Debug Token Savings

```text
[@visual-context-router](plugin://visual-context-router@personal) Call vcr_capture_route and report:
strategy, full_image_tokens, routed_text_tokens, saved_tokens, savings_ratio.
```

