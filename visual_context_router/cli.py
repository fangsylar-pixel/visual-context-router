from __future__ import annotations

import argparse
import json
from pathlib import Path

from dataclasses import asdict
from PIL import ImageGrab

from .core import crop_roi, observe, route_observation


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="vcr",
        description="Token-aware visual context router for screenshots and UI agents.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    observe_parser = subparsers.add_parser("observe", help="Analyze a screenshot.")
    observe_parser.add_argument("image", help="Current screenshot path.")
    observe_parser.add_argument("--previous", help="Previous screenshot path.")
    observe_parser.add_argument("--threshold", type=float, default=0.003, help="Change threshold.")
    observe_parser.add_argument("--no-elements", action="store_true", help="Skip UI region detection.")
    observe_parser.add_argument("--ocr", action="store_true", help="Use pytesseract OCR if available.")
    observe_parser.add_argument("--json", action="store_true", help="Print JSON instead of wireframe text.")
    observe_parser.add_argument("--token-budget", action="store_true", help="Include token estimate.")
    observe_parser.add_argument("--route", action="store_true", help="Include routing decision.")
    observe_parser.set_defaults(func=_observe_command)

    route_parser = subparsers.add_parser("route", help="Decide what visual context an agent should send.")
    route_parser.add_argument("image", help="Current screenshot path.")
    route_parser.add_argument("--previous", help="Previous screenshot path.")
    route_parser.add_argument("--threshold", type=float, default=0.003, help="Change threshold.")
    route_parser.add_argument("--ocr", action="store_true", help="Use pytesseract OCR if available.")
    route_parser.add_argument("--json", action="store_true", help="Print JSON route decision.")
    route_parser.set_defaults(func=_route_command)

    watch_parser = subparsers.add_parser(
        "watch",
        help="Capture the current screen, compare with the previous capture, and route it.",
    )
    watch_parser.add_argument("--state-dir", default=".vcr", help="Directory for saved screen state.")
    watch_parser.add_argument("--threshold", type=float, default=0.003, help="Change threshold.")
    watch_parser.add_argument("--ocr", action="store_true", help="Use pytesseract OCR if available.")
    watch_parser.add_argument("--json", action="store_true", help="Print JSON route decision.")
    watch_parser.set_defaults(func=_watch_command)

    crop_parser = subparsers.add_parser("crop", help="Crop a normalized region of interest.")
    crop_parser.add_argument("image", help="Screenshot path.")
    crop_parser.add_argument("--bbox", required=True, help="Normalized bbox: x1,y1,x2,y2")
    crop_parser.add_argument("--out", required=True, help="Output image path.")
    crop_parser.add_argument("--padding", type=float, default=0.0, help="Normalized bbox padding.")
    crop_parser.set_defaults(func=_crop_command)

    args = parser.parse_args()
    return args.func(args)


def _observe_command(args: argparse.Namespace) -> int:
    observation = observe(
        image_path=args.image,
        previous_path=args.previous,
        change_threshold=args.threshold,
        detect_elements=not args.no_elements,
        ocr=args.ocr,
    )
    if args.json:
        print(
            json.dumps(
                observation.to_dict(
                    include_token_estimate=args.token_budget,
                    include_route=args.route,
                ),
                indent=2,
            )
        )
    else:
        print(observation.to_wireframe())
        if args.token_budget:
            estimate = observation.to_dict(include_wireframe=False, include_token_estimate=True)[
                "token_estimate"
            ]
            print()
            print(
                "Token estimate: "
                f"full_image={estimate['full_image_tokens']} "
                f"routed_text={estimate['routed_text_tokens']} "
                f"saved={estimate['saved_tokens']} "
                f"savings={estimate['savings_ratio']:.1%}"
            )
    return 0


def _route_command(args: argparse.Namespace) -> int:
    observation = observe(
        image_path=args.image,
        previous_path=args.previous,
        change_threshold=args.threshold,
        ocr=args.ocr,
    )
    decision = route_observation(observation)
    if args.json:
        print(json.dumps(asdict(decision), indent=2))
    else:
        print(f"Strategy: {decision.strategy}")
        print(f"Reason: {decision.reason}")
        print(
            "Token estimate: "
            f"full_image={decision.token_estimate.full_image_tokens} "
            f"routed_text={decision.token_estimate.routed_text_tokens} "
            f"saved={decision.token_estimate.saved_tokens} "
            f"savings={decision.token_estimate.savings_ratio:.1%}"
        )
        if decision.roi_bboxes:
            print("ROI bboxes:")
            for bbox in decision.roi_bboxes:
                print("- " + ",".join(f"{value:.4f}" for value in bbox))
    return 0


def _watch_command(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    previous = state_dir / "previous-screen.png"
    current = state_dir / "current-screen.png"

    image = ImageGrab.grab()
    image.save(current)

    observation = observe(
        image_path=current,
        previous_path=previous if previous.exists() else None,
        change_threshold=args.threshold,
        ocr=args.ocr,
    )
    decision = route_observation(observation)
    current.replace(previous)

    payload = asdict(decision)
    payload["captured_path"] = str(previous)
    payload["used_previous"] = observation.change_score is not None

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Strategy: {decision.strategy}")
        print(f"Reason: {decision.reason}")
        print(f"Used previous: {payload['used_previous']}")
        print(
            "Token estimate: "
            f"full_image={decision.token_estimate.full_image_tokens} "
            f"routed_text={decision.token_estimate.routed_text_tokens} "
            f"saved={decision.token_estimate.saved_tokens} "
            f"savings={decision.token_estimate.savings_ratio:.1%}"
        )
    return 0


def _crop_command(args: argparse.Namespace) -> int:
    bbox = [float(part.strip()) for part in args.bbox.split(",")]
    if len(bbox) != 4:
        raise SystemExit("--bbox must contain exactly four comma-separated numbers")
    out = crop_roi(args.image, bbox=bbox, out_path=Path(args.out), padding=args.padding)
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
