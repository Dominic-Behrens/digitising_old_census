"""Convert unambiguous printed quantities; never guess damaged OCR digits."""
from __future__ import annotations

import re

NO_VALUE = re.compile(r"^[\s.·•…⋅\u2024\u2025—–−\-„〃”‘’\"'~“]*$")
NUMBER = re.compile(r"^[+-]?(?:(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,3}(?: \d{3})+)(?:\.\d*)?|\.\d+)$")


def numeric_value(raw: str) -> int | float | str | None:
    """Return a number, blank for source marks, or the unchanged unresolved text."""
    text = str(raw).strip()
    if not text or NO_VALUE.fullmatch(text):
        return None
    cleaned = re.sub(r"^[*†‡]+|[*†‡]+$", "", text).strip()
    if not NUMBER.fullmatch(cleaned):
        return text
    cleaned = cleaned.replace(",", "").replace(" ", "")
    return float(cleaned) if "." in cleaned else int(cleaned)


def numeric_format(raw: str) -> str:
    """Keep printed precision and footnote marks while retaining a numeric value."""
    text = str(raw).strip()
    leading = re.match(r"^[*†‡]+", text)
    trailing = re.search(r"[*†‡]+$", text)
    cleaned = re.sub(r"^[*†‡]+|[*†‡]+$", "", text).strip()
    decimals = len(cleaned.rsplit(".", 1)[1]) if "." in cleaned else 0
    code = "#,##0" + ("." + "0" * decimals if decimals else "")
    if leading:
        code = '"' + leading.group() + '"' + code
    if trailing:
        code += '"' + trailing.group() + '"'
    return code


def source_conflicted_fields(number: int, columns: dict[str, int], record: list[str]) -> tuple[str, ...]:
    """Keep a source-punctuation conflict as text, not a guessed density.

    Physical p193 prints Tinaroo's density as 3,279. Neither interpreting
    it as 3279 nor replacing it with 3.279 is source-established.
    """
    if number != 68:
        return ()
    names = ("state", "area_type", "council", "occupied_dwellings_per_area_unit")
    if not all(name in columns for name in names):
        return ()
    if tuple(record[columns[name]] for name in names) == ("Queensland", "Shires", "Tinaroo", "3,279"):
        return ("occupied_dwellings_per_area_unit",)
    return ()
