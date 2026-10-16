"""Join the left and right printed panels of Dwellings tables 10–29.

The source-region column index starts at one again on each facing page.  The
printed column heading, not that local index, determines the destination.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import median

import pymupdf


_EMPTY = {"", ".", "..", "...", "·", "··", "···", "-", "—"}
_CLASSES = ("Private Dwellings", "Dwellings Other Than Private", "All Dwellings")
_DWELLING_LABELS = {
    "caretaker": "Caretaker's Quarters in Store, Offices, etc.",
    "coffee palace": "Boarding House, Lodging House, Coffee Palace",
    "religious institution": "Religious Institution (non-Educational)",
    "charitable institution": "Charitable Institution (other than Hospital)",
    "military and naval": "Military and Naval Establishment",
}


def _text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.replace("’", "'").replace("·", "-")).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _category(value: str) -> str:
    text = _text(value)
    if text in ("total", "totals"):
        return "total"
    if text.startswith("bushes rushes"):
        return "bushes rushes"
    if text.startswith("ruberoid") or text.startswith("r uberoid"):
        return "ruberoid"
    if text.startswith("pise") or text.startswith("pis") and len(text) < 7:
        return "pise"
    if text.startswith("aboriginal camps") or text == "living":
        return "aboriginal camps"
    # Hospital and charitable institution are separate printed categories.
    if text.startswith("other camps without dwellings"):
        return "other camps without dwellings"
    if text == "palace" or "coffee palace" in text:
        return "coffee palace"
    for stem in ("private house", "tenement in private house", "caretaker",
                 "educational institution", "religious institution",
                 "charitable institution", "military and naval"):
        if text.startswith(stem):
            return stem
    if text.startswith("half castes were living"):
        return "aboriginal camps"
    return text


def _context(markers: list[tuple[float, str]], y: float) -> str:
    result = ""
    for start, name in sorted(markers):
        if start > y:
            break
        result = name
    return result


def _class(number: int, page: int, y: float, panels: dict[int, list[tuple[float, str]]]) -> str:
    if number <= 11:
        return ""
    own = panels.get(page, [])
    # PDF page 22 loses the first two class headings in text extraction;
    # its facing page prints the same three section boundaries.
    facing = panels.get(page + (1 if page % 2 == 0 else -1), [])
    if len({name for _, name in own}) < 3 and len({name for _, name in facing}) >= 3:
        own = facing
    # On a shared page, PDF text sometimes omits the final section heading
    # on one side although its mate still prints it at the same height.
    if facing and (not own or facing[-1][0] > own[-1][0] + 20) and y >= facing[-1][0]:
        own = facing
    value = _context(own, y)
    if not value and own and own[0][1] != _CLASSES[0] and facing:
        value = _context(facing, y)
    return value or (_CLASSES[0] if own and own[0][1] == _CLASSES[0] else "")


def _state(page: int, y: float, states: dict[int, list[tuple[float, str]]]) -> str:
    value = _context(states.get(page, []), y)
    if value:
        return value
    facing = page + (1 if page % 2 == 0 else -1)
    return _context(states.get(facing, []), y)


_MATERIAL_LABELS = {
    "stone": "Stone", "brick": "Brick", "concrete": "Concrete", "iron": "Iron",
    "wood": "Wood", "sun dried bricks": "Sun-dried Bricks", "pise": "Pisé",
    "lath and plaster": "Lath and Plaster", "wattle and dab": "Wattle and Dab",
    "bark": "Bark", "bushes rushes": "Bushes, Rushes, Spinifex, etc.",
    "calico canvas hessian": "Calico, Canvas, Hessian",
    "ruberoid": "Ruberoid & other Compositions", "unspecified": "Unspecified",
    "wagons trains etc": "Wagons, Trains, etc.",
    "aboriginal camps": "Aboriginal Camps in which Whites or Half-castes were Living",
    "other camps without dwellings": "Other Camps without Dwellings", "total": "Total",
}


# Image-read recoveries: table, physical PDF page, approximate y in points,
# printed row identity, and fields. No value is obtained from a residual.
# p23's printed All/Wood total 199,653 is deliberately retained, not balanced.
_SOURCE_READS = (
    (11, 18, 217, ("Victoria", "educational institution"), {"rooms_4": "1", "rooms_5": "1", "rooms_6": "5", "rooms_7": "8", "rooms_8": "6", "rooms_9": "6", "rooms_10": "6", "rooms_11": "13"}),
    (11, 19, 226, ("Victoria", "religious institution"), {"rooms_20_and_over": "10", "rooms_unspecified": ".."}),
    (11, 19, 282, ("Victoria", "police station and quarters"), {"rooms_unspecified": "3", "rooms_total": "318"}),
    (11, 18, 298, ("Victoria", "unspecified"), {"rooms_1": "1"}),
    (11, 18, 486, ("Queensland", "penal establishment"), {"rooms_9": "2"}),
    (11, 19, 495, ("Queensland", "military and naval"), {"rooms_13": "1", "rooms_total": "7"}),
    (11, 19, 503, ("Queensland", "police barracks"), {"rooms_12": "1", "rooms_18": "1", "rooms_total": "23"}),
    (11, 19, 511, ("Queensland", "police station and quarters"), {"rooms_12": "1"}),
    (11, 19, 519, ("Queensland", "fire station"), {"rooms_12": "1"}),
    (11, 18, 526, ("Queensland", "unspecified"), {"rooms_1": "2", "rooms_2": "2", "rooms_3": "3"}),
    (11, 19, 527, ("Queensland", "unspecified"), {"rooms_unspecified": "74"}),
    (11, 19, 750, ("South Australia", "unspecified"), {"rooms_20_and_over": "5", "rooms_unspecified": "26", "rooms_total": "50"}),
    (11, 18, 750, ("South Australia", "unspecified"), {"rooms_3": "..", "rooms_6": "1"}),
    (11, 18, 790, ("South Australia", "total"), {"rooms_7": "6,530"}),
    (11, 20, 261, ("Western Australia", "penal establishment"), {"rooms_5": "2"}),
    (11, 21, 450, ("Tasmania", "hospital"), {"rooms_20_and_over": "6", "rooms_unspecified": "1"}),
    (11, 21, 507, ("Tasmania", "unspecified"), {"rooms_14": "2"}),
    (11, 20, 533, ("Tasmania", "total"), {"rooms_11": "254"}),
    (11, 21, 577, ("Northern Territory", "private house"), {"rooms_total": "1,194"}),
    (12, 23, 346, ("ruberoid", "Private Dwellings"), {"rooms_12": "1", "rooms_17": "1", "rooms_18": ".."}),
    (12, 23, 354, ("unspecified", "Private Dwellings"), {"rooms_12": "4", "rooms_13": "..", "rooms_14": "1", "rooms_15": "1", "rooms_16": "2", "rooms_17": "2", "rooms_18": "1", "rooms_19": "..", "rooms_20_and_over": "2", "rooms_unspecified": "2,881", "rooms_total": "4,643"}),
    (12, 23, 517, ("ruberoid", "Dwellings Other Than Private"), {"rooms_total": "6"}),
    (12, 23, 573, ("total", "Dwellings Other Than Private"), {"rooms_total": "29,870"}),
    (12, 23, 624, ("stone", "All Dwellings"), {"rooms_12": "881"}),
    (12, 23, 656, ("wood", "All Dwellings"), {"rooms_14": "933"}),
    (12, 22, 688, ("wattle and dab", "All Dwellings"), {"rooms_3": "167"}),
    (12, 23, 720, ("ruberoid", "All Dwellings"), {"rooms_12": "1", "rooms_20_and_over": "2"}),
    (12, 23, 728, ("unspecified", "All Dwellings"), {"rooms_12": "11", "rooms_13": "3", "rooms_14": "2", "rooms_15": "1", "rooms_16": "6", "rooms_17": "4", "rooms_18": "2", "rooms_19": ".."}),
    (14, 27, 366, ("calico canvas hessian", "Private Dwellings"), {"rooms_unspecified": "1"}),
    (14, 27, 382, ("unspecified", "Private Dwellings"), {"rooms_17": "1"}),
    (14, 27, 723, ("ruberoid", "All Dwellings"), {"rooms_total": "42"}),
    (14, 27, 651, ("iron", "All Dwellings"), {"rooms_unspecified": "11"}),
    (15, 28, 300, ("wood", "Private Dwellings"), {"rooms_5": "22,749"}),
    (15, 29, 313, ("pise", "Private Dwellings"), {"rooms_15": "2", "rooms_16": "1", "rooms_17": "1"}),
    (16, 31, 306, ("wood", "Private Dwellings"), {"rooms_12": "5", "rooms_13": "1", "rooms_14": "1", "rooms_15": "1", "rooms_16": "1"}),
    (18, 35, 273, ("ruberoid", "Private Dwellings"), {"rooms_17": "1"}),
    (18, 35, 281, ("unspecified", "Private Dwellings"), {"rooms_14": "1", "rooms_16": "..", "rooms_unspecified": "289", "rooms_total": "379"}),
    (18, 35, 297, ("total", "Private Dwellings"), {"rooms_unspecified": "382"}),
    (19, 35, 801, ("total", "Private Dwellings"), {"rooms_unspecified": "6", "rooms_total": "1,194"}),
    (19, 36, 297, ("iron", "All Dwellings"), {"rooms_6": "17"}),
    (19, 37, 385, ("total", "All Dwellings"), {"rooms_unspecified": "29", "rooms_total": "1,248"}),
    (20, 37, 759, ("calico canvas hessian", "All Dwellings"), {"rooms_total": "136"}),
    (21, 39, 696, ("ruberoid", "All Dwellings"), {"inmates_total": "343"}),
    (22, 40, 281, ("concrete", "Private Dwellings"), {"inmates_3": "112"}),
    (22, 40, 637, ("concrete", "All Dwellings"), {"inmates_4": "137"}),
    (22, 40, 669, ("pise", "All Dwellings"), {"inmates_8": "149", "inmates_9": "109", "inmates_10": "64", "inmates_11": "56"}),
    (22, 40, 701, ("bushes rushes", "All Dwellings"), {"inmates_9": ".."}),
    (23, 42, 332, ("wattle and dab", "Private Dwellings"), {"inmates_3": "39"}),
    (23, 42, 276, ("brick", "Private Dwellings"), {"inmates_4": "12,377"}),
    (23, 42, 688, ("wattle and dab", "All Dwellings"), {"inmates_5": "39"}),
    (23, 42, 696, ("bark", "All Dwellings"), {"inmates_1": "388"}),
    (24, 44, 286, ("concrete", "Private Dwellings"), {"inmates_7": "3"}),
    (24, 44, 326, ("lath and plaster", "Private Dwellings"), {"inmates_11": "1"}),
    (24, 44, 334, ("wattle and dab", "Private Dwellings"), {"inmates_8": ".."}),
    (25, 46, 436, ("brick", "Dwellings Other Than Private"), {"inmates_1": "..", "inmates_2": "8", "inmates_3": "5", "inmates_4": "15", "inmates_5": "24", "inmates_6": "14", "inmates_7": "22", "inmates_8": "26", "inmates_9": "23", "inmates_10": "23", "inmates_11": "16"}),
    (26, 49, 376, ("unspecified", "Private Dwellings"), {"inmates_19": "..", "inmates_20_and_over": "1"}),
    (26, 48, 624, ("stone", "All Dwellings"), {"inmates_1": "411", "inmates_2": "477"}),
    (26, 49, 780, ("total", "All Dwellings"), {"inmates_14": "144"}),
    (26, 48, 776, ("total", "All Dwellings"), {"inmates_10": "904"}),
    (27, 51, 289, ("ruberoid", "Private Dwellings"), {"inmates_total": "6"}),
    (28, 53, 299, ("iron", "All Dwellings"), {"inmates_12": "1", "inmates_13": "1", "inmates_14": "..", "inmates_15": "2", "inmates_16": "1", "inmates_17": "1", "inmates_18": "..", "inmates_19": "1", "inmates_20_and_over": "1", "inmates_total": "528"}),
    (28, 53, 307, ("wood", "All Dwellings"), {"inmates_total": "191"}),
    (28, 53, 323, ("bark", "All Dwellings"), {"inmates_total": "175"}),
    (28, 53, 331, ("bushes rushes", "All Dwellings"), {"inmates_total": "179"}),
    (28, 53, 339, ("calico canvas hessian", "All Dwellings"), {"inmates_total": "93"}),
    (28, 53, 347, ("unspecified", "All Dwellings"), {"inmates_total": "12"}),
    (29, 52, 511, ("iron", "Private Dwellings"), {"inmates_1": "..", "inmates_2": "1", "inmates_3": "1", "inmates_8": "..", "inmates_9": ".."}),
    (29, 52, 772, ("unspecified", "All Dwellings"), {"inmates_3": "3"}),
    (13, 24, 481, ("pise", "Dwellings Other Than Private"), {"rooms_11": "3"}),
    (13, 24, 513, ("calico canvas hessian", "Dwellings Other Than Private"), {"rooms_11": "1"}),
    (14, 27, 302, ("iron", "Private Dwellings"), {"rooms_13": "2"}),
    (17, 33, 487, ("sun dried bricks", "Dwellings Other Than Private"), {"rooms_17": "1"}),
    (18, 35, 353, ("concrete", "Dwellings Other Than Private"), {"rooms_12": "1", "rooms_13": "..", "rooms_14": "..", "rooms_15": "..", "rooms_16": "..", "rooms_17": "..", "rooms_18": "..", "rooms_19": "..", "rooms_20_and_over": "5", "rooms_unspecified": "..", "rooms_total": "11"}),
    (18, 34, 497, ("sun dried bricks", "All Dwellings"), {"rooms_7": "2"}),
    (18, 34, 505, ("lath and plaster", "All Dwellings"), {"rooms_11": "1"}),
    (19, 36, 305, ("wood", "All Dwellings"), {"rooms_8": "2", "rooms_9": "1"}),
    (20, 37, 489, ("brick", "Private Dwellings"), {"rooms_20_and_over": "1"}),
    (20, 37, 609, ("stone", "Dwellings Other Than Private"), {"rooms_20_and_over": "1"}),
    (20, 36, 633, ("wood", "Dwellings Other Than Private"), {"rooms_5": "1", "rooms_6": "1"}),
    (20, 37, 636, ("wood", "Dwellings Other Than Private"), {"rooms_13": "2", "rooms_14": ".."}),
    (20, 36, 736.8, ("sun dried bricks", "All Dwellings"), {"rooms_3": "1"}),
    (21, 39, 696, ("ruberoid", "All Dwellings"), {"inmates_12": "3", "inmates_14": "1", "inmates_15": "1", "inmates_16": "1", "inmates_20_and_over": ".."}),
    (22, 40, 479, ("pise", "Dwellings Other Than Private"), {"inmates_10": "1", "inmates_11": "3"}),
    (22, 40, 511, ("calico canvas hessian", "Dwellings Other Than Private"), {"inmates_7": "4", "inmates_8": "38", "inmates_9": "..", "inmates_10": "4", "inmates_11": "2"}),
    (23, 42, 463, ("concrete", "Dwellings Other Than Private"), {"inmates_2": "1", "inmates_4": "4"}),
    (23, 42, 471, ("iron", "Dwellings Other Than Private"), {"inmates_9": "2", "inmates_10": "1", "inmates_11": "6"}),
    (23, 42, 528, ("wagons trains etc", "Dwellings Other Than Private"), {"inmates_11": "1"}),
    (23, 42, 736, ("wagons trains etc", "All Dwellings"), {"inmates_8": "3", "inmates_9": "..", "inmates_10": ".."}),
    (24, 45, 518, ("calico canvas hessian", "Dwellings Other Than Private"), {"inmates_13": "1", "inmates_14": "..", "inmates_15": "1", "inmates_16": "1", "inmates_17": "1"}),
    (25, 46, 468, ("sun dried bricks", "Dwellings Other Than Private"), {"inmates_5": "1"}),
    (25, 47, 806, ("other camps without dwellings", "All Dwellings"), {"inmates_20_and_over": "1"}),
    (26, 48, 672, ("pise", "All Dwellings"), {"inmates_4": "2"}),
    (27, 50, 371, ("concrete", "Dwellings Other Than Private"), {"inmates_11": "1"}),
    (27, 51, 478, ("concrete", "All Dwellings"), {"inmates_20_and_over": "2"}),
    (28, 50, 724, ("concrete", "Private Dwellings"), {"inmates_3": "1", "inmates_6": "..", "inmates_8": "1"}),
    (28, 52, 291, ("concrete", "All Dwellings"), {"inmates_3": "1"}),
    (28, 52, 315, ("pise", "All Dwellings"), {"inmates_2": "1", "inmates_8": "1", "inmates_10": ".."}),
    (29, 53, 496, ("brick", "Private Dwellings"), {"inmates_12": "1"}),
    (29, 53, 536, ("pise", "Private Dwellings"), {"inmates_12": "1"}),
    (29, 52, 764, ("calico canvas hessian", "All Dwellings"), {"inmates_6": "1", "inmates_7": "..", "inmates_8": "1", "inmates_9": "1", "inmates_11": ".."}),
    (11, 17, 707, ("New South Wales", "penal establishment"), {"rooms_17": ".."}),
    (11, 19, 414, ("Queensland", "caretaker"), {"rooms_19": ".."}),
    (11, 18, 502, ("Queensland", "police barracks"), {"rooms_11": ".."}),
    (11, 20, 651, ("Northern Territory", "penal establishment"), {"rooms_6": ".."}),
    (11, 20, 667, ("Northern Territory", "unspecified"), {"rooms_6": "..", "rooms_8": "..", "rooms_10": ".."}),
    (11, 20, 754, ("Federal Territory", "hotel"), {"rooms_8": ".."}),
    (11, 21, 753, ("Federal Territory", "hotel"), {"rooms_13": "1", "rooms_total": "1"}),
    (11, 20, 777, ("Federal Territory", "military and naval"), {"rooms_1": "2", "rooms_2": "1"}),
    (11, 21, 777, ("Federal Territory", "military and naval"), {"rooms_20_and_over": "1", "rooms_total": "4"}),
    (11, 20, 786, ("Federal Territory", "police station and quarters"), {"rooms_5": "1"}),
    (11, 21, 785, ("Federal Territory", "police station and quarters"), {"rooms_total": "1"}),
    (14, 27, 382, ("unspecified", "Private Dwellings"), {"rooms_12": "1"}),
    (16, 30, 324, ("pise", "Private Dwellings"), {"rooms_11": ".."}),
    (16, 30, 330, ("lath and plaster", "Private Dwellings"), {"rooms_11": ".."}),
    (17, 32, 631, ("concrete", "All Dwellings"), {"rooms_11": ".."}),
    (17, 32, 663, ("pise", "All Dwellings"), {"rooms_10": "..", "rooms_11": ".."}),
    (17, 32, 679, ("wattle and dab", "All Dwellings"), {"rooms_10": "..", "rooms_11": ".."}),
    (17, 32, 687, ("bark", "All Dwellings"), {"rooms_10": "..", "rooms_11": ".."}),
    (20, 36, 769, ("unspecified", "All Dwellings"), {"rooms_9": ".."}),
    (23, 43, 374, ("unspecified", "Private Dwellings"), {"inmates_total": "1,204"}),
    (24, 44, 497, ("pise", "Dwellings Other Than Private"), {"inmates_9": "..", "inmates_10": "..", "inmates_11": ".."}),
    (24, 44, 529, ("unspecified", "Dwellings Other Than Private"), {"inmates_10": "1"}),
    (24, 44, 537, ("wagons trains etc", "Dwellings Other Than Private"), {"inmates_10": "1"}),
    (26, 49, 319, ("pise", "Private Dwellings"), {"inmates_13": "..", "inmates_14": ".."}),
    (26, 48, 487, ("sun dried bricks", "Dwellings Other Than Private"), {"inmates_1": ".."}),
    (28, 52, 405, ("other camps without dwellings", "All Dwellings"), {"inmates_8": ".."}),
    (11, 18, 445, ("Queensland", "educational institution"), {"rooms_5": "1"}),
    (11, 19, 446, ("Queensland", "educational institution"), {"rooms_unspecified": ".."}),
    (11, 18, 510, ("Queensland", "police station and quarters"), {"rooms_8": "16", "rooms_9": "5"}),
    (11, 19, 510, ("Queensland", "police station and quarters"), {"rooms_20_and_over": ".."}),
    (11, 20, 595, ("Northern Territory", "hotel"), {"rooms_9": "2"}),
    (11, 21, 593, ("Northern Territory", "hotel"), {"rooms_14": "..", "rooms_15": "1", "rooms_unspecified": ".."}),
    (12, 22, 502, ("bushes rushes", "Dwellings Other Than Private"), {"rooms_2": "1", "rooms_7": "..", "rooms_11": ".."}),
    (12, 23, 728, ("unspecified", "All Dwellings"), {"rooms_unspecified": "3,174", "rooms_total": "5,010"}),
    (14, 26, 473, ("iron", "Dwellings Other Than Private"), {"rooms_2": "1", "rooms_4": "4", "rooms_5": "..", "rooms_8": "6"}),
    (14, 26, 514, ("ruberoid", "Dwellings Other Than Private"), {"rooms_6": "1", "rooms_7": ".."}),
    (14, 26, 522, ("unspecified", "Dwellings Other Than Private"), {"rooms_1": "..", "rooms_2": "1", "rooms_10": "1"}),
    (16, 31, 322, ("pise", "Private Dwellings"), {"rooms_12": "1"}),
    (16, 30, 330, ("lath and plaster", "Private Dwellings"), {"rooms_1": "4", "rooms_2": "12"}),
    (16, 30, 369, ("ruberoid", "Private Dwellings"), {"rooms_8": ".."}),
    (16, 31, 371, ("ruberoid", "Private Dwellings"), {"rooms_unspecified": "1"}),
    (16, 31, 362, ("unspecified", "Private Dwellings"), {"rooms_20_and_over": ".."}),
    (17, 33, 354, ("unspecified", "Private Dwellings"), {"rooms_12": ".."}),
    (17, 32, 719, ("unspecified", "All Dwellings"), {"rooms_8": "..", "rooms_10": "..", "rooms_12": "1"}),
    (18, 34, 186, ("stone", "Private Dwellings"), {"rooms_10": "97", "rooms_11": "41"}),
    (18, 34, 265, ("pise", "Private Dwellings"), {"rooms_2": ".."}),
    (19, 34, 690, ("iron", "Private Dwellings"), {"rooms_10": "1"}),
    (19, 35, 754, ("bushes rushes", "Private Dwellings"), {"rooms_total": "178"}),
    (19, 36, 313, ("pise", "All Dwellings"), {"rooms_4": "..", "rooms_5": ".."}),
    (20, 37, 617, ("brick", "Dwellings Other Than Private"), {"rooms_20_and_over": "..", "rooms_total": "1"}),
    (20, 37, 657, ("total", "Dwellings Other Than Private"), {"rooms_14": ".."}),
    (21, 38, 463, ("wattle and dab", "Dwellings Other Than Private"), {"inmates_4": "1"}),
    (21, 38, 352, ("total", "Private Dwellings"), {"inmates_8": "47,447"}),
    (22, 41, 301, ("sun dried bricks", "Private Dwellings"), {"inmates_17": ".."}),
    (22, 41, 342, ("bushes rushes", "Private Dwellings"), {"inmates_14": ".."}),
    (23, 43, 286, ("concrete", "Private Dwellings"), {"inmates_18": ".."}),
    (23, 42, 364, ("ruberoid", "Private Dwellings"), {"inmates_10": ".."}),
    (23, 43, 690, ("wattle and dab", "All Dwellings"), {"inmates_14": "1"}),
    (24, 44, 504, ("bark", "Dwellings Other Than Private"), {"inmates_5": ".."}),
    (24, 44, 512, ("bushes rushes", "Dwellings Other Than Private"), {"inmates_6": ".."}),
    (24, 44, 520, ("calico canvas hessian", "Dwellings Other Than Private"), {"inmates_6": "1", "inmates_9": "..", "inmates_10": ".."}),
    (24, 45, 518, ("calico canvas hessian", "Dwellings Other Than Private"), {"inmates_18": ".."}),
    (24, 45, 720, ("ruberoid", "All Dwellings"), {"inmates_14": ".."}),
    (24, 45, 760, ("aboriginal camps", "All Dwellings"), {"inmates_14": "..", "inmates_16": "..", "inmates_17": "1"}),
    (25, 46, 492, ("calico canvas hessian", "Dwellings Other Than Private"), {"inmates_8": ".."}),
    (26, 48, 672, ("pise", "All Dwellings"), {"inmates_3": ".."}),
    (28, 53, 167, ("stone", "Dwellings Other Than Private"), {"inmates_19": ".."}),
    (28, 52, 173, ("iron", "Dwellings Other Than Private"), {"inmates_11": "1"}),
    (28, 52, 237, ("total", "Dwellings Other Than Private"), {"inmates_7": ".."}),
    (29, 52, 528, ("sun dried bricks", "Private Dwellings"), {"inmates_4": ".."}),
    (29, 52, 552, ("calico canvas hessian", "Private Dwellings"), {"inmates_10": ".."}),
    (29, 52, 560, ("unspecified", "Private Dwellings"), {"inmates_2": "..", "inmates_4": ".."}),
    (29, 52, 646, ("calico canvas hessian", "Dwellings Other Than Private"), {"inmates_6": "1", "inmates_7": "..", "inmates_10": ".."}),
    (29, 52, 740, ("sun dried bricks", "All Dwellings"), {"inmates_4": ".."}),
    (29, 52, 772, ("unspecified", "All Dwellings"), {"inmates_5": ".."}),
    (29, 52, 724, ("iron", "All Dwellings"), {"inmates_1": "..", "inmates_8": "..", "inmates_9": ".."}),
    (16, 30, 677, ("lath and plaster", "All Dwellings"), {"rooms_10": ".."}),
    (17, 33, 298.8, ("iron", "Private Dwellings"), {"rooms_17": "1", "rooms_18": ".."}),
    (17, 33, 314.8, ("sun dried bricks", "Private Dwellings"), {"rooms_14": "2", "rooms_15": ".."}),
    (19, 34, 729.4, ("concrete", "Private Dwellings"), {"rooms_5": ".."}),
    (19, 34, 777.7, ("calico canvas hessian", "Private Dwellings"), {"rooms_3": ".."}),
    (19, 36, 305.0, ("wood", "All Dwellings"), {"rooms_11": ".."}),
    (20, 37, 506.4, ("iron", "Private Dwellings"), {"rooms_19": ".."}),
    (20, 37, 530.7, ("pise", "Private Dwellings"), {"rooms_19": ".."}),
    (20, 36, 548.6, ("calico canvas hessian", "Private Dwellings"), {"rooms_3": "..", "rooms_4": ".."}),
    (20, 37, 709.3, ("stone", "All Dwellings"), {"rooms_20_and_over": "1", "rooms_unspecified": "1"}),
    (21, 38, 447.6, ("pise", "Dwellings Other Than Private"), {"inmates_2": "3", "inmates_3": "4", "inmates_4": "1"}),
    (28, 50, 762.0, ("bushes rushes", "Private Dwellings"), {"inmates_7": "1", "inmates_8": ".."}),
    (20, 37, 481.9, ("stone", "Private Dwellings"), {"rooms_20_and_over": "..", "rooms_unspecified": "1"}),
    (27, 51, 200.8, ("stone", "Private Dwellings"), {"inmates_15": "UNREADABLE: missing printed glyph"}),
    (28, 50, 753.8, ("bark", "Private Dwellings"), {"inmates_7": "1", "inmates_8": ".."}),
)

# Additional complete printed vectors, independently read at 3–5× from the
# unchanged PDF. Page parity fixes the half-panel; y records source provenance.
_SOURCE_PANEL_READS = (
    (11, 19, 338.6, ("Victoria", "total"), "1,839 893 906 551 426 290 244 136 1,505 1,478 272,683"),
    (11, 19, 567.1, ("Queensland", "total"), "723 332 389 233 216 131 115 94 927 828 125,836"),
    (11, 18, 725.3, ("South Australia", "police barracks"), ".. .. .. .. .. .. .. .. .. .. .."),
    (11, 21, 698.6, ("Northern Territory", "total"), ".. 1 .. 1 1 .. .. .. 3 29 1,248"),
    (11, 20, 802.3, ("Federal Territory", "total"), "138 26 19 60 60 50 30 20 7 8 6"),
    (14, 26, 403.9, ("total", "Private Dwellings"), "9,679 9,429 18,054 61,913 58,107 48,927 26,452 14,307 6,688 4,115 1,595"),
    (14, 26, 577.6, ("total", "Dwellings Other Than Private"), "62 60 80 173 424 769 824 860 712 656 529"),
    (15, 29, 361.7, ("ruberoid", "Private Dwellings"), ".. .. .. .. .. .. .. .. .. .. 81"),
    (15, 29, 369.6, ("unspecified", "Private Dwellings"), "1 .. .. .. .. .. 1 .. 1 352 663"),
    (16, 30, 487.2, ("sun dried bricks", "Dwellings Other Than Private"), ".. .. .. 1 .. 1 .. .. .. .. .."),
    (16, 30, 495.1, ("lath and plaster", "Dwellings Other Than Private"), ".. .. .. 1 .. .. .. .. .. .. .."),
    (16, 30, 572.4, ("total", "Dwellings Other Than Private"), "10 19 17 82 146 219 166 151 111 96 81"),
    (16, 30, 519.6, ("unspecified", "Dwellings Other Than Private"), "1 .. .. .. 1 .. .. .. .. .. .."),
    (18, 35, 336.1, ("stone", "Dwellings Other Than Private"), "15 5 5 5 9 5 6 3 21 1 149"),
    (18, 35, 360.6, ("iron", "Dwellings Other Than Private"), "1 1 1 .. .. .. .. .. 5 .. 15"),
    (18, 34, 375.7, ("lath and plaster", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. .. .. .."),
    (19, 34, 769.5, ("bushes rushes", "Private Dwellings"), "148 27 2 1 .. .. .. .. .. .. .."),
    (20, 36, 524.6, ("sun dried bricks", "Private Dwellings"), ".. .. 1 1 1 .. .. .. .. .. .."),
    (20, 36, 556.5, ("unspecified", "Private Dwellings"), ".. .. .. .. .. .. .. .. .. .. .."),
    (20, 36, 572.6, ("total", "Private Dwellings"), "136 25 19 60 57 49 30 19 7 8 6"),
    (20, 36, 610.8, ("stone", "Dwellings Other Than Private"), ".. .. .. .. 1 .. .. .. .. .. .."),
    (20, 37, 608.8, ("stone", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. 1 .. 2"),
    (20, 36, 618.4, ("brick", "Dwellings Other Than Private"), ".. .. .. .. 1 .. .. .. .. .. .."),
    (20, 36, 626.6, ("iron", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. 1 .. .. .."),
    (20, 37, 624.7, ("iron", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. .. .. 1"),
    (20, 36, 659.0, ("total", "Dwellings Other Than Private"), "2 1 .. .. 3 1 .. 1 .. .. .."),
    (22, 40, 519.1, ("ruberoid", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. .. .. .."),
    (23, 42, 372.6, ("unspecified", "Private Dwellings"), "260 187 194 155 117 97 90 43 21 16 13"),
    (23, 43, 398.1, ("total", "Private Dwellings"), "1,215 624 284 167 73 50 41 22 44 263,634"),
    (23, 42, 776.0, ("total", "All Dwellings"), "22,869 34,744 42,063 43,736 39,199 30,699 22,347 14,638 9,339 5,332 3,066"),
    (24, 44, 488.4, ("sun dried bricks", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. .. .. .."),
    (25, 46, 475.7, ("lath and plaster", "Dwellings Other Than Private"), ".. .. .. .. .. 1 .. .. .. .. .."),
    (25, 46, 483.8, ("wattle and dab", "Dwellings Other Than Private"), ".. .. .. 1 .. .. .. .. .. .. .."),
    (26, 49, 327.4, ("lath and plaster", "Private Dwellings"), "1 1 1 .. .. .. .. .. .. 86"),
    (26, 48, 462.7, ("concrete", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. .. .. .."),
    (26, 48, 575.0, ("total", "Dwellings Other Than Private"), "139 128 155 156 178 147 144 160 124 125 103"),
    (27, 50, 392.9, ("lath and plaster", "Dwellings Other Than Private"), ".. .. .. .. .. .. 1 .. .. .. .."),
    (27, 50, 425.0, ("total", "Dwellings Other Than Private"), "24 43 83 81 89 93 102 88 55 64 50"),
    (28, 50, 745.9, ("pise", "Private Dwellings"), ".. 1 .. .. .. .. .. 1 .. .. .."),
    (28, 51, 776.2, ("unspecified", "Private Dwellings"), ".. .. .. .. .. .. .. .. .. 11"),
    (28, 50, 801.8, ("total", "Private Dwellings"), "679 189 108 75 50 27 29 10 8 5 4"),
    (29, 52, 629.7, ("iron", "Dwellings Other Than Private"), ".. .. .. 1 .. .. .. .. .. .. .."),
    (16, 30, 503.3, ("wattle and dab", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. 1 .. .. .."),
    (23, 43, 560.0, ("aboriginal camps", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. .. 1"),
    (23, 42, 759.9, ("aboriginal camps", "All Dwellings"), "1 .. .. .. .. .. .. .. .. .. .."),
    (23, 42, 800.2, ("other camps without dwellings", "All Dwellings"), "572 92 40 20 15 13 14 8 7 7 5"),
    (26, 48, 763.7, ("aboriginal camps", "All Dwellings"), "40 13 11 5 4 1 2 1 .. .. 1"),
    (26, 48, 800.4, ("other camps without dwellings", "All Dwellings"), "1,157 153 59 38 14 5 4 8 .. 2 .."),
    (27, 50, 409.0, ("wagons trains etc", "Dwellings Other Than Private"), "6 2 .. 1 1 .. .. .. .. .. .."),
    (28, 52, 188.6, ("bushes rushes", "Dwellings Other Than Private"), ".. .. .. .. .. .. .. .. .. .. .."),
    (29, 52, 802.5, ("other camps without dwellings", "All Dwellings"), "1 .. .. .. 1 .. .. .. .. .. .."),
    (11, 20, 532.5, ("Tasmania", "total"), "2,436 2,944 3,317 11,679 6,496 5,519 2,660 1,716 873 646 254"),
    (18, 34, 273.7, ("ruberoid", "Private Dwellings"), "2 1 .. 1 .. .. 1 .. .. .. .."),
    (18, 34, 343.8, ("brick", "Dwellings Other Than Private"), "1 .. 4 13 15 28 29 46 28 25 12"),
    (18, 35, 344.2, ("brick", "Dwellings Other Than Private"), "36 15 22 14 19 14 9 9 109 4 452"),
    (18, 34, 360.1, ("iron", "Dwellings Other Than Private"), "1 .. .. .. .. 1 2 2 1 .. .."),
    (18, 35, 377.0, ("lath and plaster", "Dwellings Other Than Private"), ".. .. 1 .. .. .. .. .. .. .. 1"),
)

# Every printed camp/wagon room vector on PDF pp16–37 was rendered and read.
# These rows have explicit dots in rooms1–20+, not blank/unreadable cells.
# The order is Wagons, Aboriginal Camps, Other Camps; None is not a row.
_ROOM_CAMP_TOTALS = {
    10: ("609", "191", "5,530"), 12: ("609", "191", "5,530"),
    13: ("250", "21", "1,865"), 14: ("145", "1", "812"),
    15: ("171", "50", "998"), 16: ("18", "18", "258"),
    17: ("15", "80", "1,449"), 18: ("10", None, "86"),
    19: (None, "21", "60"), 20: (None, None, "2"),
    "New South Wales": ("250", "21", "1,865"),
    "Victoria": ("145", "1", "812"), "Queensland": ("171", "50", "998"),
    "South Australia": ("18", "18", "258"),
    "Western Australia": ("15", "80", "1,449"), "Tasmania": ("10", None, "86"),
    "Northern Territory": (None, "21", "60"), "Federal Territory": (None, None, "2"),
}


def _printed_label(text: str) -> str:
    """Recognise category words, never numbers or section/header fragments."""
    normal = _category(text)
    aliases = {"conc rete": "concrete", "sun dried brick": "sun dried bricks",
               "slul dried bricks": "sun dried bricks", "briok": "brick",
               "unspeoified": "unspecified", "bushes rqshes": "bushes rushes"}
    for damaged, clean in aliases.items():
        if normal == damaged or normal.startswith(damaged + " "):
            normal = clean + normal[len(damaged):]
            break
    compact = normal.replace(" ", "").replace("'", "")
    if compact.startswith(("othercampswithoutdwell", "othetcampswithoutdwell",
                           "othercampwithoutdwell")):
        return _MATERIAL_LABELS["other camps without dwellings"]
    for category, label in _MATERIAL_LABELS.items():
        if normal == category or normal.startswith(category + " "):
            return label
    if normal == "hospital" and ")" in text:
        return ""
    for start in ("private house", "tenement in private house", "caretaker", "hotel",
                  "educational institution", "religious institution", "charitable institution",
                  "penal establishment", "military and naval", "police barracks",
                  "police station", "fire station", "hospital"):
        if normal.startswith(start):
            return text.strip(" .")
    if "coffee palace" in normal:
        return "Coffee Palace"
    return ""


@lru_cache(maxsize=38)
def _source_geometry(page: int) -> tuple[list[float], list[tuple], list[tuple[float, str]]]:
    """Read immutable PDF evidence, not candidate headings or arithmetic.

    Repeated right-aligned digit edges locate the printed columns even when
    the OCR header is damaged. Unique clean cells can recover lost readings.
    """
    path = Path(__file__).resolve().parents[1] / "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf"
    with pymupdf.open(path) as document:
        words = document[page - 1].get_text("words")
    count = 11 if page % 2 == 0 or page <= 37 else 10
    digits = [w for w in words if w[1] > 90 and re.fullmatch(r"\d[\d,]*", w[4])
              and (170 < w[2] < 520 if page % 2 == 0 else 35 < w[2] < 405)]
    clusters: list[list[float]] = []
    for x in sorted(w[2] for w in digits):
        if clusters and x - median(clusters[-1]) < 3:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    edges: list[float] = []
    for cluster in sorted(clusters, key=lambda group: (-len(group), median(group))):
        x = median(cluster)
        if all(abs(x - old) > 18 for old in edges):
            edges.append(x)
        if len(edges) == count:
            break
    edges.sort()
    # PDF p53's inmates18 column contains only dots, not a digit edge.
    # Its position is the printed grid gap between inmates17 and inmates19.
    while len(edges) < count and len(edges) > 1:
        index = max(range(len(edges) - 1), key=lambda i: edges[i + 1] - edges[i])
        if edges[index + 1] - edges[index] < 45:
            break
        edges.insert(index + 1, (edges[index] + edges[index + 1]) / 2)
    labels: list[tuple[float, str]] = []
    alphabetic = [w for w in words if re.search(r"[A-Za-z]", w[4])
                  and (w[0] < edges[0] - 15 if page % 2 == 0 else w[0] > edges[-1] + 4)]
    lines: list[list[tuple]] = []
    for word in sorted(alphabetic, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        y = (word[1] + word[3]) / 2
        if lines and abs(y - median((w[1] + w[3]) / 2 for w in lines[-1])) <= 2.5:
            lines[-1].append(word)
        else:
            lines.append([word])
    for line in lines:
        text = " ".join(w[4] for w in sorted(line, key=lambda w: w[0]))
        label = _printed_label(text)
        continuation = _text(text)
        current_y = median((w[1] + w[3]) / 2 for w in line)
        # Numeric vectors are on the final line of wrapped labels. A
        # recognised continuation is still not another printed category.
        if labels and (not label or _category(label) == _category(labels[-1][1])) and continuation.startswith(
                ("hospital", "etc", "half castes", "halfcastes", "whites or half",
                 "whites or", "castes were", "living", "ings")):
            previous_y, previous_label = labels[-1]
            if 0 < current_y - previous_y <= 18:
                labels[-1] = (current_y, previous_label)
                continue
        if label:
            labels.append((current_y, label))
    # Image-located labels that the PDF text layer entirely loses. Both
    # facing leaves were read; these are printed identities, not count padding.
    image_labels = {
        30: ((551.8, "Aboriginal Camps in which Whites or Half-castes were Living"),),
        31: ((553.0, "Aboriginal Camps in which Whites or Half-castes were Living"),),
        38: ((798.2, "Other Camps without Dwellings"),),
        39: ((796.4, "Other Camps without Dwellings"),),
    }
    labels.extend(image_labels.get(page, ()))
    labels.sort()
    return edges, words, labels


def _printed_row(page: int, y: float) -> tuple[float, str]:
    """Find a printed identity, registering a damaged panel to its mate."""
    own = _source_geometry(page)[2]
    nearby = [(abs(start - y), start, label) for start, label in own if abs(start - y) <= 4]
    if nearby:
        _, baseline, label = min(nearby)
        return baseline, label
    facing = _source_geometry(page + (1 if page % 2 == 0 else -1))[2]
    anchors = [(abs(start - y), start - other_start)
               for start, label in own for other_start, other_label in facing
               if _category(label) == _category(other_label)
               and abs(start - other_start) < 12]
    if not anchors:
        return y, ""
    shift = min(anchors)[1]
    nearby = [(abs(start + shift - y), start + shift, label) for start, label in facing
              if abs(start + shift - y) <= 3]
    if nearby:
        _, baseline, label = min(nearby)
        return baseline, label
    return y, ""


def _reading(value: str) -> str:
    return value.replace(",", "").replace(" ", "")


def _alignment(row: dict, expected: int) -> tuple[int, float, bool]:
    """Align a candidate vector to exact PDF digits in nearby physical rows."""
    cells = row["cells"]
    overflow = max(0, max(cells, default=0) - expected)
    baseline = overflow if overflow and all(
        cells.get(i, {}).get("value", "").replace(" ", "") in _EMPTY
        for i in range(1, overflow + 1)) else 0
    edges, words, _ = _source_geometry(row["page"])
    votes: dict[tuple[int, float], set[int]] = defaultdict(set)
    for col, cell in cells.items():
        value = _reading(cell["value"])
        if not value.isdecimal():
            continue
        for word in words:
            y = (word[1] + word[3]) / 2
            if abs(y - row["y"]) > 20 or _reading(word[4]) != value:
                continue
            slot = min(range(len(edges)), key=lambda i: abs(edges[i] - word[2]))
            if abs(edges[slot] - word[2]) > 12:
                continue
            offset = col - slot - 1
            if not -3 <= offset <= 5:
                continue
            # Collect the same printed baseline despite OCR box-height noise.
            for centre in (round(y / 2) * 2, round(y / 2) * 2 - 2,
                           round(y / 2) * 2 + 2):
                votes[(offset, centre)].add(col)
    if votes:
        ranked = sorted(votes, key=lambda key: (-len(votes[key]), abs(key[1] - row["y"]), key))
        offset, y = ranked[0]
        hits = votes[(offset, y)]
        if any(other_offset != offset and len(votes[(other_offset, other_y)]) == len(hits)
               for other_offset, other_y in ranked):
            # Repeated sparse digits can support competing column origins.
            # Keep the structural baseline; do not select an arithmetic fit.
            return baseline, row["y"], False
        total_anchor = (row["page"] % 2 == 1 and expected + offset in hits
                        and len(_reading(cells[expected + offset]["value"])) >= 2)
        distinct = {_reading(cells[col]["value"]) for col in hits}
        close = abs(y - row["y"]) <= 20
        if ((close and len(hits) >= 3 and len(distinct) >= 2)
                or (close and total_anchor)):
            return offset, y, True
    return baseline, row["y"], False


def _values(number: int, row: dict, data_fields: list[str], prefix: str,
            alignment: tuple[int, float, bool] | None = None) -> dict[str, str]:
    # The physical panel fixes the bins: local heading indexes restart and
    # are often copied from the opposite page, including sparse proposals.
    fields = data_fields[:11] if row["page"] % 2 == 0 else data_fields[11:]
    offset, physical_y, anchored = alignment or _alignment(row, len(fields))
    result: dict[str, str] = {}
    for col, cell in sorted(row["cells"].items()):
        position = col - offset - 1
        if not 0 <= position < len(fields):
            continue
        value = cell["value"].strip()
        if "\n" in value or not value:
            continue
        # Keep a damaged numeric candidate visible until a source-located
        # recovery replaces it; alphabetic OCR is not an absence mark.
        result[fields[position]] = value
    if offset and anchored and row["row_id"].startswith("1911_census_volume_iii_part_xiii_dwellings::"):
        # A truncated leader proposal can end before the final printed bins.
        # Recover only that displaced tail, and only a unique clean PDF cell.
        # Ambiguous/damaged OCR words remain missing; no balancing is used.
        edges, words, _ = _source_geometry(row["page"])
        last = max(row["cells"]) - offset
        for slot in range(last, len(fields)):
            located = [word[4] for word in words
                       if abs((word[1] + word[3]) / 2 - physical_y) <= 3
                       and abs(word[2] - edges[slot]) <= 12]
            digits = [value for value in located if re.fullmatch(r"\d[\d,]*", value)]
            if len(digits) == 1 and all(value in _EMPTY or value == digits[0] for value in located):
                result[fields[slot]] = digits[0]
            elif located and all(value in _EMPTY for value in located):
                result[fields[slot]] = "".join(located)
    return result


def assign_room_table(page: int, y: float, fallback: int) -> int:
    """Classify rows on physical pages shared by two indexed tables.

    Facing pages use the same vertical cutover, even when only the left
    page's PDF title is machine-readable.  This runs before row grouping.
    """
    cutovers = {
        16: (459, 10), 17: (459, 10),
        34: (601, 18), 35: (601, 18),
        36: (425, 19), 37: (425, 19),
        50: (639, 27), 51: (639, 27),
        52: (423, 28), 53: (423, 28),
    }
    if page in cutovers:
        boundary, earlier = cutovers[page]
        return earlier if y < boundary else earlier + 1
    if 18 <= page <= 21:
        return 11
    if 22 <= page <= 33:
        return 12 + (page - 22) // 2
    if 38 <= page <= 49:
        return 21 + (page - 38) // 2
    return fallback


def _source_inventory(number: int, records: list[dict], dimensions: list[str],
                      fields: list[str], row_field: str, states, panels) -> dict:
    """Account for printed identities before considering extraction proposals.

    A duplicate or a truncated proposal cannot create another printed row.
    Conversely, a missing proposal cannot remove a source-labelled row. The
    PDF cell is authoritative only when its physical slot has a unique clean
    reading; unreadable regions never become zero or an arithmetic residual.
    """
    pages = {
        10: range(16, 18), 11: range(16, 22),
        18: range(34, 36), 19: range(34, 38), 20: range(36, 38),
        27: range(50, 52), 28: range(50, 54), 29: range(52, 54),
    }.get(number, range(22 + 2 * (number - 12), 24 + 2 * (number - 12))
          if number < 21 else range(38 + 2 * (number - 21), 40 + 2 * (number - 21)))
    inventory: dict[tuple[str, ...], dict] = {}
    for page in pages:
        for y, label in _source_geometry(page)[2]:
            if assign_room_table(page, y, number) != number:
                continue
            category = _category(label)
            label = _MATERIAL_LABELS.get(category, _DWELLING_LABELS.get(category, label))
            dims = {"state": _state(page, y, states) if number == 11 else "",
                    "dwelling_class": _class(number, page, y, panels), row_field: label}
            key = tuple(category if field == row_field else dims[field] for field in dimensions)
            item = inventory.setdefault(key, {"dimensions": dims, "values": {}, "locations": {}})
            item["locations"][page] = y

    # Missing text on one half is registered with common printed identities
    # in that same section, not the nearest material in an unrelated section.
    for key, item in inventory.items():
        for page, y in list(item["locations"].items()):
            facing = page + (1 if page % 2 == 0 else -1)
            if facing in item["locations"]:
                continue
            shifts = [other["locations"][facing] - other["locations"][page]
                      for other_key, other in inventory.items()
                      if page in other["locations"] and facing in other["locations"]
                      and all(other_key[i] == key[i] for i, field in enumerate(dimensions)
                              if field != row_field)]
            if shifts:
                item["locations"][facing] = y + median(shifts)

    for key, item in inventory.items():
        candidates: dict[str, set[str]] = defaultdict(set)
        for record in records:
            if record["category"] != _category(item["dimensions"][row_field]):
                continue
            if (record["state"] != item["dimensions"]["state"]
                    or record["dwelling_class"] != item["dimensions"]["dwelling_class"]):
                continue
            y = item["locations"].get(record["page"])
            if y is None or abs(record["y"] - y) > 4:
                continue
            for field, value in record["values"].items():
                candidates[field].add(value)
        for field, values in candidates.items():
            readings = {_reading(value) for value in values}
            if len(readings) == 1 or all(value.replace(" ", "") in _EMPTY for value in values):
                item["values"][field] = sorted(values)[0]
            else:
                item["values"][field] = "UNREADABLE: " + " / ".join(sorted(values))
        for page, y in item["locations"].items():
            edges, words, _ = _source_geometry(page)
            local_fields = fields[:11] if page % 2 == 0 else fields[11:]
            for slot, edge in enumerate(edges):
                located = [word[4].replace(" ", "") for word in words
                           if abs((word[1] + word[3]) / 2 - y) <= 3
                           and abs(word[2] - edge) <= 12]
                digits = [value for value in located
                          if re.fullmatch(r"\d+|\d{1,3}(?:,\d{3})+", value)]
                existing = item["values"].get(local_fields[slot], "")
                if (not _reading(existing).isdecimal() and len(digits) == 1
                        and all(value in _EMPTY or value == digits[0] for value in located)):
                    item["values"][local_fields[slot]] = digits[0]
                elif located and all(value in _EMPTY for value in located):
                    item["values"][local_fields[slot]] = ".."
    return inventory


def _pdf_corrections(number: int, grouped: dict[tuple[str, ...], dict]) -> None:
    """Replace damaged source candidates with legible facing-page PDF cells.

    Table 18: PDF page 35, All Dwellings panel, y=442–565; Table 29:
    PDF page 53, y=482–788. Dots below represent the printed dot marks.
    """
    prefix = "inmates" if number >= 21 else "rooms"
    fields = [f"{prefix}_{i}" for i in range(1, 20)] + [f"{prefix}_20_and_over"]
    if prefix == "rooms":
        fields.append("rooms_unspecified")
    fields.append(f"{prefix}_total")
    for table, page, _y, identity, vector in _SOURCE_PANEL_READS:
        if table == number and identity in grouped:
            local_fields = fields[:11] if page % 2 == 0 else fields[11:]
            grouped[identity]["values"].update(zip(local_fields, vector.split()))
    if number <= 20:
        camp_categories = ("wagons trains etc", "aboriginal camps", "other camps without dwellings")
        for key, item in grouped.items():
            category = key[-1] if number == 11 else key[0]
            if category not in camp_categories:
                continue
            totals = _ROOM_CAMP_TOTALS.get(key[0] if number == 11 else number)
            total = totals[camp_categories.index(category)] if totals else None
            if total is None:
                continue
            item["values"].update({field: ".." for field in fields[:20]})
            item["values"]["rooms_unspecified"] = ".." if category == camp_categories[2] else total
            item["values"]["rooms_total"] = total
    for table, _page, _y, identity, values in _SOURCE_READS:
        if table == number and identity in grouped:
            grouped[identity]["values"].update(values)
    if number == 18:
        all_rows = {
            "stone": ("64", "33", "33", "17", "25", "10", "13", "4", "31", "2", "1,724"),
            "brick": ("132", "59", "70", "38", "32", "24", "13", "14", "127", "14", "7,239"),
            # PDF p35, Concrete All Dwellings, x=365–378, y=456–467:
            # the printed total is 89, not the previous override's 39.
            "concrete": ("2", "..", "..", "..", "..", "..", "..", "..", "5", "..", "89"),
            "iron": ("1", "1", "1", "..", "1", "..", "..", "..", "5", "1", "490"),
            "wood": ("89", "52", "29", "20", "14", "15", "14", "4", "82", "81", "29,375"),
            "sun dried bricks": ("..", "..", "..", "..", "..", "1", "..", "..", "..", "..", "10"),
            "pise": ("..", "..", "..", "..", "..", "..", "..", "..", "..", "..", "3"),
            "lath and plaster": ("..", "..", "1", "..", "..", "..", "..", "..", "1", "..", "45"),
            "bark": ("..", "..", "..", "..", "..", "..", "..", "..", "..", "..", "22"),
            "bushes rushes": ("..", "..", "..", "..", "..", "..", "..", "..", "..", "..", "2"),
            "calico canvas hessian": ("..", "..", "..", "..", "..", "..", "..", "..", "..", "..", "621"),
            "ruberoid": ("..", "..", "..", "..", "..", "1", "..", "..", "..", "..", "6"),
            "unspecified": ("1", "..", "1", "..", "..", "..", "..", "..", "..", "297", "389"),
            "wagons trains etc": ("..", "..", "..", "..", "..", "..", "..", "..", "..", "10", "10"),
            "total": ("289", "145", "135", "75", "72", "51", "40", "22", "251", "405", "40,025"),
        }
        for (material, dwelling_class), item in grouped.items():
            if dwelling_class == "All Dwellings" and material in all_rows:
                item["values"].update(zip(
                    [f"rooms_{i}" for i in range(12, 20)] +
                    ["rooms_20_and_over", "rooms_unspecified", "rooms_total"],
                    all_rows[material],
                ))
            elif dwelling_class == "Dwellings Other Than Private" and material == "total":
                item["values"].update(zip(
                    [f"rooms_{i}" for i in range(12, 20)] +
                    ["rooms_20_and_over", "rooms_unspecified", "rooms_total"],
                    ("78", "44", "41", "32", "38", "29", "27", "15", "221", "23", "1,075"),
                ))
            if material == "total" and dwelling_class in (
                    "All Dwellings", "Dwellings Other Than Private"):
                left_totals = {
                    "All Dwellings": ("2,436", "2,944", "3,317", "11,679", "6,496",
                                      "5,519", "2,660", "1,716", "873", "646", "254"),
                    "Dwellings Other Than Private": ("5", "5", "16", "66", "52",
                                                     "77", "57", "90", "61", "61", "37"),
                }
                item["values"].update(zip(
                    [f"rooms_{i}" for i in range(1, 12)], left_totals[dwelling_class]))
            if dwelling_class == "All Dwellings" and material == "wagons trains etc":
                item["values"].update({f"rooms_{i}": ".." for i in range(1, 12)})
            elif dwelling_class == "Dwellings Other Than Private" and material == "wagons trains etc":
                item["values"].update(zip(
                    [f"rooms_{i}" for i in range(12, 20)] +
                    ["rooms_20_and_over", "rooms_unspecified", "rooms_total"],
                    ("..", "..", "..", "..", "..", "..", "..", "..", "..", "10", "10"),
                ))
            elif dwelling_class == "Dwellings Other Than Private" and material == "unspecified":
                item["values"].update(zip(
                    [f"rooms_{i}" for i in range(12, 20)] +
                    ["rooms_20_and_over", "rooms_unspecified", "rooms_total"],
                    ("1", "..", "..", "..", "..", "..", "..", "..", "..", "8", "10"),
                ))
                for i in range(1, 12):
                    item["values"].setdefault(f"rooms_{i}", "..")
                item["values"]["rooms_10"] = "1"
    if number == 29:
        totals = {
            "Private Dwellings": dict(zip(
                ("stone", "brick", "concrete", "iron", "wood", "sun dried bricks",
                 "pise", "bark", "calico canvas hessian", "unspecified", "total"),
                ("30", "31", "3", "12", "183", "3", "29", "2", "133", "5", "431"))),
            "Dwellings Other Than Private": dict(zip(
                ("stone", "brick", "iron", "wood", "calico canvas hessian", "total"),
                ("2", "1", "1", "4", "3", "11"))),
            "All Dwellings": dict(zip(
                ("stone", "brick", "concrete", "iron", "wood", "sun dried bricks",
                 "pise", "bark", "calico canvas hessian", "unspecified", "total",
                 "other camps without dwellings"),
                ("32", "32", "3", "13", "187", "3", "29", "2", "136", "5", "442", "2"))),
        }
        for (material, dwelling_class), item in grouped.items():
            value = totals.get(dwelling_class, {}).get(material)
            if value is not None:
                item["values"]["inmates_total"] = value
            # PDF p53 Private panel: Stone x=112–118, y=482–493
            # prints inmates13=1; Wood x=143–149, y=514–525 prints
            # inmates14=2. These are omitted cells, not balancing patches.
            if dwelling_class == "Private Dwellings" and material == "stone":
                item["values"]["inmates_13"] = "1"
            elif dwelling_class == "Private Dwellings" and material == "wood":
                item["values"]["inmates_14"] = "2"
            if dwelling_class == "Private Dwellings" and material in (
                    "calico canvas hessian", "unspecified"):
                for i in range(12, 20):
                    item["values"].setdefault(f"inmates_{i}", "..")
                item["values"].setdefault("inmates_20_and_over", "..")
            if material == "total" and dwelling_class == "Private Dwellings":
                item["values"].update({"inmates_12": "2", "inmates_13": "1", "inmates_14": "4"})
                for i in range(15, 20):
                    item["values"][f"inmates_{i}"] = ".."
                item["values"]["inmates_20_and_over"] = ".."
            elif material == "total" and dwelling_class == "Dwellings Other Than Private":
                for i in range(12, 20):
                    item["values"][f"inmates_{i}"] = ".."
                item["values"]["inmates_20_and_over"] = ".."
            if material == "total":
                left_totals = {
                    "Private Dwellings": ("140", "53", "46", "31", "47", "27", "34", "17", "14", "10", "5"),
                    "Dwellings Other Than Private": ("1", "..", "4", "1", "..", "2", "..", "1", "2", "..", ".."),
                    "All Dwellings": ("141", "53", "50", "32", "47", "29", "34", "18", "16", "10", "5"),
                }
                item["values"].update(zip(
                    [f"inmates_{i}" for i in range(1, 12)], left_totals[dwelling_class]))
            if material == "other camps without dwellings" and dwelling_class == "All Dwellings":
                item["values"].update({"inmates_1": "1", "inmates_5": "1"})


def assemble_room_panels(
    number: int,
    source_rows: list[dict],
    schema: tuple[list[str], list[str], str],
    states: dict[int, list[tuple[float, str]]],
    panels: dict[int, list[tuple[float, str]]],
) -> tuple[list[str], list[list[str]]]:
    """Return the printed categories, combining facing pages without index reuse.

    Columns and physical rows use independent PDF geometry. Facing rows
    join only on printed category, state and class; proximity alone cannot
    turn an unidentified row into the nearest labelled material.
    """
    if not 10 <= number <= 29:
        raise ValueError(f"Not a paired room/inmate table: {number}")
    dimensions, fields, row_field = schema
    prefix = "inmates" if number >= 21 else "rooms"
    records: list[dict] = []
    for row in sorted(source_rows, key=lambda r: (r["page"], r["y"], r["row_id"])):
        alignment = _alignment(row, 11 if row["page"] % 2 == 0 else len(fields) - 11)
        values = _values(number, row, fields, prefix, alignment)
        label = " ".join((row["label"] or row["resolved"]).split())
        # Wrapped category labels are data, unlike column-heading fragments.
        if _text(label) in (
                "nature of dwelling", "materials of which outer walls were built", "20 and over", "un specified"):
            continue
        numeric_label = label if label.isdecimal() else ""
        if numeric_label:
            label = ""
        page, y = row["page"], row["y"]
        source_backed = row["row_id"].startswith("1911_census_volume_iii_part_xiii_dwellings::")
        if source_backed:
            _, physical_y, anchored = alignment
            if anchored:
                y = physical_y
            edges, words, printed = _source_geometry(page)
            if not anchored and label:
                # An independently printed matching identity can register a
                # short sparse proposal whose box was placed between rows.
                # p21 FT Police Station y779.74 is printed at784.8, not the
                # nearer Military row776.64. Never use this for an unknown.
                same_label = [start for start, name in printed
                              if _category(name) == _category(label)
                              and abs(start - y) <= 7.5]
                if len(same_label) == 1:
                    y = same_label[0]
            printed_y, printed_label = _printed_row(page, y)
            if printed_label:
                y, label = printed_y, printed_label
            elif printed and y < min(start for start, _ in printed) - 12:
                # Column-heading proposals are not unidentified dwellings.
                continue
            if numeric_label and page % 2 and printed_label:
                # A numeric row label is not necessarily Total: p37 Other/
                # Stone proposes rooms20=1 as its label although Total is2.
                # Restore a total only with independent printed-column proof.
                total_words = [word[4] for word in words
                               if abs((word[1] + word[3]) / 2 - y) <= 3
                               and abs(word[2] - edges[-1]) <= 12
                               and re.fullmatch(r"\d[\d,]*", word[4])]
                if len(total_words) == 1 and _reading(total_words[0]) == _reading(numeric_label):
                    values[f"{prefix}_total"] = numeric_label
            if printed_label:
                # Recover visible printed absence marks for every category,
                # not merely camps.  An empty PDF region remains missing.
                local_fields = fields[:11] if page % 2 == 0 else fields[11:]
                for slot, edge in enumerate(edges):
                    located = [word[4].replace(" ", "") for word in words
                               if abs((word[1] + word[3]) / 2 - y) <= 3
                               and abs(word[2] - edge) <= 12]
                    if located and all(value in _EMPTY for value in located):
                        values.setdefault(local_fields[slot], "".join(located))
        canonical = _category(label)
        if canonical in _MATERIAL_LABELS:
            label = _MATERIAL_LABELS[canonical]
        elif canonical in _DWELLING_LABELS:
            label = _DWELLING_LABELS[canonical]
        if not values and not label:
            continue
        if number == 19 and page == 34 and y < 690:
            continue  # duplicated header sample before the first printed row
        if number == 11 and page == 19 and 165 <= y < 175 and label == "Private House":
            values["rooms_total"] = "261,977"  # PDF p19, Victoria Private House
        if number == 18 and page == 35 and 575 <= y < 586:
            label = "Other Camps without Dwellings"  # printed beside Total 86
        if number == 29 and page == 53 and 784 <= y < 796:
            label = "Total"  # printed at the far right, absent from row_label
        if number == 29 and page == 53 and 796 <= y < 812:
            label = "Other Camps without Dwellings"
        state = _state(page, y, states) if "state" in dimensions else ""
        dwelling_class = _class(number, page, y, panels)
        records.append({"page": page, "y": y, "label": label, "category": _category(label),
                        "row_id": row["row_id"], "state": state,
                        "dwelling_class": dwelling_class, "values": values})
    if source_rows and all(row["row_id"].startswith(
            "1911_census_volume_iii_part_xiii_dwellings::") for row in source_rows):
        grouped = _source_inventory(number, records, dimensions, fields, row_field, states, panels)
        _pdf_corrections(number, grouped)
        return dimensions + fields, [
            [item["dimensions"].get(field, "") for field in dimensions]
            + [item["values"].get(field, "") for field in fields]
            for item in sorted(grouped.values(), key=lambda item: min(item["locations"].items()))
        ]


    # Two source-region proposals sometimes describe the very same physical
    # row.  Prefer the labelled, more complete proposal; never sum proposals.
    by_page: dict[int, list[dict]] = defaultdict(list)
    for record in records:
        by_page[record["page"]].append(record)
    for page, entries in by_page.items():
        kept: list[dict] = []
        for record in sorted(entries, key=lambda r: (r["y"], -len(r["values"]))):
            duplicate = next((old for old in kept if abs(old["y"] - record["y"]) < 4
                              and old["state"] == record["state"]
                              and old["dwelling_class"] == record["dwelling_class"]
                              and (not old["category"] or not record["category"]
                                   or old["category"] == record["category"])
                              and bool(old["values"].keys() & record["values"].keys())
                              and all(_reading(old["values"][field]) == _reading(value)
                                      or old["values"][field].replace(" ", "") in _EMPTY
                                      and value.replace(" ", "") in _EMPTY
                                      for field, value in record["values"].items()
                                      if field in old["values"])), None)
            if duplicate:
                if not duplicate["label"] and record["label"]:
                    duplicate["label"] = record["label"]
                    duplicate["category"] = record["category"]
                for field, value in record["values"].items():
                    duplicate["values"].setdefault(field, value)
            else:
                kept.append(record)
        by_page[page] = kept

    merged: list[dict] = []
    for page in sorted(by_page):
        if page % 2:  # right-hand continuation, with page-local indexes 1–11
            continue
        left = sorted(by_page[page], key=lambda r: r["y"])
        right = sorted(by_page.get(page + 1, []), key=lambda r: r["y"])
        used: set[int] = set()
        for record in left:
            # A printed identity is stronger than facing-page y coordinates:
            # page25's compressed candidate y's previously paired Stone with
            # Concrete. No nearest-unlabelled or Hospital/Charitable exception.
            choices = [(i, other) for i, other in enumerate(right)
                       if i not in used and record["category"]
                       and other["category"] == record["category"]
                       and other["state"] == record["state"]
                       and other["dwelling_class"] == record["dwelling_class"]]
            if len(choices) == 1:
                index, partner = choices[0]
                used.add(index)
                for field, value in partner["values"].items():
                    record["values"].setdefault(field, value)
            merged.append(record)
        merged.extend(other for i, other in enumerate(right) if i not in used)
    # A table beginning on the right-hand page is not expected here, but do
    # retain such source rows rather than silently discarding their cells.
    for page in sorted(by_page):
        if page % 2 and page - 1 not in by_page:
            merged.extend(by_page[page])
    for record in merged:
        if not record.get("row_id", "").startswith("1911_census_volume_iii_part_xiii_dwellings::"):
            continue
        page = record["page"] + (1 if record["page"] % 2 == 0 else -1)
        y, label = _printed_row(page, record["y"])
        if (_category(label) != record["category"]
                or ("state" in dimensions and _state(page, y, states) != record["state"])
                or _class(number, page, y, panels) != record["dwelling_class"]):
            continue
        # A missing facing proposal is not a missing printed category. Fill
        # only independently visible dot cells (e.g. p20 FT Hotel), not zeros
        # or guessed digits, and never manufacture a category absent in print.
        edges, words, _ = _source_geometry(page)
        local_fields = fields[:11] if page % 2 == 0 else fields[11:]
        for slot, edge in enumerate(edges):
            located = [word[4].replace(" ", "") for word in words
                       if abs((word[1] + word[3]) / 2 - y) <= 3
                       and abs(word[2] - edge) <= 12]
            if located and all(value in _EMPTY for value in located):
                record["values"].setdefault(local_fields[slot], "".join(located))


    grouped: dict[tuple[str, ...], dict] = {}
    for record in sorted(merged, key=lambda r: (r["page"], r["y"])):
        # Preserve unidentified numeric vectors with an empty category rather
        # than silently dropping them or assigning the closest printed row.
        dims = {"state": record["state"], "dwelling_class": record["dwelling_class"],
                row_field: record["label"]}
        key = tuple(_category(dims[field]) if field == row_field else dims[field] for field in dimensions)
        if not record["label"]:
            key = tuple(record["state"] if field == "state" else record["dwelling_class"]
                        if field == "dwelling_class" else
                        f"unidentified:{record['page']}:{record['y']}:{record.get('row_id', '')}"
                        for field in dimensions)
        if key in grouped and any(
                field in grouped[key]["values"]
                and _reading(grouped[key]["values"][field]) != _reading(value)
                and not (grouped[key]["values"][field].replace(" ", "") in _EMPTY
                         and value.replace(" ", "") in _EMPTY)
                for field, value in record["values"].items()):
            # Distinct, contradictory proposals retain duplicate printed
            # dimensions so checks can flag ambiguity; never cherry-pick.
            key = tuple(f"{part}:ambiguous:{record['page']}:{record['y']}"
                        if dimensions[i] == row_field else part
                        for i, part in enumerate(key))
        if key not in grouped:
            grouped[key] = {"dimensions": dims, "values": {}}
        for field, value in record["values"].items():
            grouped[key]["values"].setdefault(field, value)
    return dimensions + fields, [
        [item["dimensions"].get(field, "") for field in dimensions]
        + [item["values"].get(field, "") for field in fields]
        for item in grouped.values()
    ]
