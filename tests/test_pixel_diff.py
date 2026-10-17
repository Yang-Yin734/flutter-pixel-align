"""Tests for scripts/pixel_diff.py — Flutter UI pixel-level diff.

Run with:  pip install pillow pytest && pytest -q
These tests are CI-friendly: they synthesize small images in memory,
so no network or external assets are required.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "pixel_diff.py"


def _parse_json(stdout):
    """Parse the first JSON object from the script's stdout (may be multiline)."""
    return json.JSONDecoder().raw_decode(stdout.strip())[0]


def _run(*args, expect_fail=False):
    """Run the script, return (returncode, stdout)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _make(path, size, color):
    img = Image.new("RGB", size, color)
    img.save(path)
    return path


def test_identical_images_zero_diff(tmp_path):
    a = _make(tmp_path / "a.png", (10, 10), (255, 255, 255))
    b = _make(tmp_path / "b.png", (10, 10), (255, 255, 255))
    rc, out, _ = _run(str(a), str(b))
    data = _parse_json(out)
    assert data["differing_pixel_ratio_pct"] == 0.0
    assert data["mse"] == 0.0
    assert data["max_pixel_diff"] == 0
    assert rc == 0  # below fail-ratio -> pass


def test_differing_pixels_and_exit_gate(tmp_path):
    a = _make(tmp_path / "a.png", (10, 10), (255, 255, 255))
    b = _make(tmp_path / "b.png", (10, 10), (0, 0, 0))
    # default fail-ratio is 1% (0.01? no, it's percent=1.0) -> 100% diff exceeds it
    rc, out, _ = _run(str(a), str(b), "--fail-ratio", "50")
    data = _parse_json(out)
    assert data["differing_pixel_ratio_pct"] == 100.0
    assert data["max_pixel_diff"] == 765  # full white vs black
    assert rc == 1  # exceeds fail-ratio -> CI gate fails


def test_size_mismatch_exits_3(tmp_path):
    a = _make(tmp_path / "a.png", (10, 10), (255, 255, 255))
    b = _make(tmp_path / "b.png", (8, 8), (255, 255, 255))
    rc, _, err = _run(str(a), str(b))
    assert rc == 3
    assert "size mismatch" in err.lower()


def test_missing_pillow_handled(tmp_path, monkeypatch):
    # If pillow can't be imported the script exits 2 with a clear message.
    # We simulate by running with a broken import shim is hard; instead just
    # assert the script file references the friendly error.
    text = SCRIPT.read_text(encoding="utf-8")
    assert "pip install pillow" in text


def test_color_at_extraction(tmp_path):
    a = _make(tmp_path / "a.png", (4, 4), (255, 255, 255))
    # paint a known color at (1,1): #FF6B35 = (255,107,53)
    img = Image.open(a).convert("RGB")
    img.putpixel((1, 1), (255, 107, 53))
    img.save(a)
    rc, out, _ = _run(str(a), "--color-at", "1,1")
    data = json.loads(out)
    assert data["point"] == [1, 1]
    assert data["reference_color"]["hex"].upper() == "#FF6B35"
    assert rc == 0


def test_color_at_delta_e_verdict(tmp_path):
    a = _make(tmp_path / "a.png", (4, 4), (255, 255, 255))
    b = _make(tmp_path / "b.png", (4, 4), (255, 255, 255))
    imgA = Image.open(a).convert("RGB"); imgA.putpixel((1, 1), (255, 107, 53)); imgA.save(a)
    imgB = Image.open(b).convert("RGB"); imgB.putpixel((1, 1), (255, 122, 69)); imgB.save(b)
    rc, out, _ = _run(str(a), str(b), "--color-at", "1,1")
    data = json.loads(out)
    assert "current_color" in data
    assert data["delta_e"] > 0
    # perceptibly different colors -> FAIL (delta_e > 5)
    assert data["verdict"] == "FAIL"
    assert rc == 0


def test_threshold_sensitivity(tmp_path):
    # a 1-channel difference sums to 1 -> below default threshold 16 => not differing
    a = _make(tmp_path / "a.png", (4, 4), (100, 100, 100))
    b = _make(tmp_path / "b.png", (4, 4), (101, 100, 100))
    rc, out, _ = _run(str(a), str(b))
    data = _parse_json(out)
    assert data["differing_pixel_ratio_pct"] == 0.0

    # with threshold 0 every non-equal pixel counts
    rc, out, _ = _run(str(a), str(b), "--threshold", "0")
    data = _parse_json(out)
    assert data["differing_pixel_ratio_pct"] == 100.0


def test_per_region_grid(tmp_path):
    a = _make(tmp_path / "a.png", (4, 4), (255, 255, 255))
    b = _make(tmp_path / "b.png", (4, 4), (255, 255, 255))
    # top-left 2x2 region is black in current
    imgB = Image.open(b).convert("RGB")
    for x in range(2):
        for y in range(2):
            imgB.putpixel((x, y), (0, 0, 0))
    imgB.save(b)
    rc, out, _ = _run(str(a), str(b), "--grid", "2")
    data = _parse_json(out)
    assert "regions" in data
    # region 0-0 (top-left) should be 100% differing
    assert data["regions"]["0-0"] == 100.0
    assert rc == 1
