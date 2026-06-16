from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps


@dataclass(frozen=True)
class ImageInfo:
    width: int
    height: int
    path: str


@dataclass(frozen=True)
class UIElement:
    id: int
    type: str
    text: str
    bbox: tuple[float, float, float, float]
    confidence: float = 0.0

    def to_line(self) -> str:
        x1, y1, x2, y2 = self.bbox
        label = f' "{self.text}"' if self.text else ""
        type_label = self.type.replace("_or_", "/").replace("_", " ").title().replace(" ", "")
        return (
            f"{type_label}[{self.id}]{label} "
            f"bbox=({x1:.3f},{y1:.3f},{x2:.3f},{y2:.3f}) "
            f"conf={self.confidence:.2f}"
        )


@dataclass(frozen=True)
class TokenEstimate:
    full_image_tokens: int
    routed_text_tokens: int
    saved_tokens: int
    savings_ratio: float


@dataclass(frozen=True)
class RouteDecision:
    strategy: str
    reason: str
    model_payload: str
    include_full_image: bool
    include_wireframe: bool
    roi_bboxes: list[tuple[float, float, float, float]]
    token_estimate: TokenEstimate


@dataclass(frozen=True)
class Observation:
    image: ImageInfo
    changed: bool
    change_score: Optional[float]
    elements: list[UIElement] = field(default_factory=list)
    ocr_text: list[str] = field(default_factory=list)
    roi_suggestions: list[tuple[float, float, float, float]] = field(default_factory=list)

    def to_dict(
        self,
        include_wireframe: bool = True,
        include_token_estimate: bool = False,
        include_route: bool = False,
    ) -> dict:
        data = asdict(self)
        if include_wireframe:
            data["wireframe"] = self.to_wireframe()
        if include_token_estimate:
            data["token_estimate"] = asdict(estimate_tokens(self))
        if include_route:
            data["route"] = asdict(route_observation(self))
        return data

    def to_wireframe(self, max_elements: int = 80) -> str:
        changed = "unknown" if self.change_score is None else ("yes" if self.changed else "no")
        lines = [
            f"Screen {self.image.width}x{self.image.height}.",
            f"Changed: {changed}.",
        ]
        if self.change_score is not None:
            lines.append(f"Change score: {self.change_score:.4f}.")
        if self.ocr_text:
            lines.append("OCR text:")
            lines.extend(f"- {text}" for text in self.ocr_text[:30])
        if self.elements:
            lines.append("Detected UI regions:")
            lines.extend(element.to_line() for element in self.elements[:max_elements])
        if self.roi_suggestions:
            lines.append("Suggested ROI crops:")
            lines.extend(
                f"- bbox=({x1:.3f},{y1:.3f},{x2:.3f},{y2:.3f})"
                for x1, y1, x2, y2 in self.roi_suggestions[:10]
            )
        return "\n".join(lines)


def observe(
    image_path: str | Path,
    previous_path: str | Path | None = None,
    change_threshold: float = 0.003,
    detect_elements: bool = True,
    ocr: bool = False,
) -> Observation:
    image_path = Path(image_path)
    image = Image.open(image_path).convert("RGB")
    image_info = ImageInfo(width=image.width, height=image.height, path=str(image_path))

    change_score = None
    changed = True
    if previous_path:
        previous = Image.open(previous_path).convert("RGB")
        change_score = image_change_score(previous, image)
        changed = change_score >= change_threshold

    elements = find_ui_regions(image) if detect_elements else []
    ocr_text = read_ocr_text(image) if ocr else []
    roi_suggestions = suggest_rois(elements, change_score=change_score)

    return Observation(
        image=image_info,
        changed=changed,
        change_score=change_score,
        elements=elements,
        ocr_text=ocr_text,
        roi_suggestions=roi_suggestions,
    )


def image_change_score(previous: Image.Image, current: Image.Image, size: tuple[int, int] = (256, 256)) -> float:
    previous_small = ImageOps.grayscale(previous.resize(size))
    current_small = ImageOps.grayscale(current.resize(size))
    diff = ImageChops.difference(previous_small, current_small)
    arr = np.asarray(diff, dtype=np.float32) / 255.0
    return float(np.mean(arr * arr))


