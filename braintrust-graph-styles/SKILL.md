---
name: braintrust-graph-styles
description: Apply Braintrust brand colors, typography, and styling when generating or editing matplotlib/seaborn graphs. Use when asked to create, restyle, or audit any data visualization for Braintrust content.
---

When generating or editing any Braintrust graph, apply all guidelines below. These are non-negotiable defaults — not suggestions. If asked to restyle existing graphs, audit for off-brand colors first, then apply the palette.

---

## Brand palette

These are the only colors permitted in Braintrust graphs. Always use the named constants, never raw hex literals.

```python
BT_BLUE        = "#2C1FEB"   # primary bars, bubbles, main data series
BT_BLUE_ACCENT = "#3A77EB"   # secondary bars, gradient mid-point
BT_BLACK       = "#000000"   # titles, primary text
BT_CONCRETE    = "#504F4F"   # axis labels, secondary text, tick labels
BT_ICE_GREY    = "#D8DEEE"   # thin/de-emphasized bars, gridlines, axis borders
BT_LIME        = "#CCFF00"   # positive highlights on dark backgrounds
BT_GREEN       = "#14382D"   # RELIABLE labels, success call-outs (dark)
BT_PINK        = "#F5AFD1"   # diamond markers, accent on white backgrounds
BT_ROSE        = "#651D31"   # ERRATIC labels, warning call-outs, low-success bars
BT_WHITE       = "#FFFFFF"   # backgrounds only
```

### Color pairings (use together, not in isolation)
- **BT Blue + BT Blue Accent** — primary data pair (main bars + gradient)
- **BT Black + BT Concrete** — text pair (titles + secondary labels)
- **BT Lime + BT Green** — positive/success pair (bright accent + dark support)
- **BT Pink + BT Rose** — warning/negative pair (soft accent + dark support)
- **BT Ice Grey** — always used alone for de-emphasis

### Colormaps

```python
from matplotlib.colors import LinearSegmentedColormap

# General gradient (de-emphasized → primary): use for success-rate-mapped bars/bubbles
BT_CMAP = LinearSegmentedColormap.from_list("bt_blue", [BT_ICE_GREY, BT_BLUE_ACCENT, BT_BLUE])

# Heatmap gradient: use wherever RdYlGn or similar was used
BT_HEAT = LinearSegmentedColormap.from_list("bt_heat", [BT_ICE_GREY, BT_BLUE_ACCENT, BT_BLUE])

# Success-rate bar coloring (low → high): use when bar color encodes success rate
BT_SUCC = LinearSegmentedColormap.from_list("bt_succ", [BT_ROSE, BT_PINK, BT_BLUE_ACCENT, BT_BLUE])

# Diverging scale for SIGNED deltas vs. a baseline (cost ratio vs. 1.0, score change
# vs. a reference run, etc.): rose = below baseline, ice grey = ~zero, blue = above.
# Set vmin/vmax symmetrically (e.g. vmin=-x, vmax=x) so the ice-grey midpoint lands on
# the true zero/baseline value.
BT_DIVERGING = LinearSegmentedColormap.from_list(
    "bt_diverging", [BT_ROSE, BT_PINK, BT_ICE_GREY, BT_BLUE_ACCENT, BT_BLUE]
)
```

Only ever build colormaps out of the named constants above. Do not introduce a new
color (e.g. a purple, an orange, a different pink hex) even if it seems visually
useful — every BT color in this file is the designer-confirmed hex; anything else is
unverified and must not ship. If you're tempted to add a color, check with the
designer/source first rather than approximating one.

---

## Typography

- Brand typeface: **Braintrust Display V2** for titles/subtitles when the font is
  installed locally. Never bundle font files in a repo or generated artifact.
- Portable fallback stack when the brand font isn't available: **Helvetica Neue →
  Arial → Inter → DejaVu Sans**.
- Point sizes:
  - Title: 14pt, bold
  - Subtitle: 9pt, `BT_CONCRETE`
  - Axis labels: 10.5pt, `BT_CONCRETE`
  - Tick labels: 9.5pt, `BT_CONCRETE`
  - Legend: 9pt; legend title: 9.5pt
  - In-chart value labels / annotations: 8.5–10.5pt, bold for primary values,
    `BT_CONCRETE` for secondary ones
