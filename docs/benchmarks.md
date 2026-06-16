# Benchmarks

These numbers are estimates from Visual Context Router's local token estimator. They are meant to compare routing modes, not to exactly match a specific model provider's billing.

## Included Sample

Command:

```bash
python scripts/benchmark_examples.py
```

Result:

| Screen | Resolution | Strategy | Full image tokens | Routed text tokens | Saved tokens | Savings |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Sample dialog UI | 960x600 | `wireframe_plus_roi` | 768 | 65 | 703 | 91.5% |

## Live Codex Desktop Example

Observed during local testing with `vcr_capture_route`:

| Screen | Resolution | Strategy | Full image tokens | Routed text tokens | Saved tokens | Savings |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Codex desktop screen | 1920x1080 | `wireframe_plus_roi` | 2765 | 778 | 1987 | 71.9% |

## Interpreting Results

- `full_image_tokens` estimates the cost of sending the whole image.
- `routed_text_tokens` estimates the cost of sending the structured wireframe text.
- `wireframe_plus_roi` means the agent should reason from text first and request only local crops if needed.
- The safest workflow is to use a full screenshot for initial orientation, then use `vcr_watch` for repeated observations.
