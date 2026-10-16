"""Transcribe the facing-page state/area panels of Dwellings Tables 59–63.

Candidate column numbers restart on every physical page.  The two halves of each
printed table have respectively 12 and 11 geographical columns; monetary tables
sometimes transcribe each shillings/pence pair as one source cell.
"""

import re


# In printed order, matching the workbooks' STATE_AREA_COLUMNS in the exporter.
LEFT_AREAS = (
    "new_south_wales_sydney_and_suburbs", "new_south_wales_remainder_of_state",
    "new_south_wales_whole_state", "victoria_melbourne_and_suburbs",
    "victoria_remainder_of_state", "victoria_whole_state",
    "queensland_brisbane_and_suburbs", "queensland_remainder_of_state",
    "queensland_whole_state", "south_australia_adelaide_and_suburbs",
    "south_australia_remainder_of_state", "south_australia_whole_state",
)
RIGHT_AREAS = (
    "western_australia_perth_and_suburbs", "western_australia_remainder_of_state",
    "western_australia_whole_state", "tasmania_hobart_and_suburbs",
    "tasmania_remainder_of_state", "tasmania_whole_state", "northern_territory",
    "federal_territory", "commonwealth_total_metropolitan",
    "commonwealth_remainder_of_commonwealth", "commonwealth_whole_commonwealth",
)

# Directly legible PDF values absent or misaligned in cells.csv (pages 126–129).
# Each numeric string is in printed state/area order; monetary strings alternate
# shillings and pence. Dots are the printed missing-value marks, not zeroes.
PDF_RIGHT_59 = {
    # PDF p.127 rows 9–10: an OCR rule fragment displaced Federal Territory
    # and all three Commonwealth values; the last value was lost altogether.
    "9": "6.357 6.556 6.450 5.554 6.116 5.930 15.000 4.429 5.851 6.377 6.166",
    "10": "6.707 6.866 6.792 5.988 6.133 6.091 4.000 6.875 6.053 6.657 6.416",
    "Unspecified": "4.078 3.890 3.973 4.313 4.405 4.385 4.333 2.333 4.271 4.314 4.299",
    "All Private Dwellings": "4.452 3.326 3.684 4.645 4.576 4.590 2.246 3.835 4.698 4.441 4.535",
}
PDF_RIGHT_61 = {
    "13": "47 1 25 5 34 2 30 4 19 4 22 4 .. .. .. .. 50 6 24 3 35 8",
    "14": "51 2 34 8 42 4 39 3 21 8 27 3 .. .. .. .. 54 0 26 7 33 3",
    "15": "52 8 37 6 44 0 53 8 27 10 33 2 .. .. .. .. 66 8 32 0 45 5",
    "16 and over": "90 6 46 8 70 3 43 3 23 9 28 4 .. .. 10 6 85 6 39 8 58 0",
    "Unspecified": "16 6 15 0 15 6 11 6 10 2 10 5 .. .. .. .. 17 11 9 6 13 0",
    "All Private Dwellings": "13 9 8 8 10 7 12 6 7 0 8 2 3 11 7 6 14 5 8 4 10 9",
}
PDF_LEFT_62_THIRTEEN = "4 6 2 0 3 1 3 8 1 9 2 8 2 10 2 0 2 4 3 10 1 10 3 0"
PDF_LEFT_63 = {
    # PDF p.128 rows 5–6: rule fragments/missing units shifted the later
    # state pairs, despite every candidate being numerically nonnegative.
    "5": "2 8 1 10 2 2 2 7 1 7 2 1 2 3 1 8 1 11 2 9 1 7 2 2",
    "6": "3 1 1 11 2 5 2 11 1 9 2 3 2 5 1 10 2 1 3 1 1 9 2 4",
    "9": "5 1 2 6 3 7 4 7 2 3 3 4 3 11 2 4 2 8 4 7 2 2 3 5",
    "11": "6 5 3 0 4 4 6 1 2 8 4 2 4 8 2 9 3 2 5 11 2 6 4 5",
    "13": "8 2 3 4 5 3 7 3 3 3 5 1 5 7 3 2 4 0 7 0 3 6 5 7",
    "16 and over": "11 5 4 2 6 4 12 0 4 5 7 7 7 5 2 4 3 0 11 8 3 8 8 1",
}
PDF_RIGHT_63_SIXTEEN = "11 1 3 9 6 10 7 0 3 1 4 1 .. .. 1 4 11 3 3 9 6 1"
PDF_RIGHT_63 = {
    # PDF p.129 rows 12 and 14: vertical rules entered the currency stream.
    "12": "6 5 3 7 4 9 4 9 3 0 3 7 .. .. .. .. 6 9 3 0 4 5",
    "14": "7 5 4 3 5 6 6 5 3 0 3 10 .. .. .. .. 7 9 3 4 5 1",
}
PDF_RIGHT_62_NINE = "3 5|2 5|2 11|2 3|1 7|1 10|..|1 1|3 1|1 8|2 3"