- `use_braintrust_theme()` (see module below) applies this automatically, including
  font-fallback detection — you don't need to set fonts manually per chart.

---

## Importable module — `bt_viz.py`

Don't paste the theme/palette/helpers inline into every script. Use the bundled
`scripts/bt_viz.py` (copy it into the target project's `scripts/` directory if it
isn't already there) as the single source of truth, and import from it:

```python
import sys
sys.path.insert(0, "scripts")
from bt_viz import (
    BT_BLUE, BT_BLUE_ACCENT, BT_BLACK, BT_CONCRETE, BT_ICE_GREY, BT_LIME,
    BT_GREEN, BT_PINK, BT_ROSE, BT_WHITE,
    BT_CMAP, BT_HEAT, BT_SUCC, BT_DIVERGING, ANNOT,
    use_braintrust_theme, titled, fig_title, repel_labels, key_box,
)

use_braintrust_theme()   # applies palette-aware rcParams + font fallback stack
```

If a local Braintrust Display V2 install is available, pass its directory:
`use_braintrust_theme(font_dir="/path/to/local/fonts")` — this registers the font
without ever bundling the font files themselves.

`bt_viz.py` contains:
- All `BT_*` color constants and colormaps (`BT_CMAP`, `BT_HEAT`, `BT_SUCC`,
  `BT_DIVERGING`) from the sections above
- `FONT_SIZES` dict + the font-fallback logic backing the typography spec above
- `use_braintrust_theme(font_dir=None)` — applies the full rcParams block
- `titled(ax, main, sub=None, pad=22)` — left-aligned bold title + optional subtitle
- `fig_title(fig, main, sub=None)` — figure-level title/subtitle above `tight_layout`
- `key_box(target, lines, loc="upper right", fontsize=8)` — a boxed, legend-styled
  key for chart facts that aren't a color/size mapping (a symbol definition like
  "gap = best − worst harness", a notation key like "bar = success ±Wilson 95% CI").
  Use this instead of putting that text in a plain subtitle — it should look like a
  legend, not floating prose, even when there's no color/size swatch to draw.
  `target` can be an Axes or a Figure (figure-level multi-panel charts anchor to the
  whole figure).
- `repel_labels(ax, xs, ys, texts, ...)` — point-label de-collision (needs `adjustText`)

When restyling a script that currently has the palette/rcParams pasted inline
(e.g. an older notebook predating this module), replace the inline block with the
import above rather than leaving two copies of the palette to drift apart.

### Check glyph coverage before using a special character in chart text

If the brand font (Braintrust Display V2) is installed and registered via
`use_braintrust_theme()`, every `ax.set_title`/`ax.set_xlabel`/`ax.text`/`titled`/
`fig_title`/`key_box`/legend-label string renders through it — and that font does
**not** include every Unicode character. This shipped as a real bug: `Δ` (delta),
`η` (eta), `τ` (tau), and `▲`/`▼` all rendered as tofu boxes in chart titles/labels
even though the exact same characters look fine in this notebook's *markdown* cells
(Jupyter renders markdown with a system font, not the brand font, so the bug only
shows up in the exported PNGs, not in a quick on-screen read of the notebook).

Before using any non-ASCII character in a string that gets drawn by matplotlib
(title, label, annotation, legend, `key_box`), check it against the installed brand
font's cmap:

```python
from fontTools.ttLib import TTFont
cmap = TTFont(font_path).getBestCmap()   # font_path from fm.findfont(...)
ord(char) in cmap                        # False -> will render as a tofu box
```

`±`, `−` (minus), `·`, `→`, `–`/`—`, `…`, `≥`, `≈`, `≠`, `×`, `÷`, `§`, `²` are all
supported. Greek letters (`Δ`, `η`, `τ`, `Σ`) and most symbol/dingbat glyphs (`♦`,
`▲`, `▼`, `─`) are **not** — spell them out instead (`eta-squared` not `η²`, `tau2`
not `τ²`, `gap` not `Δ`, `up`/`down` not `▲`/`▼`). Markdown prose describing the same
chart is unaffected and can keep using the Unicode character if you prefer — just
keep the prose and the rendered chart text consistent with each other (don't tell the
reader to look for "Δ" in a title that now says "gap").

---

## Chart-type conventions

