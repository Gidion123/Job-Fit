"""Chart style for JobFit research figures (static PNG for notebooks and slides).

Follows the reference data-viz palette: categorical slots in fixed order (first three validated
all-pairs for colorblind separation), one hue for single-series charts, hairline recessive grid,
text in ink tokens (never the series color), selective direct labels, no dual axes.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # blue, orange, aqua; max 3 series per chart
NEUTRAL = "#c3c2b7"                           # de-emphasis / "unknown" category
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]


def apply_style() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "semibold", "axes.titlelocation": "left",
        "axes.titlecolor": INK, "axes.labelcolor": INK_2, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": INK_2, "axes.edgecolor": BASELINE,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.axisbelow": True, "legend.frameon": False, "figure.dpi": 110, "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })


def barh(ax, labels, values, color=SERIES[0], fmt="{:,.0f}", note_values=None):
    """Horizontal bars, largest on top, value labels at the bar tip in secondary ink."""
    y = range(len(labels))[::-1]
    ax.barh(list(y), values, color=color, height=0.62)
    ax.set_yticks(list(y), labels)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    vmax = max(values) if len(values) else 1
    for yi, v, extra in zip(y, values, note_values or [None] * len(values)):
        text = fmt.format(v) + (f"  {extra}" if extra else "")
        ax.text(v + vmax * 0.01, yi, text, va="center", ha="left", color=INK_2, fontsize=9)
    ax.set_xlim(0, vmax * 1.18)
    return ax


def save(fig, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    return path