def assign_state_table(page: int, y: float, fallback: int) -> int:
    """Use the actual horizontal printed table boundaries, not candidate IDs."""
    if page in (126, 127):
        return 59 if y < 370 else 60 if y < 610 else 61
    if page in (128, 129):
        return 62 if y < 565 else 63
    return fallback


def _units(value: str) -> tuple[str, str]:
    """Split only clearly transcribed shillings/pence, preserving source strings."""
    value = value.strip()
    match = re.fullmatch(r"(\d+)\s*s\.?\s*(\d+)\s*d\.?", value, re.I)
    if not match:
        match = re.fullmatch(r"(\d+)\s+(\d+)", value)
    if match:
        return match.group(1), match.group(2)
    if value in ("", ".", "..", "...", "—", "-"):
        return value, ""
    return value, ""


def _columns(number: int, row: dict) -> list[str]:
    """Restore explicit OCR column shifts without manufacturing missing cells."""
    page, y = row["page"], row["y"]
    values = [cell["value"].strip() for _, cell in sorted(row["cells"].items())]
    if number == 59 and page == 126 and 260 < y < 282 and len(values) == 13:
        # The left-edge vertical rule was captured as an additional '..' cell.
        values = values[1:]
    if number == 60 and page == 126 and 495 < y < 535:
        # Printed row 11 onwards begins with two OCR rule fragments.  Further
        # isolated 'I' marks are the internal rules between state blocks.
        values = values[2:]
        if 502 < y < 508:
            values = [value for index, value in enumerate(values) if index != 3]
        elif 515 < y < 521:
            values = [value for index, value in enumerate(values)
                      if index not in (2, 4, 8, 12)]
        elif 527 < y < 533:
            values = [value for index, value in enumerate(values)
                      if index not in (5, 10)]
            values[3] = ".403"  # PDF decimal point dropped from Victoria's entry
    if number == 61 and page == 126 and 770 < y < 778 and len(values) == 22:
        # The PDF prints 90s. 8d. for Melbourne in the 16-and-over row;
        # cells.csv omitted this entire pair between NSW and Victoria.
        values[6:6] = ["90", "8"]
    if number == 61 and page == 126 and 778 < y < 784 and len(values) == 24:
        values[2] = "10"  # PDF prints 10s. 6d., candidate reads '.10'
    if number == 62 and page == 128 and 360 < y < 410 and len(values) == 13:
        values = values[1:]  # extra left-edge '..' before the 12 combined amounts
    if number == 62 and page == 129 and 315 < y < 380 and len(values) == 11:
        # PDF p.129: the combined Perth amounts were OCR'd pence-first
        # on rows 2–8 and 10–12. Row 9 has its separate source recovery.
        if not 358 < y < 364:
            shillings, pence = _units(values[0])
            values[0] = f"{pence} {shillings}"
    if number == 62 and page == 129 and 383 < y < 410 and len(values) == 21:
        # Final cell is the printed right-hand row label, not a currency unit.
        # Federal Territory is absent only on rows 13–15; row 16 prints
        # 6s. 0d. and instead lost the final Commonwealth 3s. 0d. pair.
        values = values[:-1]
        if y < 401:
            values[14:14] = ["", ""]
        else:
            values.extend(["3", "0"])
    if number == 63 and page == 129 and 742 < y < 750 and len(values) == 21:
        # Room 11: Northern Territory pence is not captured; the remaining
        # columns, including all three Commonwealth totals, are present.
        values[13:13] = [""]
    if number == 63 and page == 129 and 755 < y < 774:
        if len(values) == 20:
            # Rooms 13 and 15: Federal Territory is entirely absent.
            values[14:14] = ["", ""]
        elif len(values) == 21:
            # Room 14: the Commonwealth total pence was not transcribed.
            values.append("")
    if number == 63 and page == 128 and 720 < y < 730 and len(values) == 28:
        # The extractor repeated two consecutive currency pairs in room row 7.
        values = values[:12] + values[16:]
        values[16] = "2"  # PDF prints 2s. 4d.; candidate captured 1s. 4d.
    if number == 63 and page == 128 and 770 < y < 780 and len(values) == 25:
        values = values[:4] + values[5:]  # stray OCR '1' before NSW whole state
    if number == 63 and page == 129 and 775 < y < 785 and len(values) == 23:
        values = [value for index, value in enumerate(values) if index != 13]
    if number == 63 and page == 129 and 790 < y < 800 and len(values) == 23:
        values = [value for index, value in enumerate(values) if index != 10]
    return values


