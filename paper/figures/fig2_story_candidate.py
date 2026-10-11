import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle


HERE = Path(__file__).resolve().parent
EVIDENCE = (
    HERE.parents[1]
    / "results/final_naacl"
    / "paper_evidence_sheet_2026_10_07/family_level_results.csv"
)
MODELS = (
    ("GPT-5.5", "GPT-5.5"),
    ("Qwen3-4B", "Qwen3-4B"),
    ("Gemma3-4B", "Gemma3-4B"),
    ("Llama-3.1-8B", "Llama-3.1-8B"),
    ("Ministral-3-8B", "Ministral-3-8B"),
)
ORIGINAL = ("CF-P1", "CF-P2", "CF-P3")
LATER = ("P5R", "P6R")

INK = "#17212A"
MUTED = "#34444D"
BLUE = "#176392"
RED = "#AD3F39"
GREEN = "#26745B"
PALE_RED = "#FBEDEB"
PALE_GREEN = "#EDF6F0"
PALE_GRAY = "#F1F3F4"
RULE = "#C6CFD3"


def read_evidence() -> dict[tuple[str, str], dict[str, str]]:
    with EVIDENCE.open(newline="", encoding="utf-8-sig") as stream:
        rows = {(row["family"], row["model"]): row for row in csv.DictReader(stream)}
    for family in ORIGINAL + LATER:
        for model, _ in MODELS:
            row = rows[(family, model)]
            assert int(row["same_trial_valid"]) + int(row["same_trial_rejected"]) == 5
            if family in LATER:
                assert int(row["grouped_valid"]) + int(row["grouped_rejected"]) == 5
    return rows


def text(ax, x, y, value, *, size=8, color=INK, weight="normal", ha="left"):
    ax.text(
        x, y, value, ha=ha, va="center", fontsize=size, color=color,
        fontweight=weight, family="DejaVu Sans",
    )


def rounded(ax, x, y, width, height, face, edge="none", lw=0, radius=3):
    ax.add_patch(FancyBboxPatch(
        (x, y), width, height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=face, edgecolor=edge, linewidth=lw,
    ))


def original_cell(ax, row, x, y):
    recognition_correct = int(row["provenance_recognition_correct"])
    recognition_valid = int(row["provenance_recognition_valid"])
    recognition_rejected = int(row["recognition_rejected"])
    overcredit = int(row["same_trial_overcredit"])
    same_valid = int(row["same_trial_valid"])
    full_recognition = recognition_correct == recognition_valid == 10
    full_gap = full_recognition and overcredit == same_valid == 5
    rounded(ax, x, y - 14, 58, 30, PALE_RED if full_gap else PALE_GRAY if same_valid == 0 else "white")
    recognition = f"{recognition_correct}/{recognition_valid}"
    if recognition_rejected:
        recognition += "*"
    text(ax, x + 29, y + 6.4, recognition, size=8.3,
         color=BLUE if full_recognition else MUTED, weight="bold", ha="center")
    text(ax, x + 29, y - 6.0, f"{overcredit}/{same_valid}" if same_valid else "NA",
         size=8.6, color=RED if overcredit else MUTED,
         weight="bold" if overcredit else "normal", ha="center")


def later_cell(ax, row, x, y):
    document_valid = int(row["same_trial_valid"])
    grouped_valid = int(row["grouped_valid"])
    document_overcredit = int(row["same_trial_overcredit"])
    grouped_overcredit = int(row["grouped_overcredit"])
    improved = document_valid and grouped_valid and grouped_overcredit < document_overcredit
    unchanged_error = document_valid and grouped_valid and document_overcredit and grouped_overcredit == document_overcredit
    face = PALE_GREEN if improved else PALE_RED if unchanged_error else PALE_GRAY
    rounded(ax, x, y - 14, 87, 30, face)
    document_rejected = int(row["same_trial_rejected"])
    grouped_rejected = int(row["grouped_rejected"])
    before = (f"{document_overcredit}/{document_valid}"
              if document_valid else f"NA{'*' if document_rejected else ''}")
    after = (f"{grouped_overcredit}/{grouped_valid}"
             if grouped_valid else f"NA{'*' if grouped_rejected else ''}")
    text(ax, x + 43.5, y + 0.5, f"{before}  →  {after}", size=8.5,
         color=GREEN if improved else RED if unchanged_error else MUTED,
         weight="bold" if improved or unchanged_error else "normal", ha="center")


def main():
    rows = read_evidence()
    fig = plt.figure(figsize=(7.2, 3.13), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 720)
    ax.set_ylim(0, 313)
    ax.axis("off")

    text(ax, 16, 292, "Correct lineage answers coexist with over-credit; grouping helps selectively",
         size=10.8, weight="bold")
    ax.plot([16, 704], [277, 277], color=RULE, lw=0.75)

    rounded(ax, 16, 246, 23, 22, BLUE, radius=3)
    text(ax, 27.5, 257, "A", size=9, color="white", weight="bold", ha="center")
    text(ax, 45, 257, "Original provenance families", size=8.6, weight="bold")
    text(ax, 16, 236, "Top: lineage recognition correct / valid", size=7.5, color=MUTED)
    text(ax, 16, 225, "Bottom: same-trial over-credit / valid", size=7.5, color=MUTED)

    rounded(ax, 368, 246, 23, 22, BLUE, radius=3)
    text(ax, 379.5, 257, "B", size=9, color="white", weight="bold", ha="center")
    text(ax, 397, 257, "Later study-grouping test", size=8.6, weight="bold")
    text(ax, 368, 236, "Same-trial over-credit: document → grouped", size=7.5, color=MUTED)
    text(ax, 368, 225, "Counts are calls within each clinical family", size=7.5, color=MUTED)

    original_x = (157, 220, 283)
    later_x = (493, 590)
    for x, name in zip(original_x, ORIGINAL):
        text(ax, x + 29, 208, name, size=8.2, weight="bold", ha="center")
    for x, name in zip(later_x, LATER):
        text(ax, x + 43.5, 208, name, size=8.2, weight="bold", ha="center")
    ax.plot([16, 344], [198, 198], color=RULE, lw=0.65)
    ax.plot([368, 704], [198, 198], color=RULE, lw=0.65)

    for index, (model, label) in enumerate(MODELS):
        y = 181 - 31 * index
        text(ax, 18, y, label, size=8.1, weight="bold")
        text(ax, 370, y, label, size=8.1, weight="bold")
        for family, x in zip(ORIGINAL, original_x):
            original_cell(ax, rows[(family, model)], x, y)
        for family, x in zip(LATER, later_x):
            later_cell(ax, rows[(family, model)], x, y)

    ax.plot([16, 704], [37, 37], color=RULE, lw=0.65)
    rounded(ax, 16, 18, 11, 11, PALE_RED)
    text(ax, 34, 23.5, "A pink: full recognition + over-credit", size=7.4)
    rounded(ax, 368, 18, 11, 11, PALE_GREEN)
    text(ax, 386, 23.5, "B green: fewer errors", size=7.4)
    rounded(ax, 524, 18, 11, 11, PALE_RED)
    text(ax, 542, 23.5, "pink: unchanged error", size=7.4)
    text(ax, 16, 8.5, "NA = five rejected verifier outputs", size=7.4, color=MUTED)
    text(ax, 368, 8.5, "* = five rejected calls in the marked condition", size=7.4, color=MUTED)

    # The safety check belongs in the caption: a longer footer would make the
    # one-screen comparison less legible at two-column paper width.
    for suffix in ("pdf", "png", "svg"):
        fig.savefig(HERE / f"fig2_story_candidate.{suffix}", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