def find_ui_regions(image: Image.Image, max_regions: int = 80) -> list[UIElement]:
    cv_regions = _find_regions_with_cv(image, max_regions=max_regions)
    if cv_regions:
        return cv_regions
    return _find_regions_with_pillow(image, max_regions=max_regions)


def _find_regions_with_cv(image: Image.Image, max_regions: int) -> list[UIElement]:
    try:
        import cv2  # type: ignore
    except Exception:
        return []

    width, height = image.size
    gray = np.asarray(ImageOps.grayscale(image))
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 40, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes: list[tuple[int, int, int, int, float]] = []
    image_area = width * height
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < image_area * 0.0004 or area > image_area * 0.35:
            continue
        if w < 12 or h < 10:
            continue
        boxes.append((x, y, x + w, y + h, min(0.95, area / image_area * 8)))

    return _boxes_to_elements(_dedupe_boxes(boxes), width, height, max_regions)


def _find_regions_with_pillow(image: Image.Image, max_regions: int) -> list[UIElement]:
    width, height = image.size
    gray = ImageOps.grayscale(image).filter(ImageFilter.FIND_EDGES)
    arr = np.asarray(gray, dtype=np.uint8)
    threshold = max(24, int(arr.mean() + arr.std()))
    mask = arr > threshold

    visited = np.zeros(mask.shape, dtype=bool)
    boxes: list[tuple[int, int, int, int, float]] = []
    image_area = width * height

    for y in range(0, height, 4):
        for x in range(0, width, 4):
            if not mask[y, x] or visited[y, x]:
                continue
            box = _flood_box(mask, visited, x, y, step=4)
            if not box:
                continue
            x1, y1, x2, y2 = box
            area = max(1, (x2 - x1) * (y2 - y1))
            if image_area * 0.0006 <= area <= image_area * 0.25:
                boxes.append((x1, y1, x2, y2, min(0.70, area / image_area * 10)))
    return _boxes_to_elements(_dedupe_boxes(boxes), width, height, max_regions)


def _flood_box(
    mask: np.ndarray,
    visited: np.ndarray,
    start_x: int,
    start_y: int,
    step: int = 4,
) -> tuple[int, int, int, int] | None:
    height, width = mask.shape
    stack = [(start_x, start_y)]
    visited[start_y, start_x] = True
    xs: list[int] = []
    ys: list[int] = []
    while stack and len(xs) < 3000:
        x, y = stack.pop()
        xs.append(x)
        ys.append(y)
        for nx, ny in ((x + step, y), (x - step, y), (x, y + step), (x, y - step)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            if visited[ny, nx] or not mask[ny, nx]:
                continue
            visited[ny, nx] = True
            stack.append((nx, ny))
    if len(xs) < 4:
        return None
    return max(0, min(xs) - step), max(0, min(ys) - step), min(width, max(xs) + step), min(height, max(ys) + step)


def _dedupe_boxes(boxes: Iterable[tuple[int, int, int, int, float]]) -> list[tuple[int, int, int, int, float]]:
    sorted_boxes = sorted(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]), reverse=True)
    kept: list[tuple[int, int, int, int, float]] = []
    for box in sorted_boxes:
        if all(_iou(box, existing) < 0.55 for existing in kept):
            kept.append(box)
    return kept


def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, ax2, ay2 = a[:4]
    bx1, by1, bx2, by2 = b[:4]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = max(1.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1.0, (bx2 - bx1) * (by2 - by1))
    return intersection / (area_a + area_b - intersection)


def _boxes_to_elements(
    boxes: list[tuple[int, int, int, int, float]],
    width: int,
    height: int,
    max_regions: int,
) -> list[UIElement]:
    elements = []
    for idx, (x1, y1, x2, y2, confidence) in enumerate(boxes[:max_regions], start=1):
        element_type = _classify_box(x1, y1, x2, y2, width, height)
        elements.append(
            UIElement(
                id=idx,
                type=element_type,
                text="",
                bbox=(x1 / width, y1 / height, x2 / width, y2 / height),
                confidence=float(confidence),
            )
        )
    return elements


