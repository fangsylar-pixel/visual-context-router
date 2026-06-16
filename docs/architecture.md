# Architecture

Visual Context Router is a pre-model layer for multimodal agents.

```text
Raw screen or frame
  -> change detector
  -> element extractor
  -> OCR adapter
  -> ROI selector
  -> compact observation
  -> model prompt
```

## Design Principles

- The cheapest image token is the one never sent.
- Preserve reliability before maximizing compression.
- Route evidence by task: text state for planning, ROI pixels for confirmation.
- Keep the first version local, inspectable, and easy to extend.

## Observation Schema

```json
{
  "changed": true,
  "change_score": 0.018,
  "image": {
    "width": 1440,
    "height": 900,
    "path": "current.png"
  },
  "elements": [],
  "ocr_text": [],
  "roi_suggestions": []
}
```

