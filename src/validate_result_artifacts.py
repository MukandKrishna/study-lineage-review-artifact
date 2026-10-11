"""Check that paper-facing result tables and figures are present."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    ROOT / "results" / "final_naacl" / "paper_scope_and_denominator.md",
    ROOT / "results" / "final_naacl" / "call_coverage_manifest.csv",
    ROOT / "paper" / "main.tex",
    ROOT / "paper" / "figures" / "fig1_story_candidate.pdf",
    ROOT / "paper" / "figures" / "fig2_story_candidate.pdf",
)


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
    if missing:
        raise SystemExit("Missing paper artifacts:\n- " + "\n- ".join(missing))
    print(f"PASS {len(REQUIRED)} paper artifacts present")


if __name__ == "__main__":
    main()
