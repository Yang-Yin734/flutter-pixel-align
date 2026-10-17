#!/usr/bin/env python3
"""Pixel-level diff for Flutter UI alignment verification.

Compares two screenshots taken under identical conditions and reports
quantitative differences (MSE, max per-pixel diff, differing-pixel ratio)
plus optional per-region breakdown and a highlighted diff image.

Usage:
    pip install pillow
    python pixel_diff.py reference.png current.png \
        --threshold 16 --grid 4 --out diff.png

Exit code is 0 when the differing-pixel ratio is below --fail-ratio,
otherwise 1 (useful as a CI/PR visual-regression gate).
"""
import argparse
import json
import sys

try:
    from PIL import Image
except ImportError:
    sys.stderr.write(
        "ERROR: Pillow is required. Install with: pip install pillow\n"
    )
    sys.exit(2)


def color_diff(a, b):
    """Sum of absolute channel differences for one pixel (0-765)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def main():
    ap = argparse.ArgumentParser(description="Pixel-level UI diff for Flutter alignment.")
    ap.add_argument("reference")
    ap.add_argument("current")
    ap.add_argument("--threshold", type=int, default=16,
                    help="Per-pixel channel-sum diff above this counts as 'differing' (0-765).")
    ap.add_argument("--grid", type=int, default=1,
                    help="Split image into NxN regions for per-region diff ratio.")
    ap.add_argument("--out", default="diff.png", help="Highlighted diff image path.")
    ap.add_argument("--fail-ratio", type=float, default=1.0,
                    help="Differing-pixel ratio (percent) above which exit code is 1.")
    args = ap.parse_args()

    ref = Image.open(args.reference).convert("RGB")
    cur = Image.open(args.current).convert("RGB")

    if ref.size != cur.size:
        sys.stderr.write(
            f"ERROR: size mismatch {ref.size} vs {cur.size}. "
            "Capture both shots under identical device/size/density.\n"
        )
        sys.exit(3)

    W, H = ref.size
    rp = ref.load()
    cp = cur.load()

    total = W * H
    diff_px = 0
    max_diff = 0
    sum_sq = 0
    # region accumulators: count + diff count
    regions = {}
    if args.grid > 1:
        rw, rh = W / args.grid, H / args.grid

    diff_img = Image.new("RGB", (W, H))
    dp = diff_img.load()

    for y in range(H):
        for x in range(W):
            a = rp[x, y]
            b = cp[x, y]
            d = color_diff(a, b)
            if d > 0:
                sum_sq += d * d
            if d > max_diff:
                max_diff = d
            if d > args.threshold:
                diff_px += 1
                dp[x, y] = (255, 0, 0)  # highlight differing pixels red
            else:
                # dim unchanged pixels for contrast
                dp[x, y] = (a[0] // 3, a[1] // 3, a[2] // 3)
            if args.grid > 1:
                gx = min(int(x // rw), args.grid - 1)
                gy = min(int(y // rh), args.grid - 1)
                key = (gx, gy)
                c, n = regions.get(key, (0, 0))
                regions[key] = (c + (1 if d > args.threshold else 0), n + 1)

    ratio = 100.0 * diff_px / total
    mse = sum_sq / total
    summary = {
        "reference": args.reference,
        "current": args.current,
        "size": list(ref.size),
        "threshold": args.threshold,
        "differing_pixels": diff_px,
        "differing_pixel_ratio_pct": round(ratio, 4),
        "mse": round(mse, 3),
        "max_pixel_diff": max_diff,
    }
    if args.grid > 1:
        summary["regions"] = {
            f"{gx}-{gy}": round(100.0 * c / n, 4)
            for (gx, gy), (c, n) in sorted(regions.items())
        }

    diff_img.save(args.out)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"diff image written to: {args.out}")

    sys.exit(1 if ratio > args.fail_ratio else 0)


if __name__ == "__main__":
    main()