### Bar charts
- **Solid bars** (≥3 benchmarks / statistically meaningful): `BT_BLUE` or `BT_CMAP` gradient
- **Thin bars** (<3 benchmarks / de-emphasized): `BT_ICE_GREY`, no hatch
- **Error bars**: `BT_BLUE` cap color, `ecolor=BT_BLUE`
- **Diamond markers** (macro/benchmark-balanced rate): `facecolors="none"`, `edgecolors=BT_PINK`, `linewidth=1.5`
- **Value labels** (right-hand column): `color=BT_BLACK`, `weight="semibold"`
- **Secondary labels** (n=, bm counts): `color=BT_CONCRETE` for normal, `color=BT_ROSE` for flagged

### Heatmaps
- Colormap: `BT_HEAT`
- Masked/thin cells background: `ax.set_facecolor(BT_ICE_GREY)`
- Annotation text: white if cell value > 0.5, `BT_BLACK` if ≤ 0.5
- Cell borders: `linewidths=2, linecolor="white"`
- Low value = `BT_ICE_GREY`, high value = `BT_BLUE` — describe this in captions as
  "light → dark blue" or "pale → dark," never "red → green"

### Scatter / bubble charts
- All bubbles: `color=BT_BLUE`, `edgecolor="white"`, `linewidth=1.2`
- Reference lines (median crosshairs): `ls="--"`, `color=BT_ICE_GREY`
- **RELIABLE** label: `color=BT_LIME` on dark bg, `color=BT_GREEN` on white
- **ERRATIC** label: `color=BT_PINK` on dark bg, `color=BT_ROSE` on white

### Success-rate-colored bars (cost charts)
- Use `BT_SUCC` colormap: low success → BT Rose, high success → BT Blue
- Never use `RdYlGn`, `crest`, `Set2`, or any non-BT colormap

### Multi-series / categorical colors
When you need distinct colors for multiple categories (e.g. harnesses, models), use this fixed sequence in order:
```python
BT_CATEGORICAL = [BT_BLUE, BT_BLUE_ACCENT, BT_ICE_GREY, BT_PINK, BT_ROSE, BT_GREEN]
```

---

## Caption / legend / key wording

This is the part that breaks silently: the *colors* get fixed but the *words describing
them* (titles, subtitles, axis labels, legend text, prose right after a chart) keep
saying "red," "green," "yellow," "all-green row," "hatched," etc. from the old
RdYlGn/crest era. Every caption must describe the palette actually on screen.

When restyling an existing chart, grep the surrounding `titled(...)`, `fig_title(...)`,
subtitle strings, and the markdown prose immediately before/after the chart for:
`red`, `green`, `yellow`, `hatch(ed)`, and update them to match the BT palette:

| Old wording | New wording |
|---|---|
| "red → green" | "light → dark blue" / "pale → dark" |
| "all-green row" | "all-dark-blue row" |
| "a red cell" | "a pale/light cell" |
| "hatched" / "hatched bars" | "light bars" (BT_ICE_GREY fill, no hatch) |
| "red `…bm` count" | "pink `…bm` count" (BT_ROSE/BT_PINK flag) |
| "yellow band" | "pink band" |
| "blue <1 / red >1" | "blue <1 (BT_BLUE_ACCENT) / rose >1 (BT_ROSE)" |

Do this check on *every* chart you restyle, not just the ones with obvious leftover
color names in the styling code — caption text lives in separate strings and won't be
caught by an audit that only scans `color=`/`palette=`/`cmap=` arguments.

### Prefer real color swatches over color-name words

Plain subtitle text (`titled(ax, main, sub)`) cannot render an inline colored chip —
"rose >1 = thrash" is still just the word "rose." Whenever a chart's meaning depends on
which color is which, render that mapping as an actual `ax.legend()` with `Patch` or
`Line2D` handles instead of describing it in the subtitle string. The legend box then
shows a literal colored swatch next to each label, so the reader never has to know what
"BT Rose" looks like from the word alone.

```python
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ax.legend(handles=[
    Patch(facecolor=BT_ROSE, label="failures cost MORE (thrash)"),
    Patch(facecolor=BT_BLUE_ACCENT, label="failures cost LESS (give up)"),
    Line2D([0], [0], marker="D", linestyle="none", markerfacecolor="none",
           markeredgecolor=BT_PINK, markeredgewidth=1.5, markersize=9,
           label="benchmark-balanced (macro) rate"),
], loc="lower right", frameon=True, framealpha=0.92, edgecolor=BT_ICE_GREY, fontsize=8.5)
```

