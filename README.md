# flutter-pixel-align

A reusable agent **skill** that turns "make the UI look the same" from a subjective feeling into a measurable engineering process. It is built for Flutter projects that need to align the current UI pixel-by-pixel against a reference (a competitor app, a Figma/design export, or a previously approved `golden` screenshot) and produce a quantitative acceptance report that can be re-verified on every change.

> Core rule of this skill: **no measurement, no "aligned".** Any "aligned / passed" conclusion must be backed by numbers or a diff image — never by "looks about the same".

## What it does

- Defines a **reference baseline** and a quantifiable alignment checklist (each item maps to a measurable metric).
- Guides **identical-condition screenshot capture** (same device, resolution, density, font scaling, light/dark mode) using deterministic golden tests when possible.
- Extracts **measurable metrics**: spacing/margins, colors (ΔE in CIELAB), font size/weight/line-height, component geometry (bounding box, corner radius, shadow), and overall pixel difference.
- Produces a **structured acceptance report** (PASS / WARN / FAIL per item with measured values and evidence).
- Drives **fix-and-regression**: re-run after edits to confirm failures reach zero and previously-passing items did not regress; then freeze the passing screenshot as the new golden.

## When to use

- "Align our UI with app X" / "pixel-perfect match" / "make it look like the reference app"
- "Compare against the design / screenshot and give me evidence of the differences"
- "Accept the UI" / "visual regression" / "freeze the UI before release"
- After a layout/theme change in a Flutter project, confirm there is no visual regression

## Repository layout

```
flutter-pixel-align/
├── SKILL.md                      # Skill definition: triggers + workflow + hard rules
├── references/
│   ├── metrics.md               # Measurable metric definitions & pass thresholds
│   ├── measurement-method.md    # Screenshot capture, golden tests, color/diff commands
│   └── report-template.md       # Per-item acceptance report template
├── scripts/
│   └── pixel_diff.py            # Quantitative pixel diff (MSE, max diff, ratio, diff image)
└── README.md
```

## Install

Copy the skill folder into your agent's skills directory. For example, with WorkBuddy / Claude-style skill loaders:

```bash
# into a project-scoped skills dir
cp -r flutter-pixel-align <project>/.workbuddy/skills/

# or a user-global skills dir
cp -r flutter-pixel-align ~/.workbuddy/skills/
```

The agent will pick it up automatically and trigger it when you ask for pixel-level UI alignment.

## Usage

1. **Set the baseline.** Tell the agent the reference source and the alignment scope (one page, a component, or the whole visual system). Agree on tolerance thresholds up front (e.g. spacing ±1px, ΔE ≤ 5).
2. **Capture identically.** Render fixed fixtures via golden tests, or take screenshots under identical conditions. Put `reference.png` and `current.png` in one folder.
3. **Run the diff script** (optional but recommended):

   ```bash
   pip install pillow
   python scripts/pixel_diff.py reference.png current.png \
       --threshold 16 --grid 4 --out diff.png
   ```

   Output: MSE, max per-pixel diff, differing-pixel ratio, per-region breakdown, and a highlighted `diff.png`. Exit code is `1` when the differing-pixel ratio exceeds `--fail-ratio` — useful as a CI / PR visual-regression gate.
4. **Fill the report.** Use `references/report-template.md` to record measured values and a number-based conclusion.
5. **Fix & re-verify.** After edits, re-run steps 2–4 until failures are zero and no prior PASS item regressed, then freeze with `flutter test --update-goldens`.

## Metric thresholds (defaults)

| Metric | Unit | Default pass |
|---|---|---|
| Spacing / margin | px | ≤1 PASS; ≤2 WARN; >2 FAIL |
| Color (ΔE, CIELAB) | ΔE | ≤2 PASS; ≤5 WARN; >5 FAIL |
| Font size | px | ≤0.5 PASS; ≤1 WARN; >1 FAIL |
| Bounding box (x,y,w,h) | px | ≤1 PASS; ≤2 WARN; >2 FAIL |
| Corner radius | px | ≤1 PASS; else WARN/FAIL |
| Shadow offset/blur | px,% | ≤1px / ≤5% PASS |
| Overall pixel diff | % | <0.1% PASS; <1% WARN; ≥1% FAIL |

Thresholds are adjustable per project and must be agreed before measurement.

## License

MIT — see [LICENSE](LICENSE).
