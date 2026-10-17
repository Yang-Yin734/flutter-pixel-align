#!/usr/bin/env python3
"""Pixel-level diff for Flutter UI alignment verification.

Compares two screenshots taken under identical conditions and reports
quantitative differences (MSE, max per-pixel diff, differing-pixel ratio)
plus optional per-region breakdown and a highlighted diff image.

It can also extract the exact color at a coordinate (--color-at) and report
the CIE76 ΔE against the current screenshot, which directly supports the
"measure the color difference, don't guess" workflow.

Usage:
    pip install pillow
    python pixel_diff.py reference.png current.png \
        --threshold 16 --grid 4 --out diff.png
    python pixel_diff.py reference.png current.png --color-at 40,40

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


def rgb_to_lab(rgb):
    """sRGB (0-255) -> CIE L*a*b* (D65)."""
    r, g, b = [c / 255.0 for c in rgb]
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    xn, yn, zn = 0.95047, 1.0, 1.08883
    x, y, z = x / xn, y / yn, z / zn
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e(lab1, lab2):
    """CIE76 color difference between two L*a*b* triples."""
    dl, da, db = lab1[0] - lab2[0], lab1[1] - lab2[1], lab1[2] - lab2[2]
    return (dl * dl + da * da + db * db) ** 0.5


def hex_of(rgb):
    return "#" + "".join(f"{c:02X}" for c in rgb)


def main():
    ap = argparse.ArgumentParser(description="Pixel-level UI diff for Flutter alignment.")
    ap.add_argument("reference")
    ap.add_argument("current", nargs="?", default=None,
                    help="Current screenshot. Required unless using --color-at.")
    ap.add_argument("--threshold", type=int, default=16,
                    help="Per-pixel channel-sum diff above this counts as 'differing' (0-765).")
    ap.add_argument("--grid", type=int, default=1,
                    help="Split image into NxN regions for per-region diff ratio.")
    ap.add_argument("--out", default="diff.png", help="Highlighted diff image path.")
    ap.add_argument("--fail-ratio", type=float, default=1.0,
                    help="Differing-pixel ratio (percent) above which exit code is 1.")
    ap.add_argument("--color-at", metavar="X,Y", default=None,
                    help="Print color at pixel (X,Y) of reference (and current) plus ΔE.")
    args = ap.parse_args()

    ref = Image.open(args.reference).convert("RGB")

    # --- color-at mode ---------------------------------------------------
    if args.color_at:
        try:
            x, y = (int(v) for v in args.color_at.split(","))
        except ValueError:
            sys.stderr.write("ERROR: --color-at expects X,Y (e.g. 40,40)\n")
            sys.exit(2)
        W, H = ref.size
        if not (0 <= x < W and 0 <= y < H):
            sys.stderr.write(f"ERROR: coordinate ({x},{y}) out of range {ref.size}\n")
            sys.exit(2)
        rc = ref.getpixel((x, y))
        out = {
            "reference": args.reference,
            "point": [x, y],
            "reference_color": {"rgb": list(rc), "hex": hex_of(rc)},
        }
        if args.current:
            cur = Image.open(args.current).convert("RGB")
            if cur.size != ref.size:
                sys.stderr.write("ERROR: size mismatch for color-at comparison\n")
                sys.exit(3)
            cc = cur.getpixel((x, y))
            out["current_color"] = {"rgb": list(cc), "hex": hex_of(cc)}
            de = delta_e(rgb_to_lab(rc), rgb_to_lab(cc))
            out["delta_e"] = round(de, 3)
            out["verdict"] = "PASS" if de <= 2 else ("WARN" if de <= 5 else "FAIL")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(0)

    if not args.current:
        sys.stderr.write("ERROR: 'current' image is required unless using --color-at\n")
        sys.exit(2)

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
                dp[x, y] = (a[0] // 3, a[1] // 3, a[2] // 3)  # dim unchanged
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