Rules of thumb:
- If a bar/dot/marker chart already passes `label=` to `ax.bar`/`ax.scatter`/`ax.plot`
  per series (e.g. `hue=` in seaborn, or one call per category with `label=`), calling
  `ax.legend()` is enough — matplotlib builds the real swatch automatically. No extra
  work needed.
- If color is assigned manually per-row (a list comprehension, a dict lookup, a
  threshold like `BT_ROSE if r > 1 else BT_BLUE_ACCENT`) with no `label=` anywhere,
  build the legend by hand with explicit `Patch`/`Line2D` handles.
- For a continuous gradient (a colormap mapped to a numeric value, e.g. success rate
  0–1), add a real `fig.colorbar(...)` instead of describing it as "color = success
  rate (low → high)" in words — the colorbar itself is the swatch.

### Once a legend exists, delete the caption that duplicates it

A legend and a subtitle that both explain the same color mapping is not extra
reinforcement — it's clutter, and the words drift stale even when the legend is correct
(this happened: `19_4b`'s subtitle kept saying "rose >1 = failures cost MORE · blue
<1 = failures cost LESS" for a full pass *after* the chart already had a legend
spelling out the same thing in real swatches). The rule: if you just added/confirmed a
real legend for a color mapping, go back and strip any subtitle clause that restates
that mapping in words. Keep a subtitle only for facts the legend doesn't carry (axis
definitions, units, non-color caveats). If nothing is left to say, drop the subtitle
entirely — `titled(ax, main, pad=20)` with no `sub` argument is fine.

### Match the legend swatch to how the color is actually drawn

A `Patch` (solid filled rectangle) tells the reader "somewhere in this chart, a region
is filled with this color." Don't use a `Patch` for a color that the chart only ever
applies to **text** (e.g. a colored `"6/6"` label) — that swatch is lying about what's
on screen, and a filled rectangle of a dark "label" color like `BT_GREEN`/`BT_ROSE`
also reads as muddy/near-black at legend size, which is the opposite of legible. This
exact bug shipped in the `01_1` coverage heatmap: green/rose only ever colored small
"X/6" annotations, never a fill, but the legend showed solid green/rose blocks anyway.

Match the encoding instead:
- **Filled region** (bar, heatmap cell, axhspan) → `Patch(facecolor=...)`
- **Marker / scatter dot** → `Line2D(marker=...)` with matching `markerfacecolor`/`markeredgecolor`
- **Colored text annotation** (no fill or marker anywhere) → render the legend entry as
  colored text too, not a block:
  ```python
  ax.text(1.0, 1.085, "≥5 of 6 suites covered", transform=ax.transAxes,
          ha="right", va="top", fontsize=8, color=BT_GREEN, weight="semibold")
  ax.text(1.0, 1.045, "<5 of 6 suites covered", transform=ax.transAxes,
          ha="right", va="top", fontsize=8, color=BT_ROSE, weight="semibold")
  ```
  Pair this with a normal `ax.legend()` for any genuinely-filled elements in the same
  chart (e.g. the ice-grey "too thin" cell background) — the two can coexist side by
  side; just don't put the text-only colors inside the `Patch` legend.

### This applies beyond color: any visual encoding gets a real legend, not prose

The same principle covers size, not just color. If bubble/marker size encodes a
numeric value (session count, n, spend), don't describe it in the subtitle as
"bubble = sessions" — show a handful of real, correctly-scaled example bubbles in a
legend, the same way a color legend shows real swatches:

```python
n_lo, n_hi = df.n.min(), df.n.max()
example_n = sorted(set(int(v) for v in [n_lo, np.sqrt(n_lo * n_hi), n_hi]))  # log-ish spread
example_sizes = np.interp(example_n, (n_lo, n_hi), (120, 800))  # match the real sizes= range
size_handles = [plt.scatter([], [], s=s, color=BT_ICE_GREY, edgecolor=BT_CONCRETE, linewidth=1)
                for s in example_sizes]
ax.legend(size_handles, [f"n={n}" for n in example_n], title="sessions",
          loc="lower left", frameon=True, framealpha=0.92, edgecolor=BT_ICE_GREY, fontsize=8)
```