def _classify_box(x1: int, y1: int, x2: int, y2: int, width: int, height: int) -> str:
    box_width = max(1, x2 - x1)
    box_height = max(1, y2 - y1)
    aspect = box_width / box_height
    area_ratio = (box_width * box_height) / max(1, width * height)

    if 2.0 <= aspect <= 12.0 and 0.001 <= area_ratio <= 0.035 and box_height <= height * 0.12:
        return "button_or_input"
    if area_ratio >= 0.08:
        return "panel"
    if aspect >= 6.0 and box_height <= height * 0.10:
        return "toolbar_or_textline"
    return "region"


def read_ocr_text(image: Image.Image) -> list[str]:
    try:
        import pytesseract  # type: ignore
    except Exception:
        return []
    raw = pytesseract.image_to_string(image)
    return [line.strip() for line in raw.splitlines() if line.strip()]


def suggest_rois(
    elements: Sequence[UIElement],
    change_score: Optional[float],
    max_rois: int = 5,
) -> list[tuple[float, float, float, float]]:
    if not elements or change_score == 0:
        return []
    return [element.bbox for element in sorted(elements, key=lambda item: item.confidence, reverse=True)[:max_rois]]


def crop_roi(
    image_path: str | Path,
    bbox: Sequence[float],
    out_path: str | Path,
    padding: float = 0.0,
) -> Path:
    image_path = Path(image_path)
    out_path = Path(out_path)
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    x1, y1, x2, y2 = _expand_bbox(bbox, padding)
    crop_box = (
        max(0, int(x1 * width)),
        max(0, int(y1 * height)),
        min(width, int(x2 * width)),
        min(height, int(y2 * height)),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.crop(crop_box).save(out_path)
    return out_path


def _expand_bbox(bbox: Sequence[float], padding: float) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = [float(value) for value in bbox]
    return (
        max(0.0, x1 - padding),
        max(0.0, y1 - padding),
        min(1.0, x2 + padding),
        min(1.0, y2 + padding),
    )


def estimate_tokens(observation: Observation) -> TokenEstimate:
    pixels = observation.image.width * observation.image.height
    full_image_tokens = max(85, round(pixels / 750))
    routed_chars = len(observation.to_wireframe())
    routed_text_tokens = max(1, round(routed_chars / 4))
    saved = max(0, full_image_tokens - routed_text_tokens)
    ratio = saved / full_image_tokens if full_image_tokens else 0.0
    return TokenEstimate(
        full_image_tokens=full_image_tokens,
        routed_text_tokens=routed_text_tokens,
        saved_tokens=saved,
        savings_ratio=ratio,
    )


def route_observation(
    observation: Observation,
    full_image_threshold: float = 0.08,
    roi_threshold: float = 0.003,
) -> RouteDecision:
    token_estimate = estimate_tokens(observation)

    if observation.change_score is not None and not observation.changed:
        return RouteDecision(
            strategy="skip",
            reason="Screen change is below threshold; continue from action log or cached state.",
            model_payload="No meaningful visual change detected. Continue from the previous state.",
            include_full_image=False,
            include_wireframe=False,
            roi_bboxes=[],
            token_estimate=token_estimate,
        )

    if observation.change_score is not None and observation.change_score >= full_image_threshold:
        return RouteDecision(
            strategy="full_image",
            reason="Large visual change detected; send a full screenshot for global reorientation.",
            model_payload=observation.to_wireframe(max_elements=20),
            include_full_image=True,
            include_wireframe=True,
            roi_bboxes=[],
            token_estimate=token_estimate,
        )

    if observation.roi_suggestions and (
        observation.change_score is None or observation.change_score >= roi_threshold
    ):
        return RouteDecision(
            strategy="wireframe_plus_roi",
            reason="Localized visual change detected; send compact wireframe and suggested ROI crops.",
            model_payload=observation.to_wireframe(max_elements=20),
            include_full_image=False,
            include_wireframe=True,
            roi_bboxes=observation.roi_suggestions[:3],
            token_estimate=token_estimate,
        )

    return RouteDecision(
        strategy="wireframe_only",
        reason="Use structured visual state without image pixels.",
        model_payload=observation.to_wireframe(max_elements=60),
        include_full_image=False,
        include_wireframe=True,
        roi_bboxes=[],
        token_estimate=token_estimate,
    )
