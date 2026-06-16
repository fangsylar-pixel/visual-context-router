from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from visual_context_router import observe, route_observation


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    cases = [
        {
            "name": "Sample dialog UI",
            "image": ROOT / "examples" / "sample-screen-after.png",
            "previous": ROOT / "examples" / "sample-screen.png",
        }
    ]
    results = []
    for case in cases:
        observation = observe(case["image"], previous_path=case["previous"])
        decision = route_observation(observation)
        estimate = decision.token_estimate
        results.append(
            {
                "name": case["name"],
                "resolution": f"{observation.image.width}x{observation.image.height}",
                "strategy": decision.strategy,
                "full_image_tokens": estimate.full_image_tokens,
                "routed_text_tokens": estimate.routed_text_tokens,
                "saved_tokens": estimate.saved_tokens,
                "savings_ratio": round(estimate.savings_ratio, 4),
            }
        )

    print(json.dumps({"benchmarks": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