And don't restate what an axis label already says. If `ax.set_xlabel(...)` /
`ax.set_ylabel(...)` already define what x and y mean, a subtitle clause like "x =
macro rate · y = std of those rates" is pure duplication — delete it. Subtitles should
only carry facts that have no other home on the chart (a caveat, a formula, a filter
threshold) — color goes in a color legend, size goes in a size legend, axis meaning
goes in axis labels, and the subtitle is what's left over once those exist.

---

## Output quality

- **DPI**: always 300 for both `figure.dpi` and `savefig.dpi`
- **Minimum figure width**: 12 inches for full-width charts, 10 inches minimum for any chart
- **Save format**: PNG with `bbox_inches="tight"`

---

## Audit checklist

Before exporting graphs, run this check. Any hit is a violation:

```python
import re
from pathlib import Path

BANNED_PATTERNS = [
    # Off-brand colormaps
    r'"RdYlGn"', r'"crest"', r'"Set1"', r'"Set2"', r'"Set3"',
    r'"Blues"', r'"Greens"', r'"Reds"', r'"viridis"', r'"coolwarm"',
    r'"magma"', r'"plasma"', r'"rocket"', r'"rocket_r"',
    r'plt\.cm\.[A-Za-z]',
    # Raw hex colors (anything that isn't a BT constant)
    r'color\s*=\s*"#(?!2C1FEB|3A77EB|000000|504F4F|D8DEEE|CCFF00|14382D|F5AFD1|651D31|FFFFFF)[0-9A-Fa-f]{3,6}"',
    r'palette\s*=\s*"#[0-9A-Fa-f]',
    # Old accent colors commonly mistaken for BT colors
    r'"#c0392b"', r'"#2a8a4a"', r'"#e8e8e8"', r'"#888888"', r'"#333333"',
    r'"#f0c419"', r'"#9a7d0a"', r'"#f0f0f0"', r'"#f3f3f3"', r'"#f9fafb"',
]

# Stray color WORDS in titles/subtitles/captions/markdown prose — these survive
# even after the color= args are fixed, because caption text lives in separate
# strings. Catches the class of bug where code uses BT_HEAT but the subtitle still
# says "red → green."
BANNED_CAPTION_WORDS = [
    r'\bred\b', r'\bgreen\b', r'\byellow\b', r'\bhatch(ed)?\b',
    r'all-green', r'a red cell', r'red cell',
]

def audit_file(path, check_captions=True):
    src = Path(path).read_text()
    violations = []
    for pattern in BANNED_PATTERNS:
        for match in re.finditer(pattern, src, re.IGNORECASE):
            line_num = src[:match.start()].count('\n') + 1
            violations.append(f"Line {line_num}: {match.group()}")
    if check_captions:
        for pattern in BANNED_CAPTION_WORDS:
            for match in re.finditer(pattern, src, re.IGNORECASE):
                line_num = src[:match.start()].count('\n') + 1
                violations.append(f"Line {line_num} [caption wording]: {match.group()!r}")
    violations = sorted(set(violations), key=lambda v: int(v.split(":")[0].split()[1]))
    if violations:
        print(f"❌ {len(violations)} off-brand reference(s) found in {path}:")
        for v in violations:
            print(f"   {v}")
    else:
        print(f"✅ {path} — all colors and captions on-brand")
    return violations

# Usage: audit_file("scripts/build_notebook.py")
# Caption-word hits need a human read — "red" can appear in unrelated prose
# (e.g. "Red Hat"), so review each match rather than blind find-and-replace.
```

---

## What to never use

- `RdYlGn`, `crest`, `Set2`, `Blues`, `Greens`, `Reds`, or any named seaborn/matplotlib colormap
- `plt.cm.<anything>` — always use a named BT constant or BT colormap
- Raw hex literals anywhere except inside the palette constants block at the top
- Hatching (`hatch="///"`) on de-emphasized bars — use `BT_ICE_GREY` fill instead
- Semi-transparent bars (`alpha < 1`) for de-emphasis — use `BT_ICE_GREY` fill instead
- Red/green as a success/failure signal — use BT Rose/Pink (warning) and BT Blue (success)
