from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath


OUT = Path(__file__).resolve().parent
INK = "#1B2832"
MUTED = "#52616B"
BLUE = "#176392"
BLUE_PALE = "#EFF6FB"
GREEN = "#26745B"
GREEN_PALE = "#F0F7F3"
RED = "#AD3F39"
RED_PALE = "#FFF3F1"
RULE = "#B5C2C9"


def box(ax, x, y, w, h, face, edge, radius=1.5, lw=0.9):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=lw,
    )
    ax.add_patch(patch)


def label(ax, x, y, value, *, size=8, color=INK, weight="normal", ha="left"):
    ax.text(
        x, y, value, ha=ha, va="center", fontsize=size,
        fontweight=weight, color=color, family="DejaVu Sans",
    )


def paper_icon(ax, x, y, color):
    vertices = [
        (x, y), (x + 8.1, y), (x + 8.1, y + 10.0),
        (x + 5.9, y + 12.2), (x, y + 12.2), (x, y),
        (x + 5.9, y + 12.2), (x + 5.9, y + 10.0),
        (x + 8.1, y + 10.0),
    ]
    codes = [
        MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO,
        MplPath.LINETO, MplPath.LINETO, MplPath.CLOSEPOLY,
        MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO,
    ]
    ax.add_patch(PathPatch(MplPath(vertices, codes), facecolor="white", edgecolor=color, lw=0.9))
    ax.plot([x + 1.5, x + 6.5], [y + 6.3, y + 6.3], color=color, lw=0.7)
    ax.plot([x + 1.5, x + 5.4], [y + 4.2, y + 4.2], color=color, lw=0.7)


def robot_icon(ax, x, y):
    """Draw the small head, ears, antenna, and eyes used in the figure."""
    ax.add_patch(FancyBboxPatch(
        (x, y), 5.6, 4.2, boxstyle="round,pad=0,rounding_size=0.55",
        facecolor=MUTED, edgecolor=MUTED, linewidth=0,
    ))
    ax.add_patch(Rectangle((x - 0.7, y + 1.0), 0.7, 2.2, color=MUTED, linewidth=0))
    ax.add_patch(Rectangle((x + 5.6, y + 1.0), 0.7, 2.2, color=MUTED, linewidth=0))
    ax.plot([x + 2.8, x + 2.8], [y + 4.2, y + 5.0], color=MUTED, lw=0.9)
    ax.add_patch(Circle((x + 2.8, y + 5.2), 0.32, color=MUTED, linewidth=0))
    for eye_x in (x + 1.7, x + 3.9):
        ax.add_patch(Circle((eye_x, y + 2.3), 0.40, color="white", linewidth=0))


def main() -> None:
    plt.rcParams["svg.fonttype"] = "path"
    fig = plt.figure(figsize=(3.12, 3.40), facecolor="white")
    ax = fig.add_axes((0.02, 0.015, 0.96, 0.97))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 111)
    ax.axis("off")

    label(ax, 50, 107.8, "STRIVE: two reports, one trial", size=10.2, weight="bold", ha="center")
    ax.plot([1, 99], [103.8, 103.8], color=RULE, lw=0.6)
    label(ax, 2.5, 99.9, "Fixed claim", size=7.3, color=BLUE, weight="bold")
    label(ax, 26.5, 99.9, "Erenumab reduces migraine frequency", size=6.9)
    label(ax, 26.5, 96.0, "vs placebo in adults with episodic migraine", size=6.4)

    # Study groups, not individual papers, are the visible evidence units.
    box(ax, 1.5, 55.5, 61.0, 36.1, BLUE_PALE, BLUE, radius=1.5)
    box(ax, 65.0, 55.5, 33.5, 36.1, GREEN_PALE, GREEN, radius=1.5)
    label(ax, 4.0, 86.6, "STRIVE", size=9.1, color=BLUE, weight="bold")
    label(ax, 4.0, 81.6, "NCT02456740", size=7.1, color=MUTED)
    paper_icon(ax, 5.0, 64.6, BLUE)
    paper_icon(ax, 31.0, 64.6, BLUE)
    label(ax, 15.3, 70.0, "Primary", size=7.0)
    label(ax, 15.3, 66.1, "report", size=7.0)
    label(ax, 41.3, 70.0, "Later", size=7.0)
    label(ax, 41.3, 66.1, "analysis", size=7.0)
    label(ax, 33.0, 59.2, "SAME TRIAL", size=7.5, color=BLUE, weight="bold", ha="center")

    label(ax, 67.5, 86.6, "ARISE", size=9.1, color=GREEN, weight="bold")
    label(ax, 67.5, 81.6, "NCT02483585", size=7.1, color=MUTED)
    paper_icon(ax, 68.5, 64.6, GREEN)
    label(ax, 79.0, 70.0, "Primary", size=7.0)
    label(ax, 79.0, 66.1, "report", size=7.0)
    label(ax, 81.7, 59.2, "NEW TRIAL", size=7.5, color=GREEN, weight="bold", ha="center")

    robot_icon(ax, 20.5, 48.7)
    label(ax, 58, 50.8, "Two separate GPT-5.5 tasks", size=7.3, color=MUTED, ha="center")
    box(ax, 1.5, 7.8, 47.5, 39.0, "white", BLUE, radius=1.5)
    box(ax, 51.0, 7.8, 47.5, 39.0, "white", RED, radius=1.5)
    box(ax, 1.5, 39.2, 47.5, 7.6, BLUE_PALE, BLUE, radius=1.5)
    box(ax, 51.0, 39.2, 47.5, 7.6, RED_PALE, RED, radius=1.5)
    label(ax, 25.2, 43.0, "RECOGNISE LINEAGE", size=7.6, color=BLUE, weight="bold", ha="center")
    label(ax, 74.7, 43.0, "AGGREGATE EVIDENCE", size=7.6, color=RED, weight="bold", ha="center")

    label(ax, 25.2, 33.4, "ARISE is the new trial", size=7.9, weight="bold", ha="center")
    label(ax, 25.2, 25.5, "10/10", size=14.2, color=BLUE, weight="bold", ha="center")
    label(ax, 25.2, 18.1, "recognition calls correct", size=7.1, ha="center")
    label(ax, 25.2, 12.2, "both A/B orders", size=6.7, color=MUTED, ha="center")

    label(ax, 74.7, 33.4, "Later STRIVE analysis", size=7.7, weight="bold", ha="center")
    label(ax, 74.7, 29.0, "counted as independent", size=7.0, weight="bold", ha="center")
    label(ax, 74.7, 21.5, "5/5", size=14.2, color=RED, weight="bold", ha="center")
    label(ax, 74.7, 14.1, "aggregation calls over-credit", size=6.9, ha="center")

    label(ax, 50, 3.5, "Publication count is not study count.", size=7.6, weight="bold", ha="center")
    for suffix in ("svg", "pdf", "png"):
        fig.savefig(OUT / f"fig1_story_candidate.{suffix}", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
