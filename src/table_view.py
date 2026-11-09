"""
Table views for the terminal (Challenge 4).

Uses the `tabulate` library when it is installed (pip install tabulate);
otherwise falls back to a small built-in ASCII table, so nothing extra is required.
"""

import textwrap
from typing import List, Sequence

try:  # optional dependency
    from tabulate import tabulate as _tabulate
except ImportError:  # pragma: no cover - depends on the environment
    _tabulate = None

BAR_LENGTH = 10


def mini_bar(score: float, best: float, length: int = BAR_LENGTH) -> str:
    """A short text bar showing score / best, clamped to the bar length."""
    filled = max(0, min(length, round(length * score / best))) if best else 0
    return "█" * filled + "░" * (length - filled)


def _wrap_cell(text: str, width: int) -> List[str]:
    """Wrap one cell to `width`, keeping its own line breaks (one reason per line)."""
    lines: List[str] = []
    for part in str(text).split("\n"):
        lines.extend(textwrap.wrap(part, width, subsequent_indent="  ") or [""])
    return lines


def ascii_table(headers: Sequence[str], rows: Sequence[Sequence], widths: Sequence[int]) -> str:
    """Render a boxed table with wrapped, multi-line cells using only built-in Python."""
    def border(left: str, mid: str, right: str) -> str:
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def render_row(cells: Sequence) -> List[str]:
        wrapped = [_wrap_cell(c, w) for c, w in zip(cells, widths)]
        height = max(len(lines) for lines in wrapped)
        return [
            "│" + "│".join(f" {(lines[i] if i < len(lines) else ''):<{w}} " for lines, w in zip(wrapped, widths)) + "│"
            for i in range(height)
        ]

    out = [border("┌", "┬", "┐"), *render_row(headers), border("├", "┼", "┤")]
    for i, row in enumerate(rows):
        if i:
            out.append(border("├", "┼", "┤"))
        out.extend(render_row(row))
    out.append(border("└", "┴", "┘"))
    return "\n".join(out)


def make_table(headers: Sequence[str], rows: Sequence[Sequence], widths: Sequence[int]) -> str:
    """Use tabulate if available, otherwise the built-in ASCII table."""
    if _tabulate is not None:
        return _tabulate(rows, headers=headers, tablefmt="fancy_grid", maxcolwidths=list(widths))
    return ascii_table(headers, rows, widths)


# Column widths for the recommendations table (total stays under ~100 characters).
REC_HEADERS = ("#", "Song / Artist", "Genre / Mood", "Score", "Why (reasons for the score)")
REC_WIDTHS = (2, 19, 12, 11, 40)


def recommendations_table(recommendations: list, best: float) -> str:
    """One row per recommended song, with every reason for its score on its own line."""
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append((
            rank,
            f"{song['title']}\n{song['artist']}",
            f"{song['genre']}\n{song['mood']}",
            f"{score:.2f} / {best:.2f}\n{mini_bar(score, best)}",
            "\n".join(f"• {reason}" for reason in explanation.split("; ")),
        ))
    return make_table(REC_HEADERS, rows, REC_WIDTHS)


SUMMARY_HEADERS = ("Profile", "#1 pick", "Score", "Match", "Also in top 5")
SUMMARY_WIDTHS = (26, 18, 5, 5, 30)


def summary_table(results: list) -> str:
    """One row per profile: its #1 song, how close it is to perfect, and the rest of the top 5.

    `results` is a list of (profile_name, recommendations, best_possible_score).
    """
    rows = []
    for name, recs, best in results:
        song, score, _ = recs[0]
        rows.append((
            name,
            song["title"],
            f"{score:.2f}",
            f"{score / best:.0%}" if best else "-",
            ", ".join(s["title"] for s, _, _ in recs[1:]),
        ))
    return make_table(SUMMARY_HEADERS, rows, SUMMARY_WIDTHS)
