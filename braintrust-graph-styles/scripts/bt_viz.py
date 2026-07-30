"""Braintrust brand styling for matplotlib/seaborn charts.

Single source of truth for colors, colormaps, typography, and the small
helper functions (`titled`, `fig_title`, `repel_labels`) used across
build_notebook.py and any other script that renders Braintrust-branded
figures. Import this instead of re-declaring the palette/rcParams inline.

    sys.path.insert(0, "scripts")
    import bt_viz as viz
    viz.use_braintrust_theme()

Colors below are the designer-confirmed brand hex values — do not add,
substitute, or "generalize" any color that isn't one of these constants.
If you need a new visual encoding (e.g. a diverging scale), compose it from
these colors rather than introducing an unverified one.
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap

# ── Braintrust brand palette (designer-confirmed hex — do not edit) ───────────
BT_BLUE        = "#2C1FEB"   # primary bars, bubbles, main data series
BT_BLUE_ACCENT = "#3A77EB"   # secondary bars, gradient mid-point
BT_BLACK       = "#000000"   # titles, primary text
BT_CONCRETE    = "#504F4F"   # axis labels, secondary text, tick labels
BT_ICE_GREY    = "#D8DEEE"   # thin/de-emphasized fills, gridlines, axis borders, diverging-scale neutral
BT_LIME        = "#CCFF00"   # positive highlights on dark backgrounds
BT_GREEN       = "#14382D"   # RELIABLE labels, success call-outs (dark, on white)
BT_PINK        = "#F5AFD1"   # diamond markers, accent on white backgrounds
BT_ROSE        = "#651D31"   # ERRATIC labels, warning call-outs, low-success bars
BT_WHITE       = "#FFFFFF"   # backgrounds only

# ── Colormaps (built only from the constants above) ───────────────────────────
# General gradient (de-emphasized -> primary): success-rate-mapped bars/bubbles.
BT_CMAP = LinearSegmentedColormap.from_list("bt_blue", [BT_ICE_GREY, BT_BLUE_ACCENT, BT_BLUE])

# Heatmap gradient: use wherever RdYlGn/Blues/etc. would otherwise be used.
BT_HEAT = LinearSegmentedColormap.from_list("bt_heat", [BT_ICE_GREY, BT_BLUE_ACCENT, BT_BLUE])

# Success-rate bar coloring (low -> high): rose/pink (low) -> blue (high).
BT_SUCC = LinearSegmentedColormap.from_list("bt_succ", [BT_ROSE, BT_PINK, BT_BLUE_ACCENT, BT_BLUE])

# Diverging scale for SIGNED deltas vs. a baseline (e.g. cost ratio vs. 1.0,
# score change vs. a reference run): rose = below baseline, ice grey = ~zero,
# blue = above baseline. Symmetric around the neutral midpoint so vmin/vmax
# should be set symmetrically (e.g. vmin=-x, vmax=x) by the caller.
BT_DIVERGING = LinearSegmentedColormap.from_list(
    "bt_diverging", [BT_ROSE, BT_PINK, BT_ICE_GREY, BT_BLUE_ACCENT, BT_BLUE]
)

ANNOT = dict(fontsize=8.5, color=BT_CONCRETE)


# ── Typography ──────────────────────────────────────────────────────────────
# Brand typeface is Braintrust Display V2. We never bundle font files in this
# repo, so register_brand_fonts() only does something if you point it at a
# local directory containing the installed .otf/.ttf files; otherwise the
# fallback stack below is used automatically.
_FONT_FALLBACKS = ("Braintrust Display V2", "Helvetica Neue", "Arial", "Inter", "DejaVu Sans")

# Point sizes, by element (mirrors the brand type scale used in build_notebook.py).
FONT_SIZES = {
    "title": 14,
    "subtitle": 9,
    "axis_label": 10.5,
    "tick_label": 9.5,
    "legend": 9,
    "legend_title": 9.5,
    "value_label": 10.5,
    "annotation": 8.5,
}


def register_brand_fonts(font_dir: str | os.PathLike | None = None) -> None:
    """Register local Braintrust Display V2 font files, if available.

    Do not bundle font files in this repo or in generated artifacts. Pass the
    local directory containing the installed .otf/.ttf files when rendering on
    a machine that has the brand font; otherwise this is a no-op and the
    portable fallback stack (Helvetica Neue / Arial / Inter / DejaVu Sans) is
    used instead.
    """
    if not font_dir:
        return
    for fp in glob.glob(str(Path(font_dir) / "*.otf")) + glob.glob(str(Path(font_dir) / "*.ttf")):
        try:
            fm.fontManager.addfont(fp)
        except Exception:
            pass


def _available_font(preferred: tuple[str, ...] = _FONT_FALLBACKS) -> str:
    names = {f.name for f in fm.fontManager.ttflist}
    for name in preferred:
        if name in names:
            return name
    return "DejaVu Sans"


def use_braintrust_theme(font_dir: str | os.PathLike | None = None) -> None:
    """Apply the global Braintrust chart theme (colors, fonts, rcParams).

    Call once near the top of a notebook/script, before creating any figures.
    """
    import seaborn as sns

    register_brand_fonts(font_dir)
    family = _available_font()

    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "font.family": family,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": BT_ICE_GREY,
        "axes.linewidth": 0.8,
        "axes.titlesize": FONT_SIZES["title"],
        "axes.titleweight": "bold",
        "axes.titlepad": 12,
        "axes.titlecolor": BT_BLACK,
        "axes.labelsize": FONT_SIZES["axis_label"],
        "axes.labelcolor": BT_CONCRETE,
        "axes.labelpad": 6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": BT_ICE_GREY,
        "grid.linewidth": 0.8,
        "xtick.labelsize": FONT_SIZES["tick_label"],
        "ytick.labelsize": FONT_SIZES["tick_label"],
        "xtick.color": BT_CONCRETE,
        "ytick.color": BT_CONCRETE,
        "legend.fontsize": FONT_SIZES["legend"],
        "legend.title_fontsize": FONT_SIZES["legend_title"],
        "legend.frameon": False,
        "font.size": FONT_SIZES["axis_label"],
        "figure.titlesize": 15,
        "figure.titleweight": "bold",
    })


# ── Shared helpers ──────────────────────────────────────────────────────────
def titled(ax, main: str, sub: str | None = None, pad: float = 22) -> None:
    """Left-aligned bold title with an optional grey subtitle.

    Only pass `sub` for facts a legend/colorbar doesn't already carry (axis
    definitions, units, non-color caveats). If a chart has a real legend for
    its color mapping, do not restate that mapping here in words.
    """
    ax.set_title(main, loc="left", pad=pad, fontweight="bold")
    if sub:
        ax.annotate(sub, xy=(0, 1), xytext=(0, 5), xycoords="axes fraction",
                    textcoords="offset points", fontsize=FONT_SIZES["subtitle"],
                    color=BT_CONCRETE, va="bottom")


def fig_title(fig, main: str, sub: str | None = None) -> None:
    """Figure-level title + subtitle, placed above tight_layout."""
    h = fig.get_figheight()
    fig.text(0.012, 1 + 0.32 / h, main, ha="left", fontsize=FONT_SIZES["title"],
              fontweight="bold", color=BT_BLACK)
    if sub:
        fig.text(0.012, 1 + 0.10 / h, sub, ha="left", fontsize=FONT_SIZES["subtitle"],
                  color=BT_CONCRETE)


_KEY_BOX_POSITIONS = {
    "upper right": (0.99, 0.99, "right", "top"),
    "upper left": (0.01, 0.99, "left", "top"),
    "lower right": (0.99, 0.01, "right", "bottom"),
    "lower left": (0.01, 0.01, "left", "bottom"),
}


def key_box(target, lines: list[str], loc: str = "upper right", fontsize: float = 8) -> None:
    """A boxed, legend-styled key for chart facts that aren't a color/size mapping
    (a symbol definition like "Δ = best-worst harness", a notation key like "bar =
    success ±Wilson 95% CI"). Use this instead of putting that text in a plain
    subtitle — it should look like a legend (framed box), not floating prose, even
    though there's no swatch to draw.

    `target` is an Axes or a Figure (figure-level multi-panel charts can anchor the
    key box to the whole figure rather than to one panel).
    """
    x, y, ha, va = _KEY_BOX_POSITIONS[loc]
    transform = target.transAxes if hasattr(target, "transAxes") else target.transFigure
    target.text(x, y, "\n".join(lines), transform=transform, ha=ha, va=va,
                 fontsize=fontsize, color=BT_CONCRETE,
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                           edgecolor=BT_ICE_GREY, alpha=0.92), zorder=10)


def repel_labels(ax, xs, ys, texts, fontsize: float = 8.5, color: str | None = None):
    """Place point labels with auto de-collision (requires adjustText)."""
    from adjustText import adjust_text

    color = color or BT_CONCRETE
    objs = [ax.text(x, y, t, fontsize=fontsize, color=color) for x, y, t in zip(xs, ys, texts)]
    adjust_text(objs, ax=ax,
                arrowprops=dict(arrowstyle="-", color=BT_ICE_GREY, lw=0.6),
                expand=(1.15, 1.4), force_text=(0.4, 0.6))
    return objs