def assemble_state_panels(
    number: int, source_rows: list[dict], schema: tuple[list[str], list[str], str]
) -> tuple[list[str], list[list[str]]]:
    """Return source-row labels and individually assigned state/area values."""
    if number not in (59, 60, 61, 62, 63):
        raise ValueError(f"Not a state-area panel: {number}")
    dimension_fields, data_fields, row_field = schema
    headers = dimension_fields + data_fields
    if dimension_fields != ["number_of_rooms"] or row_field != "number_of_rooms":
        raise ValueError("Unexpected state-area table dimensions")
    expected = [f"{area}_{unit}" for area in LEFT_AREAS + RIGHT_AREAS
                for unit in ("shillings", "pence")] if number >= 61 else list(LEFT_AREAS + RIGHT_AREAS)
    if data_fields != expected:
        raise ValueError("Unexpected state-area table column order")

    grouped: dict[str, dict] = {}
    for row in sorted(source_rows, key=lambda item: (item["page"], item["y"], item["row_id"])):
        page, y = row["page"], row["y"]
        if assign_state_table(page, y, number) != number or not row["cells"]:
            continue
        # Candidate fragments of Table 59 were captured beneath the actual
        # right-hand Table 61 panel.  They are decimals, not rental amounts.
        if number == 61 and page == 127 and y >= 750:
            continue
        if number == 59 and page == 127 and y < 100:
            continue  # top-margin duplication of the first printed row
        if number == 62 and page == 128 and y > 420:
            continue  # repeated total row, seven points below the printed one

        label = (row["label"] or row["resolved"]).strip()
        if number == 62 and page == 129 and 383 < y < 410:
            # The last OCR cell is the printed right-hand row label.
            if y < 390:
                label = "13"
            elif y < 395:
                label = "14"
            elif y < 401:
                label = "15"
            else:
                label = "16 and over"
        if not label and number in (60, 61) and page == 126 and y > 540:
            label = "All Private Dwellings"
        if not label:
            continue
        areas = LEFT_AREAS if page in (126, 128) else RIGHT_AREAS
        values = _columns(number, row)
        target = grouped.setdefault(label, {"order": (page, y), "values": {}})
        target["order"] = min(target["order"], (page, y))
        fields = target["values"]
        if number <= 60:
            for area, value in zip(areas, values):
                fields.setdefault(area, value)
        elif len(values) <= len(areas) + 1 and any(re.search(r"\d\s+\d", value) for value in values):
            # A later source batch captured whole s. d. amounts per column.
            for area, value in zip(areas, values):
                shillings, pence = _units(value)
                fields.setdefault(f"{area}_shillings", shillings)
                if pence:
                    fields.setdefault(f"{area}_pence", pence)
        else:
            # Other batches capture separate s. and d. cells in print order.
            for field, value in zip((f"{area}_{unit}" for area in areas
                                     for unit in ("shillings", "pence")), values):
                fields.setdefault(field, value)
    # Fill only values directly readable on the PDF but not present in the
    # candidate transcription. These are printed panels, never imputed totals.
    if number == 59:
        for label, printed in PDF_RIGHT_59.items():
            if label in grouped:
                grouped[label]["values"].update(zip(RIGHT_AREAS, printed.split()))
    elif number == 60:
        if "11" in grouped:
            # PDF p.127 y=496, Western Australia whole state: .625, not .525.
            grouped["11"]["values"]["western_australia_whole_state"] = ".625"
    elif number == 61:
        # Direct PDF readings, p.126 rows 3/14 and p.127 rows 2/4.
        for label, field, value in (
            ("3", "queensland_remainder_of_state_pence", "6"),
            ("14", "queensland_brisbane_and_suburbs_pence", "9"),
            ("2", "northern_territory_shillings", "3"),
            ("4", "northern_territory_shillings", "7"),
            ("4", "northern_territory_pence", "11"),
            ("4", "federal_territory_shillings", "5"),
            ("4", "federal_territory_pence", "0"),
        ):
            if label in grouped:
                grouped[label]["values"][field] = value
        for label, printed in PDF_RIGHT_61.items():
            if label in grouped:
                areas = (f"{area}_{unit}" for area in RIGHT_AREAS
                         for unit in ("shillings", "pence"))
                grouped[label]["values"].update(zip(areas, printed.split()))
        # Page 127 row 12's last pence cell is truncated by the candidate OCR.
        if "12" in grouped:
            grouped["12"]["values"]["commonwealth_whole_commonwealth_pence"] = "1"
    elif number == 62:
        # PDF p.128 rows 1, 9, 15 and p.129 row 7: explicit digit/unit reads.
        for label, field, value in (
            ("1", "new_south_wales_remainder_of_state_pence", "11"),
            ("9", "queensland_whole_state_shillings", "1"),
            ("9", "queensland_whole_state_pence", "11"),
            ("15", "queensland_brisbane_and_suburbs_shillings", "4"),
            ("15", "queensland_brisbane_and_suburbs_pence", "1"),
            ("7", "western_australia_perth_and_suburbs_shillings", "3"),
            ("7", "western_australia_perth_and_suburbs_pence", "1"),
        ):
            if label in grouped:
                grouped[label]["values"][field] = value
        if "9" in grouped:
            # The source dropped the Commonwealth metropolitan amount, then
            # captured the printed right-edge room number as its final cell.
            fields = grouped["9"]["values"]
            for area, amount in zip(RIGHT_AREAS, PDF_RIGHT_62_NINE.split("|")):
                shillings, pence = _units(amount)
                fields[f"{area}_shillings"] = shillings
                fields[f"{area}_pence"] = pence
        if "13" in grouped:
            # The left batch omitted Queensland remainder (2s. 0d.), shifting
            # its remaining combined amounts one geography to the left.
            fields = grouped["13"]["values"]
            areas = (f"{area}_{unit}" for area in LEFT_AREAS
                     for unit in ("shillings", "pence"))
            fields.update(zip(areas, PDF_LEFT_62_THIRTEEN.split()))
        # PDF p.129, upper panel: each dot pair spans both currency units.
        # NT rows 9 and 11–16 and FT rows 12–15 are printed as unavailable.
        for label in ("9", "11", "12", "13", "14", "15", "16 and over"):
            if label in grouped:
                fields = grouped[label]["values"]
                fields["northern_territory_shillings"] = ".."
                fields["northern_territory_pence"] = ".."
                if label in ("12", "13", "14", "15"):
                    fields["federal_territory_shillings"] = ".."
                    fields["federal_territory_pence"] = ".."
        if "16 and over" in grouped:
            # The Federal Territory cell is 6s. 0d., not a missing pair.
            grouped["16 and over"]["values"]["federal_territory_shillings"] = "6"
            grouped["16 and over"]["values"]["federal_territory_pence"] = "0"
        if "All Private Dwellings" in grouped:
            # Page 129 prints 2s. 1d.; the candidate ends after the shillings.
            grouped["All Private Dwellings"]["values"]["commonwealth_whole_commonwealth_pence"] = "1"
    elif number == 63:
        for label, printed in PDF_LEFT_63.items():
            if label in grouped:
                areas = (f"{area}_{unit}" for area in LEFT_AREAS
                         for unit in ("shillings", "pence"))
                grouped[label]["values"].update(zip(areas, printed.split()))
        # Direct PDF readings: p.128 rows 4/8/12, p.129 rows 3/7.
        for label, field, value in (
            ("4", "queensland_brisbane_and_suburbs_pence", "1"),
            ("8", "south_australia_whole_state_pence", "0"),
            ("12", "south_australia_whole_state_pence", "8"),
            ("3", "northern_territory_pence", "5"),
            ("3", "commonwealth_remainder_of_commonwealth_pence", "6"),
            ("7", "northern_territory_shillings", "3"),
        ):
            if label in grouped:
                grouped[label]["values"][field] = value
        for label, printed in PDF_RIGHT_63.items():
            if label in grouped:
                areas = (f"{area}_{unit}" for area in RIGHT_AREAS
                         for unit in ("shillings", "pence"))
                grouped[label]["values"].update(zip(areas, printed.split()))
        if "16 and over" in grouped:
            areas = (f"{area}_{unit}" for area in RIGHT_AREAS
                     for unit in ("shillings", "pence"))
            grouped["16 and over"]["values"].update(
                zip(areas, PDF_RIGHT_63_SIXTEEN.split())
            )
        # PDF p.129, lower panel: NT is unavailable on rows 11–16;
        # FT is unavailable on 12–15 (11 and 16 retain their printed amounts).
        for label in ("11", "12", "13", "14", "15", "16 and over"):
            if label in grouped:
                fields = grouped[label]["values"]
                fields["northern_territory_shillings"] = ".."
                fields["northern_territory_pence"] = ".."
                if label in ("12", "13", "14", "15"):
                    fields["federal_territory_shillings"] = ".."
                    fields["federal_territory_pence"] = ".."
        if "14" in grouped:
            # Page 129 prints 5s. 1d.; the candidate omits the final 1d.
            grouped["14"]["values"]["commonwealth_whole_commonwealth_pence"] = "1"

    def printed_order(item: tuple[str, dict]) -> tuple[int, float]:
        label, entry = item
        if label.isdecimal():
            return int(label), entry["order"][1]
        if label == "16 and over":
            return 16, entry["order"][1]
        if label == "Unspecified":
            return 17, entry["order"][1]
        if label == "All Private Dwellings":
            return 18, entry["order"][1]
        return 19, entry["order"][1]

    return headers, [[label] + [entry["values"].get(field, "") for field in data_fields]
                     for label, entry in sorted(grouped.items(), key=printed_order)]
