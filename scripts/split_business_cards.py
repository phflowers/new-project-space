"""Split the source photo of the four business cards / name badges into
four separate images.

Usage:
    python scripts/split_business_cards.py \
        persona/images/source/business_cards.jpg \
        persona/images/cropped/

The script looks for four card-like rectangular regions on a darker
background. If automatic detection fails (low contrast, glare,
overlap), pass --manual to crop using the boxes recorded in
`crop_boxes.json` next to the source image. That file is generated on
the first successful run so you can hand-tune it and re-run.

Requires Pillow and numpy:
    pip install pillow numpy
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

LABELS = ["usi", "cigna", "hines", "fountain_health"]


def detect_card_boxes(img: Image.Image) -> list[tuple[int, int, int, int]]:
    """Find four bright rectangular regions on a darker background.

    Returns boxes as (left, top, right, bottom) in pixel coords, ordered
    top-to-bottom then left-to-right so they map to LABELS in reading
    order on the source photo.
    """
    gray = ImageOps.grayscale(img)
    arr = np.asarray(gray)
    # Cards are light, wood is dark. Threshold above the median.
    thresh = max(150, int(np.median(arr)) + 25)
    mask = arr > thresh

    # Simple connected-components via flood fill on rows of True pixels.
    from scipy.ndimage import label, find_objects  # type: ignore

    labeled, n = label(mask)
    slices = find_objects(labeled)
    candidates = []
    h, w = arr.shape
    min_area = (h * w) * 0.01  # at least 1% of the frame
    for sl in slices:
        if sl is None:
            continue
        ys, xs = sl
        height = ys.stop - ys.start
        width = xs.stop - xs.start
        area = height * width
        if area < min_area:
            continue
        candidates.append((xs.start, ys.start, xs.stop, ys.stop))

    # Keep the four largest, then sort by (top, left).
    candidates.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    top4 = candidates[:4]
    top4.sort(key=lambda b: (b[1], b[0]))
    return top4


def load_manual_boxes(path: Path) -> list[tuple[int, int, int, int]] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [tuple(b) for b in data["boxes"]]


def save_manual_boxes(path: Path, boxes: list[tuple[int, int, int, int]]) -> None:
    path.write_text(
        json.dumps(
            {"labels": LABELS, "boxes": [list(b) for b in boxes]},
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to source photo")
    parser.add_argument("out_dir", type=Path, help="Directory for cropped images")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Use crop_boxes.json next to the source instead of auto-detection",
    )
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Source not found: {args.source}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    boxes_path = args.source.with_name("crop_boxes.json")

    img = Image.open(args.source).convert("RGB")
    if args.manual:
        boxes = load_manual_boxes(boxes_path)
        if boxes is None:
            print(f"No manual boxes at {boxes_path}", file=sys.stderr)
            return 2
    else:
        boxes = detect_card_boxes(img)
        if len(boxes) != 4:
            print(
                f"Auto-detect found {len(boxes)} regions, expected 4. "
                f"Edit {boxes_path} and re-run with --manual.",
                file=sys.stderr,
            )
            save_manual_boxes(boxes_path, boxes)
            return 3
        save_manual_boxes(boxes_path, boxes)

    for label, box in zip(LABELS, boxes):
        crop = img.crop(box)
        out = args.out_dir / f"{label}.jpg"
        crop.save(out, "JPEG", quality=92)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
