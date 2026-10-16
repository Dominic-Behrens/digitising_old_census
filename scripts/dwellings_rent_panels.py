"""Rejoin the facing-page room columns in Dwellings Tables 30–48.

The source-cell column index starts again at one on each facing page.  The
printed panels, rather than the candidate table id or OCR of a repeated row
label, determine both the dimension and the room-column offset.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import median

import pymupdf


ROOMS = [str(i) for i in range(1, 20)] + ["20_and_over", "unspecified", "total"]
INMATES = [str(i) for i in range(1, 20)] + ["20_and_over", "total"]
PRIVATE = "Private Dwellings"
OTHER = "Dwellings Other Than Private"
ALL = "All Dwellings"
METHODS = (
    "Occupied by Owners",
    "Occupied by Rent Purchasers",
    "Occupied by Tenants",
    "Other and Unspecified Methods of Occupancy",
)
ROOM_CATEGORIES = (PRIVATE, OTHER, ALL)
PLACEHOLDER = re.compile(r"^[\s.·•—–\-„〃”'\"]*$")
FIGURE = re.compile(r"^[†‡*]?\s*[0-9][0-9,]*(?:\s*[†‡*])?$|^[\s.·•—–\-„〃”'\"]+$")
PDF = (Path(__file__).resolve().parents[1] /
       "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf")

# Independently read from the printed leaves, not calculated from residuals.
# Keys are (table, physical page, printed section, row identity); values use
# the page-local figure slots. Totals retain their printed values even where
# OCR has merged a horizontal rule and several adjacent numeral columns.
SOURCE_READINGS = {
    (30, 54, PRIVATE, '5'): {1: '22,562'},
    (30, 54, PRIVATE, '9'): {4: '2,882'},
    (30, 54, PRIVATE, 'total'): {2: '132,601', 4: '124,099'},
    (30, 54, PRIVATE, 'unspecified'): dict(enumerate('843 561 526 466 427 304 268 173 135 67'.split())),
    (30, 54, OTHER, '1'): {3: '5', 4: '54', 5: '2', 6: '2'},
    (30, 54, OTHER, '2'): {3: '17', 4: '6', 5: '8'},
    (30, 54, OTHER, '4'): {0: '75'},
    (30, 54, OTHER, 'total'): {0: '1,167', 7: '2,313'},
    (30, 54, ALL, '7'): {7: '6,536'},
    (30, 54, ALL, 'wagons'): {1: '144'},
    (30, 55, OTHER, '1'): {4: '1'},
    (30, 55, OTHER, '16'): {6: '33', 7: '22'},
    (30, 55, OTHER, '2'): {0: '1', 1: '1', 2: '1', 8: '..'},
    (30, 55, OTHER, '3'): {2: '2', 3: '2', 4: '2', 5: '1'},
    (30, 55, OTHER, '4'): {0: '8', 1: '9', 2: '2', 4: '..', 5: '1'},
    (30, 55, OTHER, '5'): {1: '11', 7: '1'},
    (30, 55, ALL, '8'): {8: '23'},
    (31, 56, PRIVATE, '1'): {1: '3,395', 2: '1,197'},
    (31, 56, PRIVATE, '17'): {0: '3'},
    (31, 56, PRIVATE, '19'): {1: '2'},
    (31, 56, PRIVATE, '5'): {5: '9,899'},
    (31, 56, PRIVATE, '8'): {4: '2,249'},
    (31, 56, PRIVATE, 'total'): dict(enumerate('32,211 37,648 46,879 50,122 45,538 36,714 26,640 18,134 11,377 6,593'.split())),
    (31, 56, OTHER, '11'): {7: '40'},
    (31, 56, ALL, '17'): {6: '23'},
    (31, 56, ALL, 'total'): {0: '32,584', 5: '37,661'},
    (31, 57, PRIVATE, '1'): {0: '3', 1: '4', 2: '..', 3: '1', 5: '1', 8: '2', 9: '1', 10: '20,321'},
    (31, 57, PRIVATE, '12'): {2: '46', 9: '6'},
    (31, 57, PRIVATE, '15'): {4: '4', 7: '..'},
    (31, 57, PRIVATE, '2'): {4: '1', 5: '..', 6: '..', 8: '..'},
    (31, 57, PRIVATE, '20 and over'): {2: '18'},
    (31, 57, OTHER, 'total'): {7: '179'},
    (31, 57, ALL, 'aboriginal camps'): {9: '2'},
    (31, 57, ALL, 'total'): {3: '883', 4: '590', 6: '309', 7: '247', 10: '330,976'},
    (32, 58, PRIVATE, '12'): {2: '100'},
    (32, 58, PRIVATE, '19'): {0: '..', 2: '4', 3: '2', 4: '4', 7: '4', 8: '3'},
    (32, 58, PRIVATE, '2'): {2: '1,284', 3: '974', 7: '86'},
    (32, 58, PRIVATE, '3'): {5: '1,319'},
    (32, 58, PRIVATE, '7'): {2: '3,586', 4: '4,286', 5: '3,614'},
    (32, 58, PRIVATE, 'total'): {4: '38,377', 8: '8,639', 0: '22,578', 1: '34,418', 2: '41,542', 3: '43,003', 5: '29,798', 7: '13,899'},
    (32, 58, PRIVATE, 'unspecified'): dict(enumerate('248 179 149 150 108 89 74 40 27 22'.split())),
    (32, 58, OTHER, '1'): dict(enumerate('51 5 3 .. .. 2 .. .. .. ..'.split())),
    (32, 58, OTHER, '2'): {0: '26', 1: '20', 2: '8', 7: '1', 5: '..'},
    (32, 58, OTHER, 'total'): dict(enumerate('291 326 521 733 822 901 850 739 700 547'.split())),
    (32, 58, ALL, '1'): {0: '7,508', 1: '1,560', 2: '429', 5: '28'},
    (32, 58, ALL, '5'): {3: '10,545', 5: '7,129'},
    (32, 58, ALL, '8'): {2: '1,782'},
    (32, 59, PRIVATE, '6'): {1: '279'},
    (32, 59, PRIVATE, '7'): {1: '223', 4: '21', 8: '2', 9: '2'},
    (32, 59, PRIVATE, 'total'): {0: '2,578', 2: '624', 3: '284', 4: '167', 5: '73', 6: '50', 9: '44', 10: '263,634', 1: '1,215'},
    (32, 59, PRIVATE, 'unspecified'): dict(enumerate('16 5 4 .. 1 1 2 1 1 2 1,119'.split())),
    (32, 59, OTHER, '1'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '1', 10: '62'},
    (32, 59, OTHER, '16'): {8: '..'},
    (32, 59, OTHER, '19'): {6: '..', 8: '..'},
    (32, 59, OTHER, '2'): {1: '..', 2: '..', 4: '1', 9: '..'},
    (32, 59, OTHER, '4'): {2: '..', 3: '..'},
    (32, 59, OTHER, '5'): {3: '..'},
    (32, 59, OTHER, 'aboriginal camps'): {3: '..', 5: '..', 6: '..', 8: '..', 9: '..', 10: '1'},
    (32, 59, OTHER, 'total'): {9: '682'},
    (32, 59, OTHER, 'unspecified'): {7: '..'},
    (32, 59, OTHER, 'wagons'): {4: '..', 5: '..', 6: '..', 8: '..', 9: '..'},
    (32, 59, ALL, '19'): {8: '..'},
    (32, 59, ALL, '2'): {0: '6', 5: '..'},
    (32, 59, ALL, '4'): {1: '113', 5: '5'},
    (32, 59, ALL, '6'): {4: '27'},
    (32, 59, ALL, '9'): {8: '3'},
    (32, 59, ALL, 'other camps'): {0: '5', 2: '5', 3: '3', 4: '2', 5: '5'},
    (32, 59, ALL, 'total'): {1: '1,555', 3: '506', 4: '331', 5: '206', 8: '105'},
    (33, 60, PRIVATE, '17'): {0: '1', 5: '4', 6: '5', 7: '4'},
    (33, 60, PRIVATE, '19'): {1: '1', 3: '..', 6: '1', 5: '3'},
    (33, 60, PRIVATE, '20 and over'): {5: '8', 6: '4'},
    (33, 60, PRIVATE, '3'): {5: '647'},
    (33, 60, PRIVATE, '9'): {4: '374'},
    (33, 60, PRIVATE, 'total'): {0: '18,546', 3: '16,987', 4: '15,273', 5: '12,873', 7: '6,647', 1: '15,732'},
    (33, 60, PRIVATE, 'unspecified'): {5: '31', 6: '42'},
    (33, 60, OTHER, '1'): {0: '31'},
    (33, 60, OTHER, '3'): {8: '..'},
    (33, 60, ALL, 'other camps'): dict(enumerate('540 177 98 52 39 26 20 13 8 9'.split())),
    (33, 60, ALL, 'total'): {4: '15,523', 3: '17,186'},
    (33, 61, PRIVATE, '15'): dict(enumerate('4 7 2 6 1 2 3 1 3 7 98'.split())),
    (33, 61, PRIVATE, '16'): {0: '4', 1: '4', 2: '2', 3: '1', 5: '2', 6: '3', 8: '3', 9: '4', 10: '74', 4: '..', 7: '..'},
    (33, 61, PRIVATE, '17'): dict(enumerate('.. .. .. .. .. 1 2 .. 2 1 29'.split())),
    (33, 61, PRIVATE, '18'): {4: '..', 7: '..', 10: '23'},
    (33, 61, PRIVATE, '19'): dict(enumerate('3 .. 1 1 .. .. .. .. .. 2 18'.split())),
    (33, 61, PRIVATE, '20 and over'): dict(enumerate('5 2 3 4 2 1 4 1 6 30 91'.split())),
    (33, 61, PRIVATE, '3'): {8: '4', 9: '..', 6: '1'},
    (33, 61, PRIVATE, 'total'): dict(enumerate('1,413 795 378 192 115 84 49 34 69 109 121,753'.split())),
    (33, 61, PRIVATE, 'unspecified'): dict(enumerate('7 2 4 2 2 .. 1 .. 1 7 486'.split())),
    (33, 61, OTHER, '1'): {0: '..', 6: '..', 8: '..', 9: '..'},
    (33, 61, OTHER, '11'): {2: '4', 5: '4'},
    (33, 61, OTHER, '16'): {2: '10'},
    (33, 61, OTHER, '18'): {2: '7', 3: '5', 4: '5', 8: '5'},
    (33, 61, OTHER, '3'): {6: '..'},
    (33, 61, OTHER, '9'): {9: '3', 2: '5'},
    (33, 61, ALL, '12'): {2: '28'},
    (33, 61, ALL, '17'): {5: '6', 6: '3', 7: '4'},
    (33, 61, ALL, '5'): {2: '53'},
    (33, 61, ALL, 'aboriginal camps'): dict(enumerate('.. .. .. .. 1 .. 1 .. .. 1 50'.split())),
    (33, 61, ALL, 'total'): {1: '956', 3: '345', 6: '123', 7: '115', 4: '248'},
    (33, 61, ALL, 'unspecified'): {0: '10', 1: '3', 3: '2', 4: '4', 5: '1', 7: '2', 10: '607', 2: '7'},
    (33, 61, ALL, 'wagons'): dict(enumerate('1 .. .. .. .. .. .. .. .. .. 171'.split())),
    (34, 62, PRIVATE, '13'): {0: '2', 1: '4'},
    (34, 62, PRIVATE, 'total'): dict(enumerate('6,219 10,931 12,985 13,579 12,078 9,408 6,580 4,331 2,811 1,494'.split())),
    (34, 62, OTHER, '1'): dict(enumerate('8 2 .. .. .. .. .. .. .. ..'.split())),
    (34, 62, OTHER, '10'): dict(enumerate('.. 1 3 6 5 9 4 11 3 8'.split())),
    (34, 62, OTHER, '11'): dict(enumerate('1 2 3 2 4 6 4 8 5 5'.split())),
    (34, 62, OTHER, '12'): dict(enumerate('.. 2 1 3 6 10 9 6 10 6'.split())),
    (34, 62, OTHER, '13'): dict(enumerate('.. .. 1 2 2 5 11 3 10 3'.split())),
    (34, 62, OTHER, '14'): dict(enumerate('1 1 7 5 12 12 5 12 10 6'.split())),
    (34, 62, OTHER, '15'): dict(enumerate('.. .. 3 1 8 6 7 4 11 4'.split())),
    (34, 62, OTHER, '16'): dict(enumerate('1 .. 4 3 9 8 7 7 7 4'.split())),
    (34, 62, OTHER, '17'): dict(enumerate('.. .. 1 5 2 2 2 3 4 4'.split())),
    (34, 62, OTHER, '18'): dict(enumerate('.. .. .. 1 5 5 6 2 2 3'.split())),
    (34, 62, OTHER, '19'): dict(enumerate('.. .. 1 1 1 .. 2 .. 3 1'.split())),
    (34, 62, OTHER, '2'): dict(enumerate('5 1 4 4 1 1 1 .. .. ..'.split())),
    (34, 62, OTHER, '20 and over'): dict(enumerate('.. .. .. 4 5 10 8 20 20 17'.split())),
    (34, 62, OTHER, '3'): dict(enumerate('2 5 3 2 1 .. 1 1 1 1'.split())),
    (34, 62, OTHER, '4'): dict(enumerate('7 6 16 18 10 4 6 8 4 ..'.split())),
    (34, 62, OTHER, '5'): dict(enumerate('3 11 11 19 20 19 23 19 5 6'.split())),
    (34, 62, OTHER, '6'): dict(enumerate('1 7 9 22 21 22 28 25 13 20'.split())),
    (34, 62, OTHER, '7'): dict(enumerate('2 7 6 13 13 11 10 23 21 14'.split())),
    (34, 62, OTHER, '8'): dict(enumerate('.. 4 1 5 11 9 13 14 18 17'.split())),
    (34, 62, OTHER, '9'): dict(enumerate('.. 2 9 2 12 8 14 9 12 10'.split())),
    (34, 62, OTHER, 'aboriginal camps'): dict(enumerate('3 5 4 1 .. .. .. .. .. 1'.split())),
    (34, 62, OTHER, 'total'): dict(enumerate('56 64 91 120 150 149 164 178 159 131'.split())),
    (34, 62, OTHER, 'unspecified'): dict(enumerate('14 2 2 1 1 1 3 3 .. 1'.split())),
    (34, 62, OTHER, 'wagons'): dict(enumerate('8 6 2 .. 1 1 .. .. .. ..'.split())),
    (34, 62, ALL, '20 and over'): {0: '3', 2: '3', 3: '8', 4: '9', 5: '16', 6: '14', 8: '28'},
    (34, 62, ALL, 'total'): dict(enumerate('6,275 10,995 13,076 13,699 12,228 9,557 6,744 4,509 2,970 1,625'.split())),
    (34, 63, PRIVATE, '10'): {5: '1', 6: '1'},
    (34, 63, PRIVATE, '20 and over'): {0: '2', 1: '4', 2: '2', 9: '1', 10: '57'},
    (34, 63, PRIVATE, '7'): {8: '1'},
    (34, 63, PRIVATE, 'total'): dict(enumerate('846 416 219 94 45 31 15 5 5 16 82,108'.split())),
    (34, 63, OTHER, '1'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 10'.split())),
    (34, 63, OTHER, '10'): dict(enumerate('8 7 7 6 1 3 3 3 2 6 96'.split())),
    (34, 63, OTHER, '11'): dict(enumerate('8 5 7 3 3 2 .. 3 1 9 81'.split())),
    (34, 63, OTHER, '12'): dict(enumerate('5 6 4 7 5 5 2 2 3 7 99'.split())),
    (34, 63, OTHER, '13'): dict(enumerate('4 2 1 1 2 2 3 1 2 8 63'.split())),
    (34, 63, OTHER, '14'): dict(enumerate('3 4 1 3 5 1 8 1 3 9 109'.split())),
    (34, 63, OTHER, '15'): dict(enumerate('2 3 4 2 2 1 .. 2 2 4 66'.split())),
    (34, 63, OTHER, '16'): dict(enumerate('3 6 2 3 1 1 3 3 4 9 85'.split())),
    (34, 63, OTHER, '17'): dict(enumerate('2 2 1 2 .. .. 1 2 3 3 39'.split())),
    (34, 63, OTHER, '18'): dict(enumerate('2 .. 6 1 .. 2 3 1 2 8 49'.split())),
    (34, 63, OTHER, '19'): dict(enumerate('.. 1 3 1 2 .. .. .. 1 9 26'.split())),
    (34, 63, OTHER, '2'): dict(enumerate('1 .. .. .. .. .. .. .. .. 1 19'.split())),
    (34, 63, OTHER, '20 and over'): dict(enumerate('18 18 14 16 18 13 12 12 10 134 349'.split())),
    (34, 63, OTHER, '3'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 17'.split())),
    (34, 63, OTHER, '4'): dict(enumerate('3 .. .. .. .. .. .. .. .. .. 82'.split())),
    (34, 63, OTHER, '5'): dict(enumerate('7 1 .. .. .. 1 .. .. .. 1 146'.split())),
    (34, 63, OTHER, '6'): dict(enumerate('18 9 11 4 1 2 1 .. 3 2 219'.split())),
    (34, 63, OTHER, '7'): dict(enumerate('10 16 8 5 3 .. 1 1 1 1 166'.split())),
    (34, 63, OTHER, '8'): dict(enumerate('17 8 12 9 5 1 3 1 2 1 151'.split())),
    (34, 63, OTHER, '9'): dict(enumerate('5 5 5 6 5 1 2 3 .. 1 111'.split())),
    (34, 63, OTHER, 'aboriginal camps'): dict(enumerate('1 .. .. 2 .. 1 .. .. .. .. 18'.split())),
    (34, 63, OTHER, 'total'): dict(enumerate('118 95 91 71 53 37 42 36 39 227 2,071'.split())),
    (34, 63, OTHER, 'unspecified'): dict(enumerate('1 2 5 .. .. 1 .. 1 .. 14 52'.split())),
    (34, 63, OTHER, 'wagons'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 18'.split())),
    (34, 63, ALL, '18'): {1: '1', 3: '1'},
    (34, 63, ALL, 'aboriginal camps'): dict(enumerate('1 .. .. 2 .. 1 .. .. .. .. 18'.split())),
    (34, 63, ALL, 'total'): dict(enumerate('964 511 310 165 98 68 57 41 44 243 84,179'.split())),
    (35, 64, PRIVATE, '12'): dict(enumerate('4 3 7 12 18 21 13 17 5 8'.split())),
    (35, 64, PRIVATE, '13'): dict(enumerate('1 2 3 5 5 5 7 7 7'.split())),
    (35, 64, PRIVATE, '14'): {0: '..', 1: '1', 2: '4', 3: '5', 4: '9', 6: '4', 7: '3', 8: '4', 5: '4'},
    (35, 64, PRIVATE, '3'): {2: '1,702', 3: '1,446', 6: '318', 8: '59'},
    (35, 64, PRIVATE, '4'): {2: '3,313'},
    (35, 64, PRIVATE, '9'): {6: '63', 7: '44'},
    (35, 64, PRIVATE, 'total'): dict(enumerate('16,133 10,455 9,170 8,844 7,440 5,586 3,703 2,209 1,376 779'.split())),
    (35, 64, PRIVATE, 'unspecified'): {3: '25', 5: '15', 6: '17', 7: '15', 8: '9', 9: '2'},
    (35, 64, OTHER, '2'): {0: '8', 1: '11', 5: '2'},
    (35, 64, OTHER, '20 and over'): {2: '6', 3: '6', 4: '9', 5: '8', 6: '7'},
    (35, 64, OTHER, '3'): {5: '3'},
    (35, 64, OTHER, '5'): dict(enumerate('9 21 17 29 21 20 20'.split())),
    (35, 64, OTHER, '6'): {3: '19', 4: '21'},
    (35, 64, OTHER, '7'): {3: '11'},
    (35, 64, OTHER, '8'): {0: '..'},
    (35, 64, OTHER, 'aboriginal camps'): dict(enumerate('40 13 11 5 4 1 2 1'.split())),
    (35, 64, OTHER, 'total'): {1: '128'},
    (35, 64, OTHER, 'unspecified'): {4: '2'},
    (35, 64, ALL, '1'): {0: '10,635', 2: '566', 5: '36', 8: '3', 6: '11'},
    (35, 64, ALL, '15'): {9: '3'},
    (35, 64, ALL, '9'): {0: '21'},
    (35, 64, ALL, 'other camps'): dict(enumerate('1,157 153 59 38 14 5 4 8 .. 2'.split())),
    (35, 64, ALL, 'total'): {1: '10,583', 2: '9,325', 3: '9,000', 4: '7,618', 5: '5,733', 8: '1,500', 9: '904'},
    (35, 65, PRIVATE, '1'): {1: '2'},
    (35, 65, PRIVATE, '16'): {1: '1', 2: '1', 4: '..', 5: '..', 8: '..', 10: '23', 3: '1', 7: '..'},
    (35, 65, PRIVATE, '19'): {2: '1', 3: '..', 4: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '3', 1: '..', 5: '..'},
    (35, 65, PRIVATE, '2'): dict(enumerate('10 1 1 .. 1 .. .. 1 .. 1 6,418'.split())),
    (35, 65, PRIVATE, '8'): {7: '1', 8: '1', 9: '1'},
    (35, 65, PRIVATE, '9'): {0: '17', 7: '1', 8: '1', 9: '..'},
    (35, 65, PRIVATE, 'unspecified'): {0: '4', 1: '2', 2: '1', 3: '3', 4: '2', 5: '..', 6: '..', 8: '..', 9: '1', 10: '291'},
    (35, 65, OTHER, '1'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '13'},
    (35, 65, OTHER, '14'): {1: '..', 2: '..'},
    (35, 65, OTHER, '15'): {3: '..', 6: '3', 9: '10'},
    (35, 65, OTHER, '17'): {7: '1'},
    (35, 65, OTHER, '19'): {2: '..', 7: '1', 10: '33'},
    (35, 65, OTHER, '2'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 6: '1', 7: '..', 9: '..', 10: '26'},
    (35, 65, OTHER, '20 and over'): {5: '18', 6: '24', 7: '13', 8: '16', 9: '185', 10: '393'},
    (35, 65, OTHER, '3'): {0: '1', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 7: '..', 9: '..'},
    (35, 65, OTHER, '4'): {5: '1', 6: '..'},
    (35, 65, OTHER, '5'): {4: '2'},
    (35, 65, OTHER, '7'): {6: '2', 7: '..'},
    (35, 65, OTHER, 'unspecified'): {2: '..', 4: '2', 5: '2', 6: '..', 7: '..', 8: '..', 9: '8', 10: '34'},
    (35, 65, OTHER, 'wagons'): {0: '..', 1: '..', 2: '..', 3: '..', 6: '..', 8: '..', 10: '15'},
    (35, 65, ALL, '1'): {0: '..', 1: '2', 2: '..', 4: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '13,906'},
    (35, 65, ALL, '19'): {5: '..'},
    (35, 65, ALL, '2'): dict(enumerate('10 1 1 .. 1 .. 1 1 .. 1 6,444'.split())),
    (35, 65, ALL, '3'): {5: '..', 7: '..', 9: '1', 4: '..'},
    (35, 65, ALL, '5'): {8: '..'},
    (35, 65, ALL, '7'): {0: '52', 1: '38', 2: '20', 3: '13', 4: '7', 5: '2', 6: '2', 7: '1', 9: '2', 10: '2,357', 8: '..'},
    (35, 65, ALL, 'aboriginal camps'): {6: '..'},
    (36, 66, PRIVATE, '17'): {1: '..', 2: '1', 3: '4', 4: '2', 5: '5', 6: '1', 7: '7', 8: '1'},
    (36, 66, OTHER, '1'): {2: '2'},
    (36, 66, OTHER, '13'): {0: '..', 4: '3', 5: '3', 6: '5', 7: '6', 8: '4', 9: '3'},
    (36, 66, OTHER, '15'): {0: '..', 6: '2', 7: '2', 8: '3'},
    (36, 66, OTHER, '16'): {7: '3', 8: '2', 9: '3'},
    (36, 66, OTHER, '18'): {2: '1'},
    (36, 66, OTHER, '3'): {2: '6', 3: '2', 8: '..'},
    (36, 66, OTHER, '9'): {0: '..', 8: '5'},
    (36, 66, OTHER, 'total'): {0: '24', 1: '43', 2: '83', 6: '102', 7: '88', 8: '55', 9: '64', 4: '89'},
    (36, 66, OTHER, 'unspecified'): {4: '1', 5: '1', 6: '2', 7: '2', 8: '1'},
    (36, 66, ALL, '17'): {2: '1', 3: '4', 4: '4', 6: '4', 7: '9', 8: '5'},
    (36, 66, ALL, '18'): {1: '..', 2: '2', 3: '1', 4: '2', 5: '6', 6: '4', 7: '4', 8: '4'},
    (36, 66, ALL, '19'): {3: '2', 4: '2', 5: '3', 6: '1', 7: '1', 9: '..', 1: '..', 2: '..', 8: '..'},
    (36, 66, ALL, '4'): {5: '1,409', 6: '926'},
    (36, 66, ALL, '6'): {6: '577'},
    (36, 66, ALL, 'wagons'): {0: '6', 1: '2', 3: '1', 4: '1'},
    (36, 67, PRIVATE, '1'): {0: '1', 3: '1', 10: '2,431'},
    (36, 67, PRIVATE, '18'): {2: '..', 7: '..', 8: '..'},
    (36, 67, PRIVATE, '2'): {1: '1', 2: '1'},
    (36, 67, PRIVATE, '20 and over'): {0: '3', 1: '2', 3: '..', 4: '1', 6: '..', 7: '..', 8: '..', 9: '..', 10: '30'},
    (36, 67, PRIVATE, '3'): {1: '1'},
    (36, 67, PRIVATE, '4'): {2: '10'},
    (36, 67, PRIVATE, '5'): {9: '1'},
    (36, 67, PRIVATE, '6'): {0: '102', 1: '56'},
    (36, 67, PRIVATE, '7'): {7: '1', 8: '..'},
    (36, 67, PRIVATE, 'total'): {5: '17', 7: '2'},
    (36, 67, PRIVATE, 'unspecified'): {0: '4', 1: '5', 3: '3', 4: '1', 5: '..', 6: '1', 7: '..', 8: '..', 10: '382'},
    (36, 67, OTHER, '11'): dict(enumerate('4 1 .. .. 2 .. .. .. 1 .. 37'.split())),
    (36, 67, OTHER, '12'): dict(enumerate('4 3 3 3 3 1 2 .. .. 2 78'.split())),
    (36, 67, OTHER, '13'): dict(enumerate('2 1 6 .. 4 1 .. .. 1 1 44'.split())),
    (36, 67, OTHER, '14'): dict(enumerate('1 4 2 2 1 1 .. .. .. 6 41'.split())),
    (36, 67, OTHER, '15'): dict(enumerate('2 2 1 1 2 1 1 .. .. 3 32'.split())),
    (36, 67, OTHER, '16'): dict(enumerate('2 1 3 3 .. .. .. 1 .. 2 38'.split())),
    (36, 67, OTHER, '17'): dict(enumerate('4 2 .. 1 .. 1 1 .. 2 1 29'.split())),
    (36, 67, OTHER, '18'): dict(enumerate('2 5 2 .. 1 1 .. .. .. 2 27'.split())),
    (36, 67, OTHER, '19'): dict(enumerate('1 2 3 1 1 .. .. 1 1 2 15'.split())),
    (36, 67, OTHER, '20 and over'): dict(enumerate('9 8 12 14 11 12 14 11 7 61 221'.split())),
    (36, 67, OTHER, '3'): {7: '..'},
    (36, 67, OTHER, '9'): {7: '..'},
    (36, 67, OTHER, 'total'): dict(enumerate('50 44 42 31 27 22 20 14 13 90 1,075'.split())),
    (36, 67, OTHER, 'unspecified'): {0: '1', 1: '..', 2: '1', 3: '..', 4: '..', 5: '..', 6: '..', 9: '4', 10: '13', 7: '..'},
    (36, 67, ALL, '10'): {1: '10', 2: '9', 3: '7', 6: '..', 7: '..', 8: '..', 9: '2'},
    (36, 67, ALL, '11'): {2: '5', 3: '1', 6: '..', 7: '..', 8: '..', 9: '1'},
    (36, 67, ALL, '12'): {2: '4', 3: '4', 7: '..', 8: '1', 9: '4'},
    (36, 67, ALL, '2'): {2: '1'},
    (36, 67, ALL, '3'): {0: '15'},
    (36, 67, ALL, '4'): {2: '10', 3: '5', 5: '..', 7: '1', 8: '1', 9: '1'},
    (36, 67, ALL, '5'): {2: '10', 3: '2', 7: '..'},
    (36, 67, ALL, '6'): {2: '22', 3: '12', 7: '..'},
    (36, 67, ALL, '7'): {1: '40', 2: '15', 3: '11', 7: '1', 8: '..', 9: '..'},
    (36, 67, ALL, '8'): {2: '16', 3: '5', 7: '..', 8: '2', 9: '1'},
    (36, 67, ALL, '9'): {2: '12', 3: '4', 7: '..', 8: '1', 9: '..'},
    (37, 68, PRIVATE, '1'): dict(enumerate('516 60 20 10 5 .. 1 .. .. ..'.split())),
    (37, 68, PRIVATE, '10'): dict(enumerate('.. .. .. 1 .. .. .. .. .. ..'.split())),
    (37, 68, PRIVATE, '2'): dict(enumerate('122 77 33 22 14 7 4 2 1 ..'.split())),
    (37, 68, PRIVATE, '3'): dict(enumerate('22 23 21 14 9 8 7 3 1 ..'.split())),
    (37, 68, PRIVATE, '4'): dict(enumerate('10 16 12 15 12 2 7 2 1 2'.split())),
    (37, 68, PRIVATE, '5'): dict(enumerate('7 5 10 6 4 5 3 1 .. 2'.split())),
    (37, 68, PRIVATE, '6'): dict(enumerate('.. 5 7 3 4 3 2 2 3 ..'.split())),
    (37, 68, PRIVATE, '7'): dict(enumerate('1 1 3 2 1 2 1 .. .. 1'.split())),
    (37, 68, PRIVATE, '8'): dict(enumerate('.. .. 2 2 .. .. 3 .. 1 ..'.split())),
    (37, 68, PRIVATE, '9'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, PRIVATE, 'total'): dict(enumerate('679 189 108 75 50 27 29 10 8 5'.split())),
    (37, 68, PRIVATE, 'unspecified'): dict(enumerate('1 2 .. .. 1 .. 1 .. 1 ..'.split())),
    (37, 68, OTHER, '1'): dict(enumerate('1 .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '10'): dict(enumerate('.. .. 1 .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '11'): dict(enumerate('.. .. .. 1 .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '13'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '15'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '16'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '2'): dict(enumerate('3 1 1 .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '20 and over'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '3'): dict(enumerate('2 .. .. .. 1 .. .. .. .. ..'.split())),
    (37, 68, OTHER, '4'): dict(enumerate('1 .. 1 2 1 .. .. .. .. ..'.split())),
    (37, 68, OTHER, '5'): dict(enumerate('1 .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '6'): dict(enumerate('.. .. 1 2 .. .. .. .. .. ..'.split())),
    (37, 68, OTHER, '8'): dict(enumerate('.. .. .. .. .. 1 .. .. .. ..'.split())),
    (37, 68, OTHER, '9'): dict(enumerate('.. .. 1 .. 1 .. .. .. .. ..'.split())),
    (37, 68, OTHER, 'aboriginal camps'): dict(enumerate('6 8 4 2 1 .. .. .. .. ..'.split())),
    (37, 68, OTHER, 'total'): dict(enumerate('14 9 9 8 4 1 .. .. .. 1'.split())),
    (37, 68, OTHER, 'unspecified'): dict(enumerate('.. .. .. 1 .. .. .. .. .. 1'.split())),
    (37, 68, ALL, '1'): dict(enumerate('517 60 20 10 5 .. 1 .. .. ..'.split())),
    (37, 68, ALL, '10'): dict(enumerate('.. .. 1 1 .. .. .. .. .. ..'.split())),
    (37, 68, ALL, '11'): dict(enumerate('.. .. .. 1 .. .. .. .. .. ..'.split())),
    (37, 68, ALL, '13'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, ALL, '15'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, ALL, '16'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, ALL, '2'): dict(enumerate('125 78 34 22 14 7 4 2 1 ..'.split())),
    (37, 68, ALL, '20 and over'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (37, 68, ALL, '3'): dict(enumerate('24 23 21 14 10 8 7 3 1 ..'.split())),
    (37, 68, ALL, '4'): dict(enumerate('11 16 13 17 13 2 7 2 1 2'.split())),
    (37, 68, ALL, '5'): dict(enumerate('8 5 10 6 4 5 3 1 .. 2'.split())),
    (37, 68, ALL, '6'): dict(enumerate('.. 5 8 5 4 3 2 2 3 ..'.split())),
    (37, 68, ALL, '7'): dict(enumerate('1 1 3 2 1 2 1 .. .. 1'.split())),
    (37, 68, ALL, '8'): dict(enumerate('.. .. 2 2 .. 1 3 .. 1 ..'.split())),
    (37, 68, ALL, '9'): dict(enumerate('.. .. 1 .. 1 .. .. .. .. ..'.split())),
    (37, 68, ALL, 'aboriginal camps'): dict(enumerate('6 8 4 2 1 .. .. .. .. ..'.split())),
    (37, 68, ALL, 'other camps'): dict(enumerate('35 7 2 1 5 3 2 .. 1 1'.split())),
    (37, 68, ALL, 'total'): dict(enumerate('693 198 117 83 54 28 29 10 8 6'.split())),
    (37, 68, ALL, 'unspecified'): dict(enumerate('1 2 .. 1 1 .. 1 .. 1 1'.split())),
    (37, 69, PRIVATE, '1'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 613'.split())),
    (37, 69, PRIVATE, '10'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (37, 69, PRIVATE, '2'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 283'.split())),
    (37, 69, PRIVATE, '3'): dict(enumerate('2 .. .. .. .. 1 .. .. .. .. 111'.split())),
    (37, 69, PRIVATE, '4'): dict(enumerate('1 1 .. .. .. .. .. .. .. .. 81'.split())),
    (37, 69, PRIVATE, '5'): dict(enumerate('1 1 .. .. .. .. .. .. .. .. 45'.split())),
    (37, 69, PRIVATE, '6'): dict(enumerate('.. 1 .. .. .. .. 1 .. .. .. 31'.split())),
    (37, 69, PRIVATE, '7'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. 13'.split())),
    (37, 69, PRIVATE, '8'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. 9'.split())),
    (37, 69, PRIVATE, '9'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 1'.split())),
    (37, 69, PRIVATE, 'total'): dict(enumerate('4 3 2 .. 3 1 1 .. .. .. 1,194'.split())),
    (37, 69, PRIVATE, 'unspecified'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 6'.split())),
    (37, 69, OTHER, '1'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (37, 69, OTHER, '10'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (37, 69, OTHER, '11'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (37, 69, OTHER, '13'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 1'.split())),
    (37, 69, OTHER, '15'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. 1'.split())),
    (37, 69, OTHER, '16'): dict(enumerate('.. .. .. .. .. .. .. .. .. 1 1'.split())),
    (37, 69, OTHER, '2'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 5'.split())),
    (37, 69, OTHER, '20 and over'): dict(enumerate('.. .. .. .. .. .. .. .. 1 2 3'.split())),
    (37, 69, OTHER, '3'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 3'.split())),
    (37, 69, OTHER, '4'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 5'.split())),
    (37, 69, OTHER, '5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (37, 69, OTHER, '6'): dict(enumerate('.. 1 .. .. .. .. .. .. .. .. 4'.split())),
    (37, 69, OTHER, '8'): dict(enumerate('1 .. .. .. .. .. .. .. .. .. 2'.split())),
    (37, 69, OTHER, '9'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (37, 69, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 21'.split())),
    (37, 69, OTHER, 'total'): dict(enumerate('1 1 1 .. 1 .. .. .. 1 3 54'.split())),
    (37, 69, OTHER, 'unspecified'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (37, 69, ALL, '1'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 614'.split())),
    (37, 69, ALL, '10'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (37, 69, ALL, '11'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (37, 69, ALL, '13'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 1'.split())),
    (37, 69, ALL, '15'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. 1'.split())),
    (37, 69, ALL, '16'): dict(enumerate('.. .. .. .. .. .. .. .. .. 1 1'.split())),
    (37, 69, ALL, '2'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 288'.split())),
    (37, 69, ALL, '20 and over'): dict(enumerate('.. .. .. .. .. .. .. .. 1 2 3'.split())),
    (37, 69, ALL, '3'): dict(enumerate('2 .. .. .. .. 1 .. .. .. .. 114'.split())),
    (37, 69, ALL, '4'): dict(enumerate('1 1 .. .. .. .. .. .. .. .. 86'.split())),
    (37, 69, ALL, '5'): dict(enumerate('1 1 .. .. .. .. .. .. .. .. 46'.split())),
    (37, 69, ALL, '6'): dict(enumerate('.. 2 .. .. .. .. 1 .. .. .. 35'.split())),
    (37, 69, ALL, '7'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. 13'.split())),
    (37, 69, ALL, '8'): dict(enumerate('1 .. 1 .. .. .. .. .. .. .. 11'.split())),
    (37, 69, ALL, '9'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. 3'.split())),
    (37, 69, ALL, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 21'.split())),
    (37, 69, ALL, 'other camps'): dict(enumerate('.. .. 1 1 .. .. .. .. 1 .. 60'.split())),
    (37, 69, ALL, 'total'): dict(enumerate('5 4 3 .. 4 1 1 .. 1 3 1,248'.split())),
    (37, 69, ALL, 'unspecified'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 8'.split())),
    (38, 70, PRIVATE, '1'): dict(enumerate('109 18 5 .. .. .. 1 2 1 ..'.split())),
    (38, 70, PRIVATE, '10'): dict(enumerate('.. 1 1 1 .. .. 1 .. 2 1'.split())),
    (38, 70, PRIVATE, '11'): dict(enumerate('1 .. 1 .. 1 .. 1 1 .. ..'.split())),
    (38, 70, PRIVATE, '12'): dict(enumerate('.. .. .. 1 .. .. .. .. 1 ..'.split())),
    (38, 70, PRIVATE, '14'): dict(enumerate('.. .. .. .. .. .. 1 .. .. ..'.split())),
    (38, 70, PRIVATE, '16'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (38, 70, PRIVATE, '19'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (38, 70, PRIVATE, '2'): dict(enumerate('12 6 3 1 2 .. .. 1 .. ..'.split())),
    (38, 70, PRIVATE, '20 and over'): dict(enumerate('.. .. .. .. .. .. 1 .. .. 1'.split())),
    (38, 70, PRIVATE, '3'): dict(enumerate('2 1 5 3 2 4 1 .. .. 1'.split())),
    (38, 70, PRIVATE, '4'): dict(enumerate('10 11 12 8 8 3 4 1 .. 2'.split())),
    (38, 70, PRIVATE, '5'): dict(enumerate('3 8 8 7 10 9 6 4 .. 2'.split())),
    (38, 70, PRIVATE, '6'): dict(enumerate('.. 2 4 4 12 7 9 4 3 ..'.split())),
    (38, 70, PRIVATE, '7'): dict(enumerate('.. 3 2 1 8 1 5 3 4 2'.split())),
    (38, 70, PRIVATE, '8'): dict(enumerate('1 1 .. 4 3 1 3 1 3 1'.split())),
    (38, 70, PRIVATE, '9'): dict(enumerate('.. 2 1 .. 1 2 1 .. .. ..'.split())),
    (38, 70, PRIVATE, 'total'): dict(enumerate('140 53 46 31 47 27 34 17 14 10'.split())),
    (38, 70, PRIVATE, 'unspecified'): dict(enumerate('2 .. 4 .. .. .. .. .. .. ..'.split())),
    (38, 70, OTHER, '1'): dict(enumerate('1 .. 1 .. .. .. .. .. .. ..'.split())),
    (38, 70, OTHER, '13'): dict(enumerate('.. .. 1 .. .. .. .. 1 .. ..'.split())),
    (38, 70, OTHER, '2'): dict(enumerate('.. .. .. .. .. 1 .. .. .. ..'.split())),
    (38, 70, OTHER, '20 and over'): dict(enumerate('.. .. 1 .. .. .. .. .. .. ..'.split())),
    (38, 70, OTHER, '5'): dict(enumerate('.. .. 1 .. .. .. .. .. 2 ..'.split())),
    (38, 70, OTHER, '6'): dict(enumerate('.. .. .. .. .. 1 .. .. .. ..'.split())),
    (38, 70, OTHER, '8'): dict(enumerate('.. .. .. 1 .. .. .. .. .. ..'.split())),
    (38, 70, OTHER, 'total'): dict(enumerate('1 .. 4 1 .. 2 .. 1 2 ..'.split())),
    (38, 70, ALL, '1'): dict(enumerate('110 18 6 .. .. .. 1 2 1 ..'.split())),
    (38, 70, ALL, '10'): dict(enumerate('.. 1 1 1 .. .. 1 .. 2 1'.split())),
    (38, 70, ALL, '11'): dict(enumerate('1 .. 1 .. 1 .. 1 1 .. ..'.split())),
    (38, 70, ALL, '12'): dict(enumerate('.. .. .. 1 .. .. .. .. 1 ..'.split())),
    (38, 70, ALL, '13'): dict(enumerate('.. .. 1 .. .. .. .. 1 .. ..'.split())),
    (38, 70, ALL, '14'): dict(enumerate('.. .. .. .. .. .. 1 .. .. ..'.split())),
    (38, 70, ALL, '16'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (38, 70, ALL, '19'): dict(enumerate('.. .. .. .. .. .. .. .. .. ..'.split())),
    (38, 70, ALL, '2'): dict(enumerate('12 6 3 1 2 1 .. 1 .. ..'.split())),
    (38, 70, ALL, '20 and over'): dict(enumerate('.. .. 1 .. .. .. 1 .. .. 1'.split())),
    (38, 70, ALL, '3'): dict(enumerate('2 1 5 3 2 4 1 .. .. 1'.split())),
    (38, 70, ALL, '4'): dict(enumerate('10 11 12 8 8 3 4 1 .. 2'.split())),
    (38, 70, ALL, '5'): dict(enumerate('3 8 9 7 10 9 6 4 2 2'.split())),
    (38, 70, ALL, '6'): dict(enumerate('.. 2 4 4 12 8 9 4 3 ..'.split())),
    (38, 70, ALL, '7'): dict(enumerate('.. 3 2 1 8 1 5 3 4 2'.split())),
    (38, 70, ALL, '8'): dict(enumerate('1 1 .. 5 3 1 3 1 3 1'.split())),
    (38, 70, ALL, '9'): dict(enumerate('.. 2 1 .. 1 2 1 .. .. ..'.split())),
    (38, 70, ALL, 'other camps'): {0: '1', 1: '..', 2: '..', 3: '..', 4: '1', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..'},
    (38, 70, ALL, 'total'): dict(enumerate('141 53 50 32 47 29 34 18 16 10'.split())),
    (38, 70, ALL, 'unspecified'): dict(enumerate('2 .. 4 .. .. .. .. .. .. ..'.split())),
    (38, 71, PRIVATE, '1'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 136'.split())),
    (38, 71, PRIVATE, '10'): dict(enumerate('1 .. .. .. .. .. .. .. .. .. 8'.split())),
    (38, 71, PRIVATE, '11'): dict(enumerate('.. 1 .. .. .. .. .. .. .. .. 6'.split())),
    (38, 71, PRIVATE, '12'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (38, 71, PRIVATE, '14'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 2'.split())),
    (38, 71, PRIVATE, '16'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. 1'.split())),
    (38, 71, PRIVATE, '19'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 1'.split())),
    (38, 71, PRIVATE, '2'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 25'.split())),
    (38, 71, PRIVATE, '20 and over'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 3'.split())),
    (38, 71, PRIVATE, '3'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 19'.split())),
    (38, 71, PRIVATE, '4'): dict(enumerate('1 .. .. .. .. .. .. .. .. .. 60'.split())),
    (38, 71, PRIVATE, '5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 57'.split())),
    (38, 71, PRIVATE, '6'): dict(enumerate('3 1 .. .. .. .. .. .. .. .. 49'.split())),
    (38, 71, PRIVATE, '7'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 30'.split())),
    (38, 71, PRIVATE, '8'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 19'.split())),
    (38, 71, PRIVATE, '9'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 7'.split())),
    (38, 71, PRIVATE, 'total'): dict(enumerate('5 2 1 4 .. .. .. .. .. .. 431'.split())),
    (38, 71, PRIVATE, 'unspecified'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 6'.split())),
    (38, 71, OTHER, '1'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (38, 71, OTHER, '13'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (38, 71, OTHER, '2'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (38, 71, OTHER, '20 and over'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (38, 71, OTHER, '5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 3'.split())),
    (38, 71, OTHER, '6'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (38, 71, OTHER, '8'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (38, 71, OTHER, 'total'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 11'.split())),
    (38, 71, ALL, '1'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 138'.split())),
    (38, 71, ALL, '10'): dict(enumerate('1 .. .. .. .. .. .. .. .. .. 8'.split())),
    (38, 71, ALL, '11'): dict(enumerate('.. 1 .. .. .. .. .. .. .. .. 6'.split())),
    (38, 71, ALL, '12'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (38, 71, ALL, '13'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (38, 71, ALL, '14'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 2'.split())),
    (38, 71, ALL, '16'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. 1'.split())),
    (38, 71, ALL, '19'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 1'.split())),
    (38, 71, ALL, '2'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 26'.split())),
    (38, 71, ALL, '20 and over'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 4'.split())),
    (38, 71, ALL, '3'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 19'.split())),
    (38, 71, ALL, '4'): dict(enumerate('1 .. .. .. .. .. .. .. .. .. 60'.split())),
    (38, 71, ALL, '5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 60'.split())),
    (38, 71, ALL, '6'): dict(enumerate('3 1 .. .. .. .. .. .. .. .. 50'.split())),
    (38, 71, ALL, '7'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 30'.split())),
    (38, 71, ALL, '8'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. 20'.split())),
    (38, 71, ALL, '9'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 7'.split())),
    (38, 71, ALL, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (38, 71, ALL, 'total'): dict(enumerate('5 2 1 4 .. .. .. .. .. .. 442'.split())),
    (38, 71, ALL, 'unspecified'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 6'.split())),
    (39, 72, PRIVATE, 'pounds 10 0 over'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (39, 72, PRIVATE, 'pounds 9 0'): {3: '..', 5: '..', 9: '..'},
    (39, 72, PRIVATE, 'shillings 14'): {5: '4,615'},
    (39, 72, PRIVATE, 'shillings 2'): {4: '3,018'},
    (39, 72, PRIVATE, 'shillings 5'): {5: '10,104'},
    (39, 72, PRIVATE, 'total'): {4: '190,865', 8: '19,259'},
    (39, 72, PRIVATE, 'unspecified'): dict(enumerate('39,574 11,100 10,474 23,717 21,685 18,678'.split())),
    (39, 73, PRIVATE, 'pounds 10 0 over'): {1: '1'},
    (39, 73, PRIVATE, 'shillings 1'): dict(enumerate('.. .. .. .. .. .. .. .. .. 16 22,096'.split())),
    (39, 73, PRIVATE, 'shillings 11'): {2: '2', 9: '15'},
    (39, 73, PRIVATE, 'shillings 2'): {1: '..', 3: '1', 6: '1', 9: '32', 10: '34,806'},
    (39, 73, PRIVATE, 'shillings 22'): {3: '1', 9: '3'},
    (39, 73, PRIVATE, 'shillings 3'): {1: '1', 3: '..', 4: '..', 5: '..', 8: '..'},
    (39, 73, PRIVATE, 'shillings 4'): {1: '..', 3: '1', 4: '1', 5: '..', 7: '..', 8: '..'},
    (39, 73, PRIVATE, 'shillings 5'): {2: '8', 5: '1', 7: '..', 8: '..'},
    (39, 73, PRIVATE, 'shillings 6'): {4: '1', 5: '..', 7: '..'},
    (39, 73, PRIVATE, 'shillings 7'): {5: '..', 7: '..'},
    (39, 73, PRIVATE, 'shillings 8'): {7: '..'},
    (39, 73, PRIVATE, 'shillings 9'): {3: '..', 4: '..', 7: '..', 8: '..'},
    (39, 73, PRIVATE, 'under 1s'): dict(enumerate('.. .. .. .. .. .. .. .. .. 1 3,769'.split())),
    (39, 73, PRIVATE, 'unspecified'): {6: '82'},
    (39, 74, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (39, 74, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (39, 74, OTHER, 'pounds 4 5'): {8: '1', 10: '..'},
    (39, 74, OTHER, 'pounds 8 0'): {6: '1'},
    (39, 74, OTHER, 'shillings 14'): {1: '1', 4: '77', 6: '75'},
    (39, 74, OTHER, 'shillings 15'): {0: '1'},
    (39, 74, OTHER, 'shillings 16'): {0: '..', 1: '..', 2: '1'},
    (39, 74, OTHER, 'shillings 20'): {0: '1', 5: '226', 6: '306'},
    (39, 74, OTHER, 'shillings 24'): {4: '1'},
    (39, 74, OTHER, 'shillings 26'): {4: '1'},
    (39, 74, OTHER, 'shillings 27'): {4: '1'},
    (39, 74, OTHER, 'shillings 28'): {1: '1', 5: '1'},
    (39, 74, OTHER, 'shillings 29'): {1: '1'},
    (39, 74, OTHER, 'shillings 3'): {9: '1'},
    (39, 74, OTHER, 'shillings 30'): {4: '14'},
    (39, 74, OTHER, 'shillings 31'): {7: '4', 8: '5'},
    (39, 74, OTHER, 'shillings 32'): {8: '37'},
    (39, 74, OTHER, 'shillings 33'): {5: '1'},
    (39, 74, OTHER, 'shillings 36'): {9: '1'},
    (39, 74, OTHER, 'shillings 39'): {9: '1', 10: '1'},
    (39, 74, OTHER, 'shillings 4'): {9: '1'},
    (39, 74, OTHER, 'total'): dict(enumerate('303 240 358 855 1,678 2,810 2,570 2,417 2,000 1,818 1,410'.split())),
    (39, 74, OTHER, 'under 1s'): {6: '1'},
    (39, 74, OTHER, 'wagons'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (39, 75, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. 191 191'.split())),
    (39, 75, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 5,530'.split())),
    (39, 75, OTHER, 'shillings 2'): {1: '1'},
    (39, 75, OTHER, 'shillings 20'): {1: '135'},
    (39, 75, OTHER, 'shillings 39'): {4: '..', 5: '..', 8: '..'},
    (39, 75, OTHER, 'shillings 7'): {0: '4', 1: '4'},
    (39, 75, OTHER, 'shillings 8'): {5: '..', 6: '..', 1: '4'},
    (40, 76, PRIVATE, 'pounds 2 15'): {4: '1'},
    (40, 76, PRIVATE, 'shillings 27'): {1: '1'},
    (40, 76, PRIVATE, 'shillings 28'): {3: '1'},
    (40, 76, PRIVATE, 'shillings 32'): {3: '1'},
    (40, 76, PRIVATE, 'shillings 39'): {7: '1', 8: '1'},
    (40, 76, PRIVATE, 'total'): {3: '70,241'},
    (40, 77, PRIVATE, 'pounds 10 0 over'): {5: '..'},
    (40, 77, PRIVATE, 'shillings 10'): {0: '66', 10: '36,165'},
    (40, 77, PRIVATE, 'shillings 7'): {0: '7'},
    (40, 77, PRIVATE, 'shillings 9'): {0: '4'},
    (40, 77, PRIVATE, 'unspecified'): {4: '81', 10: '55,741'},
    (40, 78, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (40, 78, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (40, 78, OTHER, 'pounds 10 0 over'): dict(enumerate('.. .. .. .. .. .. .. .. .. 2 4'.split())),
    (40, 78, OTHER, 'pounds 2 10'): {3: '..', 5: '..'},
    (40, 78, OTHER, 'pounds 2 15'): {6: '..'},
    (40, 78, OTHER, 'pounds 3 15'): {6: '..', 7: '..'},
    (40, 78, OTHER, 'pounds 4 10'): {8: '..'},
    (40, 78, OTHER, 'pounds 4 15'): {9: '..'},
    (40, 78, OTHER, 'pounds 5 0'): {6: '1'},
    (40, 78, OTHER, 'pounds 6 0'): {6: '..', 7: '..', 8: '..'},
    (40, 78, OTHER, 'pounds 8 0'): {6: '1', 9: '1'},
    (40, 78, OTHER, 'shillings 1'): {2: '7', 3: '3', 4: '4', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..'},
    (40, 78, OTHER, 'shillings 12'): {1: '1'},
    (40, 78, OTHER, 'shillings 14'): {1: '1'},
    (40, 78, OTHER, 'shillings 2'): {2: '4', 4: '6', 5: '1', 7: '1', 8: '..', 9: '..', 3: '3'},
    (40, 78, OTHER, 'shillings 20'): {2: '1'},
    (40, 78, OTHER, 'shillings 27'): {4: '1'},
    (40, 78, OTHER, 'shillings 28'): {4: '..'},
    (40, 78, OTHER, 'shillings 29'): {5: '..'},
    (40, 78, OTHER, 'shillings 3'): {2: '4', 5: '1', 8: '..'},
    (40, 78, OTHER, 'shillings 30'): {3: '1'},
    (40, 78, OTHER, 'shillings 34'): {5: '..', 6: '..'},
    (40, 78, OTHER, 'shillings 35'): {4: '2'},
    (40, 78, OTHER, 'shillings 36'): {4: '1', 5: '..', 6: '..', 7: '..'},
    (40, 78, OTHER, 'shillings 37'): {4: '..', 5: '1'},
    (40, 78, OTHER, 'shillings 38'): {5: '..'},
    (40, 78, OTHER, 'shillings 4'): {4: '2', 5: '3', 9: '..'},
    (40, 78, OTHER, 'shillings 5'): {3: '14', 4: '23'},
    (40, 78, OTHER, 'shillings 6'): {4: '10'},
    (40, 78, OTHER, 'shillings 9'): {10: '..'},
    (40, 78, OTHER, 'under 1s'): {1: '..', 2: '..', 3: '..', 4: '..', 7: '..', 9: '..'},
    (40, 78, OTHER, 'unspecified'): {3: '88', 4: '94', 5: '101', 6: '76'},
    (40, 78, OTHER, 'wagons'): {0: '..', 4: '..', 5: '..'},
    (40, 79, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. 21 21'.split())),
    (40, 79, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1,865'.split())),
    (40, 79, OTHER, 'shillings 11'): {6: '..'},
    (40, 79, OTHER, 'shillings 2'): {1: '1'},
    (40, 79, OTHER, 'shillings 3'): {1: '..'},
    (40, 79, OTHER, 'shillings 6'): {0: '..'},
    (40, 79, OTHER, 'shillings 8'): {0: '1'},
    (40, 79, OTHER, 'shillings 9'): {0: '..', 1: '..'},
    (41, 80, PRIVATE, 'pounds 10 0 over'): {8: '..', 10: '..'},
    (41, 80, PRIVATE, 'pounds 2 10'): {3: '1'},
    (41, 80, PRIVATE, 'pounds 2 5'): {3: '..'},
    (41, 80, PRIVATE, 'pounds 3 0'): {4: '..'},
    (41, 80, PRIVATE, 'pounds 3 10'): {0: '..'},
    (41, 80, PRIVATE, 'pounds 4 0'): {8: '..'},
    (41, 80, PRIVATE, 'pounds 4 10'): {7: '1', 8: '1', 9: '1', 10: '1'},
    (41, 80, PRIVATE, 'pounds 4 15'): {9: '..', 10: '..'},
    (41, 80, PRIVATE, 'pounds 8 0'): {9: '1'},
    (41, 80, PRIVATE, 'shillings 12'): {9: '156'},
    (41, 80, PRIVATE, 'shillings 18'): {2: '2'},
    (41, 80, PRIVATE, 'shillings 21'): {1: '1'},
    (41, 80, PRIVATE, 'shillings 26'): {2: '..'},
    (41, 80, PRIVATE, 'shillings 29'): {3: '..'},
    (41, 80, PRIVATE, 'shillings 30'): {1: '1'},
    (41, 80, PRIVATE, 'shillings 31'): {3: '..'},
    (41, 80, PRIVATE, 'shillings 32'): {1: '..', 2: '1'},
    (41, 80, PRIVATE, 'shillings 33'): {2: '..'},
    (41, 80, PRIVATE, 'shillings 34'): {2: '1', 3: '..', 4: '1'},
    (41, 80, PRIVATE, 'shillings 36'): {3: '..', 6: '2'},
    (41, 80, PRIVATE, 'shillings 37'): {5: '6'},
    (41, 80, PRIVATE, 'shillings 38'): {2: '..', 4: '1'},
    (41, 80, PRIVATE, 'shillings 4'): {3: '4,099'},
    (41, 80, PRIVATE, 'shillings 6'): {1: '351', 2: '2,385'},
    (41, 80, PRIVATE, 'total'): {2: '18,054', 5: '48,927'},
    (41, 81, PRIVATE, 'pounds 10 0 over'): dict(enumerate('.. .. .. .. .. 1 2 .. 14 .. 17'.split())),
    (41, 81, PRIVATE, 'pounds 8 0'): {1: '1', 8: '6', 4: '2'},
    (41, 81, PRIVATE, 'shillings 10'): {10: '30,166'},
    (41, 81, PRIVATE, 'shillings 21'): {9: '..'},
    (41, 81, PRIVATE, 'shillings 4'): {4: '1', 9: '9', 10: '9,300'},
    (41, 81, PRIVATE, 'shillings 5'): {3: '1', 4: '1', 9: '16', 10: '24,887', 1: '7'},
    (41, 81, PRIVATE, 'shillings 9'): {9: '6'},
    (41, 81, PRIVATE, 'unspecified'): {10: '41,264'},
    (41, 82, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (41, 82, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (41, 82, OTHER, 'shillings 25'): {7: '67'},
    (41, 82, OTHER, 'shillings 34'): {1: '..'},
    (41, 82, OTHER, 'unspecified'): {8: '37'},
    (41, 83, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. 1 1'.split())),
    (41, 83, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 812'.split())),
    (41, 83, OTHER, 'shillings 24'): {8: '..'},
    (41, 83, OTHER, 'shillings 27'): {0: '17', 9: '..'},
    (41, 83, OTHER, 'shillings 28'): {3: '..'},
    (41, 83, OTHER, 'shillings 33'): {0: '1'},
    (41, 83, OTHER, 'shillings 6'): {3: '1'},
    (41, 83, OTHER, 'shillings 7'): {5: '1'},
    (41, 83, OTHER, 'shillings 8'): {0: '1', 1: '..', 2: '..', 3: '1', 4: '..', 5: '..', 9: '..', 10: '170'},
    (41, 83, OTHER, 'shillings 9'): {0: '..'},
    (41, 83, OTHER, 'total'): dict(enumerate('569 350 389 301 244 190 173 96 1,229 359 9,049'.split())),
    (41, 83, OTHER, 'wagons'): dict(enumerate('.. .. .. .. .. .. .. .. ..'.split())),
    (42, 84, PRIVATE, 'pounds 2 15'): {3: '..', 4: '..', 6: '..'},
    (42, 84, PRIVATE, 'pounds 2 5'): {3: '1'},
    (42, 84, PRIVATE, 'pounds 3 5'): {5: '..'},
    (42, 84, PRIVATE, 'pounds 4 10'): {7: '..'},
    (42, 84, PRIVATE, 'pounds 5 0'): {6: '2', 10: '1'},
    (42, 84, PRIVATE, 'pounds 7 0'): {6: '..', 10: '1'},
    (42, 84, PRIVATE, 'shillings 1'): {6: '10', 4: 'UNREADABLE: obscured leading glyph; suffix 46'},
    (42, 84, PRIVATE, 'shillings 17'): {8: '77'},
    (42, 84, PRIVATE, 'shillings 2'): {4: '372', 9: '1', 0: '1,509', 1: '1,664', 2: '872', 3: '931', 5: '147', 6: '45', 7: '8', 8: '7', 10: '..'},
    (42, 84, PRIVATE, 'shillings 24'): {1: '1'},
    (42, 84, PRIVATE, 'shillings 29'): {5: '..', 6: '..'},
    (42, 84, PRIVATE, 'shillings 33'): {1: '1', 5: '..'},
    (42, 84, PRIVATE, 'shillings 34'): {8: '1', 9: '1'},
    (42, 84, PRIVATE, 'shillings 35'): {2: '1', 3: '1'},
    (42, 84, PRIVATE, 'shillings 36'): {3: '..', 4: '4', 6: '..'},
    (42, 84, PRIVATE, 'shillings 37'): {7: '1'},
    (42, 84, PRIVATE, 'shillings 38'): {7: '..'},
    (42, 84, PRIVATE, 'total'): {3: '22,979', 4: '24,648', 5: '19,366', 6: '10,779', 9: '1,710'},
    (42, 84, PRIVATE, 'under 1s'): {2: '11', 4: 'UNREADABLE: obscured leading glyph; suffix 3'},
    (42, 84, PRIVATE, 'unspecified'): {6: '991', 10: '96'},
    (42, 85, PRIVATE, 'pounds 10 0 over'): dict(enumerate('.. 1 .. .. .. .. .. .. .. .. 1'.split())),
    (42, 85, PRIVATE, 'pounds 3 15'): {8: '2', 9: '..'},
    (42, 85, PRIVATE, 'pounds 6 0'): {0: '1', 2: '2', 3: '2', 4: '1', 8: '1', 10: '9'},
    (42, 85, PRIVATE, 'pounds 7 0'): dict(enumerate('.. .. .. .. .. .. 1 .. .. .. 2'.split())),
    (42, 85, PRIVATE, 'shillings 11'): {2: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..'},
    (42, 85, PRIVATE, 'shillings 13'): {8: '..'},
    (42, 85, PRIVATE, 'shillings 14'): {1: '..', 2: '1'},
    (42, 85, PRIVATE, 'shillings 15'): {5: '1', 6: '1', 8: '1'},
    (42, 85, PRIVATE, 'shillings 16'): {6: '..', 8: '..', 9: '1'},
    (42, 85, PRIVATE, 'shillings 17'): {2: '1', 9: '..'},
    (42, 85, PRIVATE, 'shillings 18'): {4: '1'},
    (42, 85, PRIVATE, 'shillings 19'): {0: '..', 1: '..', 4: '..'},
    (42, 85, PRIVATE, 'shillings 20'): {2: '30'},
    (42, 85, PRIVATE, 'shillings 21'): {7: '..'},
    (42, 85, PRIVATE, 'shillings 22'): {1: '1', 2: '2'},
    (42, 85, PRIVATE, 'shillings 23'): {1: '1', 2: '..', 8: '..'},
    (42, 85, PRIVATE, 'shillings 24'): {0: '..', 1: '..', 8: '1'},
    (42, 85, PRIVATE, 'shillings 27'): {3: '1'},
    (42, 85, PRIVATE, 'shillings 3'): {0: '..', 9: '..'},
    (42, 85, PRIVATE, 'shillings 5'): {1: '1', 2: '1', 5: '1', 7: '..'},
    (42, 85, PRIVATE, 'shillings 6'): {1: '1', 2: '..', 5: '..'},
    (42, 85, PRIVATE, 'shillings 7'): {4: '1', 0: '3', 1: '..', 2: '2', 3: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '2', 10: '8,459'},
    (42, 85, PRIVATE, 'shillings 8'): {3: '1', 4: '1'},
    (42, 85, PRIVATE, 'shillings 9'): {0: '..', 1: '..', 3: '..', 4: '..'},
    (42, 85, PRIVATE, 'total'): dict(enumerate('509 178 183 98 74 29 23 18 91 486 121,753'.split())),
    (42, 85, PRIVATE, 'under 1s'): {9: '1', 10: '557'},
    (42, 85, PRIVATE, 'unspecified'): {3: '23'},
    (42, 86, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (42, 86, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (42, 86, OTHER, 'pounds 2 10'): {3: '..'},
    (42, 86, OTHER, 'pounds 2 5'): {4: '..', 6: '..', 8: '..'},
    (42, 86, OTHER, 'pounds 3 10'): {10: '1'},
    (42, 86, OTHER, 'pounds 3 15'): {8: '..', 9: '..', 10: '1'},
    (42, 86, OTHER, 'shillings 18'): {4: '..'},
    (42, 86, OTHER, 'shillings 19'): {5: '..'},
    (42, 86, OTHER, 'shillings 2'): {2: '4', 4: '2', 9: '..'},
    (42, 86, OTHER, 'shillings 22'): {4: '..'},
    (42, 86, OTHER, 'shillings 24'): {6: '..'},
    (42, 86, OTHER, 'shillings 25'): {2: '1', 3: '1'},
    (42, 86, OTHER, 'shillings 27'): {6: '1', 10: '1'},
    (42, 86, OTHER, 'shillings 29'): {8: '..'},
    (42, 86, OTHER, 'shillings 3'): {8: '1'},
    (42, 86, OTHER, 'shillings 30'): {4: '1'},
    (42, 86, OTHER, 'shillings 33'): {8: '..', 9: '..'},
    (42, 86, OTHER, 'shillings 36'): {5: '..', 8: '..', 9: '..'},
    (42, 86, OTHER, 'shillings 38'): {6: '..', 9: '..'},
    (42, 86, OTHER, 'total'): dict(enumerate('39 40 61 95 203 231 264 254 212 228 157'.split())),
    (42, 87, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. 50 50'.split())),
    (42, 87, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 998'.split())),
    (42, 87, OTHER, 'pounds 4 10'): {2: '1'},
    (42, 87, OTHER, 'shillings 23'): {1: '..', 0: '1', 2: '1', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '12'},
    (42, 87, OTHER, 'shillings 27'): {0: '1'},
    (42, 87, OTHER, 'shillings 28'): {0: '..', 1: '3', 2: '1', 3: '..', 4: '..', 6: '..', 8: '..', 10: '7'},
    (42, 87, OTHER, 'shillings 33'): {0: '..', 1: '..', 2: '..', 6: '..'},
    (42, 87, OTHER, 'shillings 36'): {1: '..', 2: '..', 3: '..'},
    (43, 88, PRIVATE, 'pounds 10 0 over'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (43, 88, PRIVATE, 'pounds 2 10'): {4: '1', 5: '1', 7: '2', 8: '8', 9: '10', 10: '8'},
    (43, 88, PRIVATE, 'shillings 1'): {3: '172', 4: '32', 8: '1'},
    (43, 88, PRIVATE, 'shillings 2'): {4: '227'},
    (43, 88, PRIVATE, 'shillings 27'): {1: '1', 3: '..', 6: '52', 7: '49', 8: '24', 9: '12', 10: '4'},
    (43, 88, PRIVATE, 'shillings 3'): {4: '391', 8: '2'},
    (43, 88, PRIVATE, 'shillings 34'): {3: '1', 7: '2', 8: '7', 9: '3', 10: '3'},
    (43, 88, PRIVATE, 'shillings 35'): {3: '1', 6: '22', 7: '22', 8: '37', 9: '34', 10: '12'},
    (43, 88, PRIVATE, 'shillings 4'): {4: '645', 8: '7'},
    (43, 88, PRIVATE, 'shillings 5'): {4: '1,613', 6: '281', 7: '94', 8: '26', 9: '10', 10: '1'},
    (43, 88, PRIVATE, 'total'): {5: '14,048'},
    (43, 88, PRIVATE, 'under 1s'): {3: '17', 4: '10'},
    (43, 88, PRIVATE, 'unspecified'): dict(enumerate('1,733 623 766 1,952 1,538 1,262 673 362 144 110 31'.split())),
    (43, 89, PRIVATE, 'shillings 15'): {0: '11'},
    (43, 90, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (43, 90, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (43, 90, OTHER, 'pounds 2 10'): {4: '1', 6: '1', 3: '..'},
    (43, 90, OTHER, 'pounds 3 10'): {10: '1'},
    (43, 90, OTHER, 'pounds 3 15'): {10: '1'},
    (43, 90, OTHER, 'pounds 4 0'): {9: '1', 8: '1'},
    (43, 90, OTHER, 'pounds 4 15'): {9: '1'},
    (43, 90, OTHER, 'shillings 11'): {8: '2'},
    (43, 90, OTHER, 'shillings 30'): {4: '1', 3: '1'},
    (43, 90, OTHER, 'shillings 32'): {6: '1'},
    (43, 90, OTHER, 'shillings 5'): {10: '1'},
    (43, 90, OTHER, 'shillings 8'): {10: '1'},
    (43, 91, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. 18 18'.split())),
    (43, 91, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 258'.split())),
    (43, 91, OTHER, 'shillings 36'): dict(enumerate('.. .. 2 .. .. .. 1 .. .. .. 3'.split())),
    (43, 91, OTHER, 'shillings 38'): {10: '1'},
    (43, 91, OTHER, 'wagons'): {9: '18', 10: '18'},
    (44, 92, PRIVATE, 'shillings 2'): {7: '1'},
    (44, 92, PRIVATE, 'total'): dict(enumerate('13,893 6,418 8,316 17,656 9,680 5,620 2,215 1,149 536 336 124'.split())),
    (44, 92, PRIVATE, 'unspecified'): {6: '321', 0: '8,761', 1: '1,848', 2: '1,494', 3: '2,280', 4: '1,209', 5: '774', 7: '204', 8: '76', 9: '74', 10: '26'},
    (44, 93, PRIVATE, 'shillings 14'): {9: '1', 0: '..', 1: '..'},
    (44, 93, PRIVATE, 'total'): dict(enumerate('129 56 46 19 23 13 7 3 23 291 66,553'.split())),
    (44, 94, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (44, 94, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (44, 94, OTHER, 'pounds 10 0 over'): {8: '1', 9: '1', 10: '1'},
    (44, 94, OTHER, 'pounds 2 10'): {5: '1', 6: '..'},
    (44, 94, OTHER, 'pounds 3 0'): {6: '1', 8: '1'},
    (44, 94, OTHER, 'pounds 3 10'): {10: '1', 8: '..'},
    (44, 94, OTHER, 'pounds 5 0'): {7: '1', 10: '2'},
    (44, 94, OTHER, 'pounds 6 0'): {6: '1'},
    (44, 94, OTHER, 'pounds 7 0'): {8: '1', 10: '1'},
    (44, 94, OTHER, 'shillings 12'): {7: '3'},
    (44, 94, OTHER, 'shillings 13'): {9: '1', 8: '..'},
    (44, 94, OTHER, 'shillings 14'): {2: '1'},
    (44, 94, OTHER, 'shillings 15'): {6: '8'},
    (44, 94, OTHER, 'shillings 16'): {5: '8', 9: '1', 2: '..', 3: '..', 10: '..'},
    (44, 94, OTHER, 'shillings 18'): {9: '1', 10: '..'},
    (44, 94, OTHER, 'shillings 19'): {5: '1', 7: '..', 9: '..'},
    (44, 94, OTHER, 'shillings 20'): {3: '8', 7: '28'},
    (44, 94, OTHER, 'shillings 26'): {7: '1', 10: '1'},
    (44, 94, OTHER, 'shillings 30'): {4: '8'},
    (44, 94, OTHER, 'shillings 31'): {9: '1', 7: '..', 8: '1', 10: '..'},
    (44, 94, OTHER, 'shillings 34'): {9: '1'},
    (44, 94, OTHER, 'shillings 37'): {6: '1'},
    (44, 94, OTHER, 'shillings 39'): {10: '1', 7: '..'},
    (44, 94, OTHER, 'shillings 4'): {9: '1', 2: '1'},
    (44, 94, OTHER, 'shillings 6'): {2: '2', 10: '1', 7: '..', 9: '..'},
    (44, 94, OTHER, 'shillings 7'): {2: '4', 10: '1'},
    (44, 94, OTHER, 'shillings 8'): {2: '4', 4: '8', 10: '..'},
    (44, 94, OTHER, 'total'): {7: '159', 0: '13', 1: '26', 2: '62', 3: '154', 4: '172', 5: '169', 6: '142', 8: '139', 9: '139', 10: '98'},
    (44, 94, OTHER, 'unspecified'): {8: '18'},
    (44, 95, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. 80 80'.split())),
    (44, 95, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1,449'.split())),
    (44, 95, OTHER, 'total'): {3: '62', 6: '47', 7: '33', 0: '112', 1: '70', 2: '85', 4: '65', 5: '48', 8: '393', 9: '129', 10: '2,317'},
    (45, 96, PRIVATE, 'pounds 2 10'): {7: '1', 1: '..', 6: '..', 8: '1', 9: '2', 10: '1'},
    (45, 96, PRIVATE, 'pounds 2 15'): {6: '..', 0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '1', 7: '..', 8: '..', 9: '1', 10: '..'},
    (45, 96, PRIVATE, 'shillings 14'): {4: '122', 2: '..'},
    (45, 96, PRIVATE, 'shillings 19'): {1: '1', 2: '..', 4: '..', 9: '..'},
    (45, 96, PRIVATE, 'shillings 28'): {4: '1', 3: '..'},
    (45, 96, PRIVATE, 'shillings 29'): {4: '1', 7: '..', 8: '..', 9: '1', 10: '2'},
    (45, 96, PRIVATE, 'shillings 32'): {10: '1', 9: '3'},
    (45, 96, PRIVATE, 'shillings 33'): {10: '1', 4: '..', 5: '..', 6: '..', 7: '..', 9: '..'},
    (45, 96, PRIVATE, 'shillings 36'): dict(enumerate('.. .. .. .. .. 1 .. .. 1 .. ..'.split())),
    (45, 96, PRIVATE, 'shillings 39'): {6: '1'},
    (45, 96, PRIVATE, 'unspecified'): {0: '926', 1: '458', 2: '423', 3: '1,135', 4: '799', 5: '722', 6: '350', 7: '242', 8: '122', 9: '81', 10: '36'},
    (45, 97, PRIVATE, 'shillings 4'): {2: '1'},
    (45, 98, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (45, 98, OTHER, 'pounds 3 10'): {7: '1', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'shillings 1'): {1: '1'},
    (45, 98, OTHER, 'shillings 10'): {10: '1'},
    (45, 98, OTHER, 'shillings 12'): {10: '1'},
    (45, 98, OTHER, 'shillings 2'): {1: '1'},
    (45, 98, OTHER, 'shillings 23'): {6: '1', 10: '..'},
    (45, 98, OTHER, 'shillings 4'): {10: '1'},
    (45, 98, OTHER, 'shillings 6'): {1: '1'},
    (45, 98, OTHER, 'shillings 7'): {2: '1', 10: '1'},
    (45, 98, OTHER, 'shillings 8'): {2: '1', 10: '1'},
    (45, 98, OTHER, 'wagons'): {0: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 99, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 86'.split())),
    (45, 99, OTHER, 'pounds 3 0'): {9: '1'},
    (45, 99, OTHER, 'pounds 3 10'): {6: '1'},
    (45, 99, OTHER, 'pounds 4 0'): {2: '1', 6: '1'},
    (45, 99, OTHER, 'pounds 4 10'): {4: '1'},
    (45, 99, OTHER, 'shillings 32'): {7: '1'},
    (45, 99, OTHER, 'shillings 36'): {6: '1'},
    (46, 100, PRIVATE, 'shillings 1'): dict(enumerate('169 53 6 2 1 .. .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 10'): dict(enumerate('1 9 10 9 6 6 2 .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 11'): dict(enumerate('.. .. .. 1 1 3 1 .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 12'): dict(enumerate('.. .. 1 4 3 4 .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 15'): dict(enumerate('.. 1 1 3 2 2 .. 1 .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 17'): dict(enumerate('.. .. .. 1 .. .. 1 1 .. 1 ..'.split())),
    (46, 100, PRIVATE, 'shillings 2'): dict(enumerate('44 103 19 6 .. .. .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 20'): dict(enumerate('.. .. .. 4 2 2 2 2 .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 25'): dict(enumerate('.. .. .. .. 1 .. 1 1 .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 3'): dict(enumerate('4 30 22 8 3 .. .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 4'): dict(enumerate('2 7 6 7 3 .. .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 5'): dict(enumerate('15 21 13 9 5 3 .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 6'): dict(enumerate('.. 4 9 2 2 1 .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 7'): dict(enumerate('.. 6 5 4 1 1 .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'shillings 8'): dict(enumerate('.. .. 2 1 .. 1 .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'total'): dict(enumerate('613 283 111 81 45 31 13 9 1 1 ..'.split())),
    (46, 100, PRIVATE, 'under 1s'): dict(enumerate('86 4 .. .. .. .. .. .. .. .. ..'.split())),
    (46, 100, PRIVATE, 'unspecified'): dict(enumerate('292 45 17 20 15 8 6 4 1 .. ..'.split())),
    (46, 100, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'pounds 2 5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'pounds 3 0'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'pounds 3 10'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'pounds 5 0'): dict(enumerate('.. .. .. .. .. .. .. .. 1 .. ..'.split())),
    (46, 100, OTHER, 'shillings 10'): dict(enumerate('.. .. .. .. .. .. .. 1 .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 12'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 14'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 15'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 2'): dict(enumerate('.. 1 .. .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 20'): dict(enumerate('.. .. .. 1 .. 1 .. 1 .. 1 ..'.split())),
    (46, 100, OTHER, 'shillings 32'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 100, OTHER, 'shillings 5'): dict(enumerate('.. .. .. 1 .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 7'): dict(enumerate('.. .. 1 .. .. .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 8'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'shillings 9'): dict(enumerate('.. .. .. .. .. 1 .. .. .. .. ..'.split())),
    (46, 100, OTHER, 'total'): dict(enumerate('1 5 3 5 1 4 .. 2 2 1 1'.split())),
    (46, 100, OTHER, 'unspecified'): dict(enumerate('1 4 1 1 .. 2 .. .. 1 .. ..'.split())),
    (46, 101, PRIVATE, 'shillings 1'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 231'.split())),
    (46, 101, PRIVATE, 'shillings 10'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 43'.split())),
    (46, 101, PRIVATE, 'shillings 11'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 6'.split())),
    (46, 101, PRIVATE, 'shillings 12'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 12'.split())),
    (46, 101, PRIVATE, 'shillings 15'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 10'.split())),
    (46, 101, PRIVATE, 'shillings 17'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 4'.split())),
    (46, 101, PRIVATE, 'shillings 2'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 172'.split())),
    (46, 101, PRIVATE, 'shillings 20'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 12'.split())),
    (46, 101, PRIVATE, 'shillings 25'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 3'.split())),
    (46, 101, PRIVATE, 'shillings 3'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 67'.split())),
    (46, 101, PRIVATE, 'shillings 4'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 25'.split())),
    (46, 101, PRIVATE, 'shillings 5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 66'.split())),
    (46, 101, PRIVATE, 'shillings 6'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 18'.split())),
    (46, 101, PRIVATE, 'shillings 7'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 17'.split())),
    (46, 101, PRIVATE, 'shillings 8'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 4'.split())),
    (46, 101, PRIVATE, 'total'): dict(enumerate('.. .. .. .. .. .. .. .. .. 6 1,194'.split())),
    (46, 101, PRIVATE, 'under 1s'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 90'.split())),
    (46, 101, PRIVATE, 'unspecified'): dict(enumerate('.. .. .. .. .. .. .. .. .. 6 414'.split())),
    (46, 101, OTHER, 'aboriginal camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. 21 21'.split())),
    (46, 101, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 60'.split())),
    (46, 101, OTHER, 'pounds 2 5'): dict(enumerate('.. 1 .. .. .. .. .. .. 1 .. 2'.split())),
    (46, 101, OTHER, 'pounds 3 0'): dict(enumerate('.. .. .. 1 .. .. .. .. 1 .. 2'.split())),
    (46, 101, OTHER, 'pounds 3 10'): dict(enumerate('.. .. .. .. .. .. .. .. 1 .. 1'.split())),
    (46, 101, OTHER, 'pounds 5 0'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 10'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 12'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 14'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 15'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 2'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 20'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 4'.split())),
    (46, 101, OTHER, 'shillings 32'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 7'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 8'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'shillings 9'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (46, 101, OTHER, 'total'): dict(enumerate('.. 1 .. 1 1 .. .. .. 3 23 54'.split())),
    (46, 101, OTHER, 'unspecified'): dict(enumerate('.. .. .. .. 1 .. .. .. .. 2 13'.split())),
    (47, 100, PRIVATE, 'pounds 2 0'): dict(enumerate('.. .. .. .. .. .. .. .. .. 1 ..'.split())),
    (47, 100, PRIVATE, 'shillings 1'): dict(enumerate('9 2 3 4 1 1 .. 1 .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 10'): dict(enumerate('.. .. .. 2 5 6 3 1 2 1 ..'.split())),
    (47, 100, PRIVATE, 'shillings 11'): dict(enumerate('.. .. .. .. *2 .. 1 1 .. .. 1'.split())),
    (47, 100, PRIVATE, 'shillings 12'): dict(enumerate('.. .. .. 1 .. 1 2 .. .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 15'): dict(enumerate('.. .. .. .. 1 .. †2 1 .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 2'): dict(enumerate('1 2 1 6 3 1 .. .. .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 20'): dict(enumerate('.. .. .. .. .. .. 2 .. .. 3 1'.split())),
    (47, 100, PRIVATE, 'shillings 25'): dict(enumerate('.. .. .. .. .. .. .. 1 .. 2 ..'.split())),
    (47, 100, PRIVATE, 'shillings 3'): dict(enumerate('.. 4 1 2 2 1 .. .. .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 30'): dict(enumerate('.. .. .. .. .. .. .. .. .. 1 ..'.split())),
    (47, 100, PRIVATE, 'shillings 4'): dict(enumerate('.. 1 1 2 .. 3 .. .. .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 5'): dict(enumerate('.. 2 4 8 11 9 2 1 .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 6'): dict(enumerate('.. .. 1 1 3 2 1 .. .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 7'): dict(enumerate('.. 1 .. 4 6 2 1 .. 1 .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 8'): dict(enumerate('.. .. .. .. 1 4 3 1 .. .. ..'.split())),
    (47, 100, PRIVATE, 'shillings 9'): dict(enumerate('.. .. .. .. .. 1 2 .. .. .. ..'.split())),
    (47, 100, PRIVATE, 'total'): dict(enumerate('136 25 19 60 57 49 30 19 7 8 6'.split())),
    (47, 100, PRIVATE, 'unspecified'): dict(enumerate('126 13 8 30 22 18 11 11 4 1 4'.split())),
    (47, 100, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (47, 100, OTHER, 'pounds 2 0'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (47, 100, OTHER, 'shillings 10'): dict(enumerate('.. .. .. .. .. 1 .. .. .. .. ..'.split())),
    (47, 100, OTHER, 'shillings 12'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. ..'.split())),
    (47, 100, OTHER, 'shillings 3'): dict(enumerate('.. .. .. .. 1 .. .. .. .. .. ..'.split())),
    (47, 100, OTHER, 'total'): dict(enumerate('2 1 .. .. 3 1 .. 1 .. .. ..'.split())),
    (47, 100, OTHER, 'unspecified'): dict(enumerate('2 1 .. .. 1 .. .. 1 .. .. ..'.split())),
    (47, 101, PRIVATE, 'pounds 2 0'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (47, 101, PRIVATE, 'shillings 1'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 21'.split())),
    (47, 101, PRIVATE, 'shillings 10'): dict(enumerate('.. .. .. .. .. .. .. .. 1 .. 21'.split())),
    (47, 101, PRIVATE, 'shillings 11'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 5'.split())),
    (47, 101, PRIVATE, 'shillings 12'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 4'.split())),
    (47, 101, PRIVATE, 'shillings 15'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 4'.split())),
    (47, 101, PRIVATE, 'shillings 2'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 14'.split())),
    (47, 101, PRIVATE, 'shillings 20'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 6'.split())),
    (47, 101, PRIVATE, 'shillings 25'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 3'.split())),
    (47, 101, PRIVATE, 'shillings 3'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 10'.split())),
    (47, 101, PRIVATE, 'shillings 30'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (47, 101, PRIVATE, 'shillings 4'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 7'.split())),
    (47, 101, PRIVATE, 'shillings 5'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 37'.split())),
    (47, 101, PRIVATE, 'shillings 6'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 8'.split())),
    (47, 101, PRIVATE, 'shillings 7'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 15'.split())),
    (47, 101, PRIVATE, 'shillings 8'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 9'.split())),
    (47, 101, PRIVATE, 'shillings 9'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 3'.split())),
    (47, 101, PRIVATE, 'total'): dict(enumerate('2 .. 2 .. 1 .. .. 1 3 6 431'.split())),
    (47, 101, PRIVATE, 'unspecified'): dict(enumerate('2 .. 2 .. 1 .. .. 1 2 6 262'.split())),
    (47, 101, OTHER, 'other camps'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 2'.split())),
    (47, 101, OTHER, 'pounds 2 0'): dict(enumerate('.. 1 .. .. .. .. .. .. .. .. 1'.split())),
    (47, 101, OTHER, 'shillings 10'): dict(enumerate('.. 1 .. .. .. .. .. .. .. .. 2'.split())),
    (47, 101, OTHER, 'shillings 12'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (47, 101, OTHER, 'shillings 3'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. 1'.split())),
    (47, 101, OTHER, 'total'): dict(enumerate('.. 2 .. .. .. .. .. .. 1 .. 11'.split())),
    (47, 101, OTHER, 'unspecified'): dict(enumerate('.. .. .. .. .. .. .. .. 1 .. 6'.split())),
    (48, 102, METHODS[0], 'pounds 10 0 over'): dict(enumerate('.. .. .. .. .. .. .. .. .. .. ..'.split())),
    (48, 102, METHODS[0], 'pounds 2 10'): {9: '125'},
    (48, 102, METHODS[0], 'shillings 30'): {7: '1,289'},
    (48, 103, METHODS[0], 'shillings 25'): {1: '71'},
    (48, 104, METHODS[1], 'total'): {5: '7,101'},
    (48, 105, METHODS[1], 'shillings 1'): {9: '1'},
    (48, 105, METHODS[1], 'shillings 10'): {3: '1', 4: '1', 1: '1'},
    (48, 105, METHODS[1], 'shillings 12'): {10: '3,272', 9: '..'},
    (48, 105, METHODS[1], 'shillings 13'): {9: '1'},
    (48, 105, METHODS[1], 'shillings 14'): {9: '1'},
    (48, 105, METHODS[1], 'shillings 15'): {1: '1'},
    (48, 105, METHODS[1], 'total'): {5: '3'},
    (48, 106, METHODS[2], 'total'): {1: '18,487', 4: '96,422'},
    (48, 107, METHODS[2], 'shillings 32'): {9: '1'},
    (48, 108, METHODS[3], 'pounds 4 0'): {9: '1'},
    (48, 108, METHODS[3], 'shillings 13'): {10: '1'},
    (48, 108, METHODS[3], 'shillings 17'): {1: '1', 9: '1', 7: '11'},
    (48, 108, METHODS[3], 'shillings 21'): {1: '1', 0: '..', 2: '..', 3: '..', 4: '..', 5: '4', 6: '11', 7: '11', 8: '2', 9: '1', 10: '..'},
    (48, 108, METHODS[3], 'shillings 22'): {1: '1', 9: '1'},
    (48, 108, METHODS[3], 'shillings 27'): {4: '1', 6: '4'},
    (48, 108, METHODS[3], 'shillings 30'): {1: '1'},
    (48, 108, METHODS[3], 'shillings 34'): {4: '1'},
    (48, 108, METHODS[3], 'shillings 35'): {2: '1', 3: '1', 4: '1', 9: '11'},
    (48, 108, METHODS[3], 'shillings 37'): {9: '1'},
    (48, 108, METHODS[3], 'shillings 38'): {4: '1', 7: '1'},
    (48, 108, METHODS[3], 'total'): {2: '2,864', 3: '6,858', 0: '17,176', 1: '3,127', 4: '5,115', 5: 'UNREADABLE: [4,035', 6: '2,083', 7: '1,283', 8: '752', 9: '566', 10: '253'},
    (48, 109, METHODS[3], 'unspecified'): {10: '28,945'},
    (30, 55, OTHER, 'aboriginal camps'): {0: '3', 1: '1', 2: '..'},
    (31, 56, OTHER, '1'): {6: '2'},
    (31, 57, OTHER, '3'): {1: '..'},
    (31, 57, PRIVATE, '10'): {9: '4'},
    (32, 59, ALL, '3'): {5: '1'},
    (32, 59, ALL, '5'): {5: '4'},
    (32, 59, ALL, 'wagons'): {8: '..'},
    (33, 61, OTHER, '10'): {5: '3'},
    (33, 61, OTHER, '15'): {2: '9'},
    (33, 61, OTHER, 'wagons'): {2: '..'},
    (34, 63, ALL, 'wagons'): {5: '..'},
    (34, 63, PRIVATE, '18'): {2: '..'},
    (35, 64, OTHER, '1'): {3: '..', 4: '..', 5: '..', 8: '..', 9: '..'},
    (35, 64, PRIVATE, '19'): {8: '..', 9: '..'},
    (35, 65, OTHER, '6'): {7: '..'},
    (35, 65, OTHER, 'aboriginal camps'): {8: '..'},
    (36, 66, OTHER, '11'): {6: '2'},
    (36, 66, OTHER, '19'): {3: '1', 5: '1', 7: '1'},
    (36, 66, PRIVATE, '16'): {5: ''},
    (36, 67, ALL, '1'): {0: '1', 2: '..', 3: '1'},
    (36, 67, ALL, '18'): {2: '2', 3: '..', 6: '..'},
    (36, 67, OTHER, '10'): {4: '..', 5: '2', 6: '..', 8: '..'},
    (39, 74, OTHER, 'shillings 1'): {9: '1'},
    (39, 75, OTHER, 'shillings 4'): {9: '1'},
    (40, 77, PRIVATE, 'shillings 12'): {1: 'UNREADABLE: obscured digit; visible 1'},
    (41, 80, PRIVATE, 'shillings 19'): {2: '..'},
    (41, 81, PRIVATE, 'pounds 9 0'): {8: '1'},
    (41, 81, PRIVATE, 'total'): {10: '263,634'},
    (42, 84, PRIVATE, 'shillings 7'): {0: '45', 1: '166', 2: '468', 3: '2,666', 4: '2,610', 5: '1,456', 6: '725', 7: '207', 8: '70', 9: '28', 10: '10'},
    (42, 85, PRIVATE, 'shillings 2'): {0: '2', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '2', 10: '5,560'},
    (42, 86, OTHER, 'pounds 4 0'): {8: '1'},
    (42, 86, OTHER, 'pounds 4 15'): {8: '..'},
    (42, 86, OTHER, 'pounds 4 5'): {8: '..', 9: '..', 10: '..'},
    (42, 86, OTHER, 'pounds 8 0'): {7: '..', 9: '..'},
    (42, 86, OTHER, 'shillings 23'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '1', 6: '1', 7: '2', 8: '2', 9: '3', 10: '1'},
    (42, 86, OTHER, 'wagons'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (42, 87, OTHER, 'pounds 7 0'): {3: '..'},
    (42, 87, OTHER, 'pounds 9 0'): {3: '..'},
    (43, 88, PRIVATE, 'pounds 2 15'): {5: '2', 6: '..', 7: '..', 8: '..', 9: '2', 10: '2'},
    (43, 88, PRIVATE, 'pounds 2 5'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '3', 6: '1', 7: '4', 8: '6', 9: '7', 10: '5'},
    (43, 88, PRIVATE, 'pounds 3 10'): {6: '..', 7: '..', 8: '..', 9: '2'},
    (43, 88, PRIVATE, 'pounds 3 15'): {7: '..', 8: '1', 9: '..', 10: '1'},
    (43, 88, PRIVATE, 'pounds 3 5'): {5: '..', 6: '1', 7: '..', 8: '..'},
    (43, 88, PRIVATE, 'pounds 4 0'): {8: '1', 9: '3', 10: '3'},
    (43, 88, PRIVATE, 'pounds 4 10'): {7: '..', 8: '..', 9: '..', 10: '1'},
    (43, 88, PRIVATE, 'pounds 5 0'): {6: '1'},
    (43, 88, PRIVATE, 'pounds 9 0'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (43, 88, PRIVATE, 'shillings 19'): {1: '1', 5: '26', 6: '17', 7: '7', 8: '3', 9: '1', 10: '1'},
    (43, 88, PRIVATE, 'shillings 20'): {0: '1', 1: '..', 2: '15', 3: '108', 4: '482', 5: '1,212', 6: '835', 7: '459', 8: '215', 9: '115', 10: '54'},
    (43, 88, PRIVATE, 'shillings 26'): {2: '..'},
    (43, 88, PRIVATE, 'shillings 28'): {1: '..'},
    (43, 88, PRIVATE, 'shillings 29'): {6: '4', 7: '6', 9: '4'},
    (43, 88, PRIVATE, 'shillings 33'): {7: '4', 8: '2', 9: '..', 10: '1'},
    (43, 88, PRIVATE, 'shillings 37'): {4: '2', 5: '..', 6: '4', 7: '..', 8: '2', 9: '..'},
    (43, 88, PRIVATE, 'shillings 38'): {5: '2', 6: '2', 7: '2', 8: '..', 9: '3'},
    (43, 88, PRIVATE, 'shillings 39'): {8: '1'},
    (43, 88, PRIVATE, 'shillings 7'): {7: '65', 9: '13', 10: '3'},
    (43, 89, PRIVATE, 'pounds 2 5'): {0: '4', 1: '3', 2: '5', 3: '..', 4: '..', 5: '1', 6: '..', 7: '..', 8: '..', 9: '1', 10: '40'},
    (43, 89, PRIVATE, 'pounds 9 0'): {0: '..', 1: '..', 2: '..', 3: '1', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '1'},
    (43, 89, PRIVATE, 'shillings 20'): {0: '47', 1: '11', 2: '13', 3: '4', 4: '5', 5: '2', 6: '..', 7: '1', 8: '3', 9: '5', 10: '3,587'},
    (43, 90, OTHER, 'pounds 2 0'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '1', 5: '..', 6: '..', 7: '1', 8: '2', 9: '4', 10: '11'},
    (43, 90, OTHER, 'pounds 4 10'): {7: '1'},
    (43, 90, OTHER, 'pounds 5 0'): {9: '1'},
    (43, 90, OTHER, 'shillings 1'): {0: '..', 8: '..', 9: '..'},
    (43, 90, OTHER, 'shillings 13'): {0: '..', 9: '..'},
    (43, 90, OTHER, 'shillings 14'): {3: '..'},
    (43, 90, OTHER, 'shillings 2'): {0: '..'},
    (43, 90, OTHER, 'shillings 23'): {9: '..'},
    (43, 90, OTHER, 'shillings 26'): {4: '1'},
    (43, 90, OTHER, 'shillings 27'): {4: '..'},
    (43, 90, OTHER, 'shillings 3'): {0: '..', 9: '..'},
    (43, 90, OTHER, 'shillings 33'): {9: '..', 10: '..'},
    (43, 90, OTHER, 'shillings 38'): {10: '..'},
    (43, 90, OTHER, 'shillings 4'): {0: '..', 1: '..'},
    (43, 90, OTHER, 'shillings 9'): {2: '..', 10: '..'},
    (43, 91, OTHER, 'pounds 2 0'): {0: '10', 1: '6', 2: '9', 3: '6', 4: '12', 5: '9', 6: '6', 7: '..', 8: '19', 9: '..', 10: '6'},
    (44, 92, PRIVATE, 'pounds 2 15'): {3: '..'},
    (44, 92, PRIVATE, 'pounds 3 0'): {4: '1'},
    (44, 92, PRIVATE, 'pounds 3 5'): {4: '1'},
    (44, 92, PRIVATE, 'pounds 5 0'): {7: '1'},
    (44, 92, PRIVATE, 'shillings 13'): {10: '..'},
    (44, 92, PRIVATE, 'shillings 16'): {10: '..'},
    (44, 92, PRIVATE, 'shillings 17'): {10: '1'},
    (44, 92, PRIVATE, 'shillings 18'): {10: '..'},
    (44, 92, PRIVATE, 'shillings 21'): {10: '..'},
    (44, 92, PRIVATE, 'shillings 22'): {5: '111'},
    (44, 92, PRIVATE, 'shillings 28'): {9: '..', 10: '..'},
    (44, 92, PRIVATE, 'shillings 3'): {8: '1'},
    (44, 92, PRIVATE, 'shillings 33'): {2: '..'},
    (44, 92, PRIVATE, 'shillings 34'): {5: '..', 7: '..'},
    (44, 92, PRIVATE, 'shillings 37'): {2: '1', 8: '1'},
    (44, 92, PRIVATE, 'shillings 38'): {2: '..', 4: '..', 10: '..'},
    (44, 92, PRIVATE, 'shillings 6'): {10: '..'},
    (44, 93, PRIVATE, 'pounds 6 0'): {2: '..', 4: '..', 6: '..'},
    (44, 93, PRIVATE, 'shillings 12'): {1: '..'},
    (44, 93, PRIVATE, 'shillings 15'): {9: '1'},
    (44, 93, PRIVATE, 'shillings 16'): {1: '..'},
    (44, 93, PRIVATE, 'shillings 21'): {0: '..', 4: '..'},
    (44, 93, PRIVATE, 'shillings 7'): {9: '1'},
    (44, 94, OTHER, 'pounds 2 0'): {8: '11', 10: '11'},
    (44, 94, OTHER, 'pounds 2 15'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '1', 9: '1', 10: '2'},
    (44, 94, OTHER, 'pounds 2 5'): {3: '..', 4: '..', 5: '..'},
    (44, 94, OTHER, 'pounds 3 15'): {10: '..'},
    (44, 94, OTHER, 'pounds 4 0'): {0: '..'},
    (44, 94, OTHER, 'pounds 4 5'): {7: '..', 8: '..', 9: '..', 10: '..'},
    (44, 94, OTHER, 'pounds 9 0'): {9: '..', 10: '..'},
    (44, 94, OTHER, 'shillings 17'): {10: '1'},
    (44, 94, OTHER, 'shillings 2'): {8: '1'},
    (44, 94, OTHER, 'shillings 21'): {9: '..'},
    (44, 94, OTHER, 'shillings 23'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '2', 8: '1', 9: '..', 10: '..'},
    (44, 94, OTHER, 'shillings 25'): {2: '1'},
    (44, 94, OTHER, 'shillings 28'): {8: '1'},
    (44, 94, OTHER, 'shillings 3'): {8: '..'},
    (44, 94, OTHER, 'shillings 38'): {8: '..', 10: '..'},
    (44, 94, OTHER, 'shillings 9'): {7: '..'},
    (44, 94, OTHER, 'wagons'): {1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (44, 95, OTHER, 'pounds 2 15'): {0: '1', 1: '1', 2: '..', 3: '1', 4: '..', 5: '..', 6: '1', 7: '..', 8: '2', 9: '..', 10: '10'},
    (44, 95, OTHER, 'shillings 23'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '3'},
    (45, 96, PRIVATE, 'pounds 3 10'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 96, PRIVATE, 'pounds 4 10'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..'},
    (45, 96, PRIVATE, 'pounds 4 15'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 96, PRIVATE, 'shillings 11'): {10: '..'},
    (45, 96, PRIVATE, 'shillings 21'): {2: '..', 10: '..'},
    (45, 96, PRIVATE, 'shillings 30'): {5: '5'},
    (45, 96, PRIVATE, 'shillings 31'): {8: '..', 9: '1', 10: '..'},
    (45, 96, PRIVATE, 'shillings 34'): {8: '..', 10: '2'},
    (45, 97, PRIVATE, 'pounds 2 15'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '2'},
    (45, 97, PRIVATE, 'pounds 4 0'): {1: '..', 2: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..'},
    (45, 97, PRIVATE, 'pounds 4 15'): {1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..'},
    (45, 97, PRIVATE, 'shillings 24'): {0: '..', 5: '..'},
    (45, 97, PRIVATE, 'shillings 36'): {0: '..'},
    (45, 97, PRIVATE, 'shillings 38'): {1: '..'},
    (45, 97, PRIVATE, 'shillings 39'): {1: '..', 3: '..'},
    (45, 98, OTHER, 'pounds 2 10'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 2 15'): {5: '..', 6: '..', 7: '..', 8: '..', 9: '1', 10: '..'},
    (45, 98, OTHER, 'pounds 2 5'): {10: '..'},
    (45, 98, OTHER, 'pounds 3 0'): {7: '1'},
    (45, 98, OTHER, 'pounds 3 15'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 3 5'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 4 10'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '1', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 4 15'): {3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 4 5'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 6 0'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 7 0'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 8 0'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'pounds 9 0'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'shillings 13'): {10: '..'},
    (45, 98, OTHER, 'shillings 14'): {3: '..'},
    (45, 98, OTHER, 'shillings 18'): {5: '..'},
    (45, 98, OTHER, 'shillings 24'): {7: '..'},
    (45, 98, OTHER, 'shillings 29'): {7: '..'},
    (45, 98, OTHER, 'shillings 3'): {3: '..'},
    (45, 98, OTHER, 'shillings 31'): {7: '..', 8: '..', 10: '..'},
    (45, 98, OTHER, 'shillings 33'): {8: '..', 10: '..'},
    (45, 98, OTHER, 'shillings 34'): {2: '..', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'shillings 36'): {5: '..', 6: '..', 7: '..', 8: '..', 9: '..', 10: '..'},
    (45, 98, OTHER, 'shillings 9'): {8: '..'},
    (45, 99, OTHER, 'pounds 3 15'): {0: '..', 2: '..', 6: '..'},
    (45, 99, OTHER, 'pounds 3 5'): {4: '..', 5: '..', 6: '..', 7: '..', 9: '..'},
    (45, 99, OTHER, 'shillings 27'): {6: '..'},
    (45, 99, OTHER, 'shillings 28'): {0: '..', 4: '..'},
    (45, 99, OTHER, 'shillings 33'): {0: '..', 1: '..', 2: '..', 5: '..', 7: '..', 8: '..'},
    (45, 99, OTHER, 'shillings 35'): {5: '1', 7: '1'},
    (48, 104, METHODS[1], 'shillings 4'): {0: '33', 1: '145', 2: '177', 3: '485', 4: '183', 5: '65', 6: '15', 7: '7', 8: '..', 9: '1', 10: '..'},
    (48, 104, METHODS[1], 'unspecified'): {0: '200', 1: '244', 2: '284', 3: '785', 4: '705', 5: '485', 6: '228', 7: '98', 8: '55', 9: '29', 10: '6'},
    (48, 105, METHODS[1], 'pounds 2 5'): {1: '1'},
    (48, 105, METHODS[1], 'pounds 3 10'): {3: '1', 5: '1'},
    (48, 105, METHODS[1], 'pounds 8 0'): {0: '..', 2: '..', 4: '1'},
    (48, 105, METHODS[1], 'shillings 18'): {5: '..'},
    (48, 105, METHODS[1], 'shillings 21'): {2: '..', 6: '..', 8: '..', 9: '..'},
    (48, 105, METHODS[1], 'shillings 23'): {0: '..'},
    (48, 105, METHODS[1], 'shillings 4'): {0: '1', 1: '..', 2: '.', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '1', 10: '1,113'},
    (48, 105, METHODS[1], 'unspecified'): {0: '5', 1: '1', 2: '2', 3: '..', 4: '1', 5: '..', 6: '..', 7: '..', 8: '..', 9: '8', 10: '3,136'},
    (48, 106, METHODS[2], 'pounds 4 15'): {10: '..'},
    (48, 106, METHODS[2], 'pounds 5 0'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '5', 7: '2', 8: '3', 9: '16', 10: '8'},
    (48, 106, METHODS[2], 'shillings 31'): {2: '..'},
    (48, 107, METHODS[2], 'pounds 5 0'): {0: '6', 1: '11', 2: '9', 3: '3', 4: '3', 5: '5', 6: '4', 7: '2', 8: '8', 9: '..', 10: '85'},
    (48, 107, METHODS[2], 'shillings 36'): {6: '..'},
    (48, 108, METHODS[3], 'pounds 5 0'): {8: '1'},
    (48, 108, METHODS[3], 'pounds 6 0'): {9: '1'},
    (48, 108, METHODS[3], 'shillings 1'): {8: '1'},
    (48, 108, METHODS[3], 'shillings 14'): {1: '1'},
    (48, 108, METHODS[3], 'shillings 15'): {0: '1'},
    (48, 108, METHODS[3], 'shillings 16'): {0: '..', 1: '..', 2: '2', 3: '4', 4: '29', 5: '66', 6: '21', 7: '24', 8: '5', 9: '3', 10: '..'},
    (48, 109, METHODS[3], 'shillings 16'): {0: '..', 1: '..', 2: '1', 3: '..', 4: '..', 5: '..', 6: '..', 7: '..', 8: '..', 9: '1', 10: '157'},
    (48, 109, METHODS[3], 'shillings 21'): {0: '..', 1: '..', 2: '..', 3: '..', 4: '..', 5: '..', 6: '1', 7: '..', 8: '..', 9: '..', 10: '31'},
    (48, 109, METHODS[3], 'shillings 6'): {0: '..', 2: '..'},
    (48, 109, METHODS[3], 'total'): {0: '260', 1: '125', 2: '106', 3: '61', 4: '59', 5: '30', 6: '29', 7: '12', 8: '109', 9: '3,160', 10: '48,063'},
}

# Independently inspected row baselines whose label OCR is lost or displaced.
# The labels and values are printed, not inferred from a facing total.
SOURCE_ROW_BASELINES = {
    (32, 58, OTHER, '1'): 376.3,
    (32, 59, OTHER, '1'): 374.5,
    (34, 62, OTHER, '1'): 377.25,
    (34, 62, OTHER, '10'): 449.25,
    (34, 62, OTHER, '11'): 457.25,
    (34, 62, OTHER, '12'): 465.25,
    (34, 62, OTHER, '13'): 473.25,
    (34, 62, OTHER, '14'): 481.25,
    (34, 62, OTHER, '15'): 489.25,
    (34, 62, OTHER, '16'): 497.25,
    (34, 62, OTHER, '17'): 505.25,
    (34, 62, OTHER, '18'): 513.25,
    (34, 62, OTHER, '19'): 521.25,
    (34, 62, OTHER, '2'): 385.25,
    (34, 62, OTHER, '20 and over'): 529.25,
    (34, 62, OTHER, '3'): 393.25,
    (34, 62, OTHER, '4'): 401.25,
    (34, 62, OTHER, '5'): 409.25,
    (34, 62, OTHER, '6'): 417.25,
    (34, 62, OTHER, '7'): 425.25,
    (34, 62, OTHER, '8'): 433.25,
    (34, 62, OTHER, '9'): 441.25,
    (34, 63, OTHER, '1'): 374.0,
    (35, 65, ALL, '2'): 607.0,
    (36, 67, OTHER, '11'): 464,
    (36, 67, OTHER, '12'): 472,
    (36, 67, OTHER, '13'): 480,
    (36, 67, OTHER, '14'): 488,
    (36, 67, OTHER, '15'): 496,
    (36, 67, OTHER, '16'): 504,
    (36, 67, OTHER, '17'): 512,
    (36, 67, OTHER, '18'): 520,
    (36, 67, OTHER, '19'): 528,
    (36, 67, OTHER, '20 and over'): 536,
    (37, 68, OTHER, '13'): 518.1,
    (37, 68, OTHER, '15'): 526.2,
    (37, 68, OTHER, '16'): 534.2,
    (37, 68, OTHER, '20 and over'): 542.2,
    (39, 73, PRIVATE, 'shillings 1'): 238.2,
    (39, 73, PRIVATE, 'under 1s'): 228.46,
    (39, 74, OTHER, 'aboriginal camps'): 762.914,
    (39, 75, OTHER, 'aboriginal camps'): 756.6,
    (40, 78, OTHER, 'aboriginal camps'): 768.952,
    (40, 79, OTHER, 'aboriginal camps'): 761.75,
    (41, 82, OTHER, 'aboriginal camps'): 760.235,
    (41, 83, OTHER, 'aboriginal camps'): 765.5,
    (42, 86, OTHER, 'aboriginal camps'): 763.087,
    (42, 87, OTHER, 'aboriginal camps'): 763.5,
    (43, 88, PRIVATE, 'unspecified'): 791.0,
    (43, 90, OTHER, 'aboriginal camps'): 764.795,
    (43, 91, OTHER, 'aboriginal camps'): 755.25,
    (44, 94, OTHER, 'aboriginal camps'): 743.195,
    (44, 95, OTHER, 'aboriginal camps'): 731.0,
    (46, 100, OTHER, 'other camps'): 506.19,
    (46, 100, OTHER, 'total'): 493.4,
    (46, 101, OTHER, 'total'): 495.5,
    (48, 102, METHODS[0], 'pounds 10 0 over'): 763.9,
    (35, 64, OTHER, '1'): 374.7,
    (35, 64, OTHER, '20 and over'): 526.4,
    (35, 65, OTHER, '1'): 376.4,
    (35, 65, OTHER, '20 and over'): 528.3,
}



def assign_rent_table(page: int, y: float, fallback: int) -> int:
    """Assign the source's physical leaves, independent of repeated OCR titles."""
    if 54 <= page <= 71:
        return 30 + (page - 54) // 2
    if 72 <= page <= 99:
        return 39 + (page - 72) // 4
    if 102 <= page <= 109:
        return 48
    if page in (100, 101):
        return 47 if y >= (518 if page == 100 else 531) else 46
    return fallback


def _layout(number: int, page: int, y: float) -> tuple[str, int] | None:
    """Return printed panel and the first zero-based room/inmate position."""
    if 30 <= number <= 38:
        first = 54 + (number - 30) * 2
        if number == 32:
            first = 58
        if page not in (first, first + 1):
            return None
        # Cut between the preceding panel's printed Total and the next
        # panel's first data row, not at the heading itself: candidate OCR
        # rows can lie a few points on either side of the heading baseline.
        if number == 37:
            headings = (260, 420, 615)
        elif number == 38:
            headings = (285, 500, 615)
        else:
            headings = (150, 365, 590)
        panel = 2 if y >= headings[2] else 1 if y >= headings[1] else 0 if y >= headings[0] else -1
        return (ROOM_CATEGORIES[panel], 0 if page == first else 10) if panel >= 0 else None
    if 39 <= number <= 45:
        first = 72 + (number - 39) * 4
        if not first <= page <= first + 3:
            return None
        panel = PRIVATE if page <= first + 1 else OTHER
        start = (204, 206, 168, 159) if number == 39 else None
        if start is None:
            start = (190, 190, 155, 155)
        return (panel, 0 if page % 2 == 0 else 11) if y >= start[page - first] else None
    if number in (46, 47):
        if page not in (100, 101):
            return None
        if number == 46 and y >= (518 if page == 100 else 531):
            return None
        headings = ((145, 317), (147, 320)) if number == 46 else ((553, 725), (555, 728))
        first, second = headings[page - 100]
        if y < first:
            return None
        return (PRIVATE if y < second else OTHER, 0 if page == 100 else 11)
    if number == 48:
        if not 102 <= page <= 109:
            return None
        headings = (191, 191, 247, 238, 186, 182, 209, 217)
        return (METHODS[(page - 102) // 2], 0 if page % 2 == 0 else 11) if y >= headings[page - 102] else None
    return None


def _money(text: str) -> str:
    """Normalise OCR typography in labels only, never in numeric cells."""
    text = text.lower().replace("£ ", "£").replace(" ", "")
    text = text.replace("i", "1").replace("l", "1").replace("o", "0").replace("e", "s").replace("b", "s")
    text = text.strip(".,-_")
    match = re.fullmatch(r"(\d{1,2})(?:s|8|9)", text)
    if match:
        return f"{int(match[1])}s."
    if re.fullmatch(r"£\d+", text):
        return text
    return ""


def _identity(label: str, room_table: bool) -> str:
    text = " ".join(label.lower().replace("_", "").split())
    compact = text.replace(" ", "")
    if "unspecif" in compact or "un8pecif" in compact:
        return "unspecified"
    if re.search(r"\btotal\b", text) or text.startswith("to="):
        return "total"
    if "wagon" in text or "trains" in text:
        return "wagons"
    if "boriginal" in text or "half" in text or "whites" in text:
        return "aboriginal camps"
    if "camp" in text:
        return "other camps"
    if room_table:
        if "20" in text and "over" in text:
            return "20 and over"
        return text if re.fullmatch(r"[1-9]|1\d|20", text) else ""
    if "under" in text and re.search(r"[1il]s", text):
        return "under 1s"
    money = re.search(r"£\s*(\d+)(?:\s+(\d+)s)?", text)
    if money:
        return "pounds " + money[1] + " " + (money[2] or "0") + (" over" if "over" in text else "")
    match = re.search(r"(?<!\d)(\d{1,2})s\.", text)
    return "shillings " + match[1] if match else ""


def _rental_label(label: str) -> bool:
    return bool(_identity(label, False))


@lru_cache(maxsize=56)
def _page_words(page: int) -> tuple:
    with pymupdf.open(PDF) as document:
        return tuple(document[page - 1].get_text("words"))


@lru_cache(maxsize=2)
def _page_ink(page: int) -> tuple[int, bytes]:
    """Cache thresholded source ink, independently of the PDF's OCR layer."""
    with pymupdf.open(PDF) as document:
        pixmap = document[page - 1].get_pixmap(
            matrix=pymupdf.Matrix(3, 3), colorspace=pymupdf.csGRAY, alpha=False)
    return pixmap.width, pixmap.samples.translate(bytes(int(value < 140) for value in range(256)))


def _printed_absences(page: int, y: float, edges: tuple[float, ...]) -> dict[int, str]:
    """Recover only visible paired absence dots; blank or damaged ink stays unknown."""
    stride, ink = _page_ink(page)
    nearby, intercept, slope = _source_baseline(page, y, edges)
    if not slope:
        centres = [_centre(word) for word in nearby
                   if re.fullmatch(r"[0-9]+(?:,[0-9]{3})*", word[4])
                   and 7 <= word[3] - word[1] <= 14 and abs(_centre(word) - y) <= 3]
        if centres:
            intercept = median(centres)
    result = {}
    for slot, edge in enumerate(edges):
        y = intercept + slope * (edge - 9)
        x0, x1 = int((edge - 22) * 3), int((edge + 4) * 3)
        y0, y1 = int((y - 5) * 3), int((y + 5) * 3)
        width = x1 - x0
        crop = bytearray(b"".join(ink[row * stride + x0:row * stride + x1]
                                 for row in range(y0, y1)))
        dots = []
        large = False
        for seed, marked in enumerate(crop):
            if not marked:
                continue
            pending = [seed]
            crop[seed] = 0
            xmin = xmax = seed % width
            ymin = ymax = seed // width
            count = 0
            while pending:
                position = pending.pop()
                x, row = position % width, position // width
                xmin, xmax = min(xmin, x), max(xmax, x)
                ymin, ymax = min(ymin, row), max(ymax, row)
                count += 1
                for neighbour in (position - width, position + width,
                                  position - 1 if x else -1,
                                  position + 1 if x + 1 < width else -1):
                    if 0 <= neighbour < len(crop) and crop[neighbour]:
                        crop[neighbour] = 0
                        pending.append(neighbour)
            if count < 5:
                continue
            w, h = (xmax - xmin + 1) / 3, (ymax - ymin + 1) / 3
            if w > 2 or h > 2.4:
                # A numeral, rule or clipped large glyph vetoes absence,
                # even when two nearby specks resemble the printed dots.
                large = True
                break
            centre_y = (y0 + (ymin + ymax + 1) / 2) / 3
            if .5 <= w and .5 <= h and y - 2 <= centre_y <= y + 4.5:
                dots.append(((x0 + (xmin + xmax + 1) / 2) / 3, centre_y))
        if not large and any(
            3 <= abs(left[0] - right[0]) <= 6
            and abs(left[1] - right[1]) < 1
            and edge - 15 < (left[0] + right[0]) / 2 < edge - 4
            for index, left in enumerate(dots) for right in dots[index + 1:]
        ):
            result[slot] = ".."
    return result


def _centre(word: tuple) -> float:
    # Candidate row_y_pt is a word-box midpoint, not the PDF box's top.
    return (word[1] + word[3]) / 2


@lru_cache(maxsize=56)
def _column_edges(page: int, room_table: bool) -> tuple[float, ...]:
    """Locate right-aligned figure columns, excluding the repeated row label."""
    left = page % 2 == 0
    width = 10 if room_table and left else 11
    lower, upper = ((465, 515) if left else (325, 375) if room_table else (350, 405))
    counts = Counter(round(word[2]) for word in _page_words(page)
                     if lower <= word[2] <= upper and 150 < word[1] < 830
                     and re.fullmatch(r"[0-9][0-9,]*", word[4]))
    if not counts:
        raise ValueError(f"No printed figure-column anchor on physical page {page}")
    # Adjacent integer bins belong to the same right edge; a stray marginal
    # numeral must not displace the grid's last column.
    groups = []
    for edge in sorted(counts):
        if groups and edge - groups[-1][-1] <= 2:
            groups[-1].append(edge)
        else:
            groups.append([edge])
    substantial = [group for group in groups if sum(counts[x] for x in group) >= 5]
    pool = substantial or groups
    headings = [word[2] for word in _page_words(page)
                if not left and re.sub(r"[^A-Z]", "", word[4].upper()) == "TOTAL"
                and 80 < word[1] < 320 and word[2] < 410]
    group = (min(pool, key=lambda part: abs(median(part) - median(headings)))
             if headings else max(pool, key=lambda part: part[-1]))
    last = sum(x * counts[x] for x in group) / sum(counts[x] for x in group)
    if room_table and not left:
        # The final Total column is wider than the ten inmate columns.
        # Extrapolating its right edge by the inmate pitch displaces the
        # first count into the margin, especially on the sparse leaves.
        number = 30 + (page - 54) // 2
        headers = [word for word in _page_words(page)
                   if word[4].isdigit() and 11 <= int(word[4]) <= 19
                   and 80 < word[1] < 300 and word[0] < 305
                   and _layout(number, page, _centre(word)) is None]
        if len(headers) >= 3:
            first = median((word[0] + word[2]) / 2 - 27 * (int(word[4]) - 11)
                           for word in headers) + 9
        else:
            first_counts = Counter(round(word[2]) for word in _page_words(page)
                                   if 45 < word[2] < 90 and 280 < word[1] < 830
                                   and re.fullmatch(r"[0-9][0-9,]*", word[4]))
            first = (sum(edge * count for edge, count in first_counts.items()) /
                     sum(first_counts.values())) if first_counts else last - 280
        return tuple(first + 27 * index for index in range(10)) + (last,)
    pitch = 27.0 if room_table and not left else 31.3
    if left:
        # Sparse territory panels can make the ten-room column more frequent
        # than the eleventh. The printed header still locates the last column.
        header = [word for word in _page_words(page)
                  if word[4] == str(width) and 80 < word[1] < 210
                  and word[0] > 430]
        if header:
            heading = min(header, key=lambda word: word[1])
            centre = (heading[0] + heading[2]) / 2
            if abs(last - centre) > pitch / 2:
                last = centre + 8
    return tuple(last - pitch * (width - 1 - index) for index in range(width))


def _source_baseline(page: int, y: float, edges: tuple[float, ...]) -> tuple[list, float, float]:
    """Locate the physical numeral baseline without borrowing an adjacent sparse row."""
    pitch = edges[1] - edges[0]
    nearby = [word for word in _page_words(page)
              if edges[0] - pitch + 7 <= (word[0] + word[2]) / 2 <= edges[-1] + 6
              and abs(_centre(word) - y) <= 6]
    anchors = {}
    for word in nearby:
        if not re.fullmatch(r"[0-9]+(?:,[0-9]{3})*", word[4]):
            continue
        if not 7 <= word[3] - word[1] <= 14 or word[2] - word[0] < 2.5:
            continue
        x = (word[0] + word[2]) / 2
        slot = min(range(len(edges)), key=lambda index: abs(x - (edges[index] - 6)))
        previous = anchors.get(slot)
        if previous is None or abs(_centre(word) - y) < abs(_centre(previous) - y):
            anchors[slot] = word
    slopes = [(_centre(upper) - _centre(lower)) /
              (((upper[0] + upper[2]) - (lower[0] + lower[2])) / 2)
              for lower_slot, lower in anchors.items() for upper_slot, upper in anchors.items()
              if upper_slot - lower_slot >= 3
              and abs(_centre(upper) - _centre(lower)) <= 5]
    if anchors and abs(median(_centre(word) - y for word in anchors.values())) > 3:
        # Sparse rows must not borrow a dense adjacent row's baseline.
        slopes = []
    slope = median(slopes) if len(anchors) >= 4 and slopes else 0
    if abs(slope) > .025:
        slope = 0
    intercept = (median(_centre(word) - slope * (word[0] + word[2]) / 2
                        for word in anchors.values()) if len(anchors) >= 4 and slopes else y)
    return nearby, intercept, slope


def _source_values(page: int, y: float, edges: tuple[float, ...]) -> dict[int, str]:
    """Read source-located slots; no mark means unknown, not an invented zero."""
    slots = defaultdict(list)
    nearby, intercept, slope = _source_baseline(page, y, edges)
    # Scan slant varies down a leaf: a rental figure can be four points
    # below its repeated label at the opposite margin. Follow the physical
    # numeral baseline, not whichever adjacent row is nearest that label.
    for word in nearby:
        x = (word[0] + word[2]) / 2
        target = intercept + slope * x
        if abs(_centre(word) - target) > 3.5:
            continue
        position = min(range(len(edges)), key=lambda index: abs(x - (edges[index] - 6)))
        # Thin vertical rules OCR'd as I are not figures. Keep malformed
        # numeral tokens (e.g. 28,94i) verbatim, without repairing their digits.
        text = word[4]
        # A box spanning several printed baselines is not a reading of this
        # row (notably £10-and-over merged with the following Unspecified).
        if re.search(r"\d", text) and word[3] - word[1] > 20:
            continue
        if re.search(r"\d", text) and word[2] - word[0] < 2.5 and (
            word[3] - word[1] < 7 or (text == "1" and word[3] - word[1] > 14)
        ):
            continue
        if re.search(r"\d", text) or PLACEHOLDER.fullmatch(text):
            slots[position].append(word)
    result = {}
    for position, words in slots.items():
        numeric = [word for word in words if re.search(r"\d", word[4])]
        seed = min(numeric or words, key=lambda word: abs(
            _centre(word) - intercept - slope * (word[0] + word[2]) / 2))
        # Select a single baseline in each slot, never concatenate adjacent
        # rows' figures when an OCR box is displaced within its printed row.
        selected = [word for word in (numeric or words) if abs(_centre(word) - _centre(seed)) <= 1]
        text = " ".join(word[4] for word in sorted(selected, key=lambda word: word[0]))
        result[position] = ".." if PLACEHOLDER.fullmatch(text) else text
    return result


@lru_cache(maxsize=56)
def _printed_rows(number: int, page: int) -> tuple[dict, ...]:
    """Identify lower bounds in each printed panel from their own label column."""
    room_table = number <= 38
    edges = _column_edges(page, room_table)
    words = _page_words(page)
    left = page % 2 == 0
    lower, upper = (25, 95) if left else (edges[-1] + 3, edges[-1] + 61)
    label_words = [word for word in words if lower <= word[0] <= upper
                   and re.search(r"[A-Za-z0-9£]", word[4])
                   and not (not left and word[4] in ("I", "I'", "I.") and word[0] < edges[-1] + 15)]
    rows = []
    for word in sorted(label_words, key=lambda part: (_centre(part), part[0])):
        y = _centre(word)
        layout = _layout(number, page, y)
        if layout is None:
            continue
        nearby = sorted((part for part in label_words if abs(_centre(part) - y) <= 2),
                        key=lambda part: part[0])
        text = " ".join(part[4] for part in nearby)
        label = ""
        ident = _identity(text, room_table)
        if ident in ("unspecified", "total", "wagons", "aboriginal camps", "other camps"):
            label = {"unspecified": "Unspecified", "total": "Total",
                     "wagons": "Wagons, Trains, etc.",
                     "aboriginal camps": "Aboriginal Camps in which Whites or Half-castes were Living",
                     "other camps": "Other Camps without Dwellings"}[ident]
        elif room_table:
            first = nearby[0][4].strip(".,")
            if first in ("I", "II"):
                first = "1" if first == "I" else "11"
            if re.fullmatch(r"[1-9]|1\d|20", first) and (
                left or nearby[0][0] >= edges[-1] + 20
            ):
                label = "20 and over" if first == "20" else first
        else:
            # "and over" can extend past the compact lower-bound label
            # column, especially on the left leaf. It belongs to that row.
            compact = "".join(part[4].lower() for part in words
                              if nearby[0][0] <= part[0] <= nearby[0][0] + 120
                              and abs(_centre(part) - y) <= 3)
            if "under" in compact or "nder" in compact:
                # Only the first (open-bottom) row starts with Under.
                if nearby[0][4].lower() in ("under", "u", "nder"):
                    label = "Under 1s."
            if not label:
                consumed = 1
                first = _money(nearby[0][4])
                if len(nearby) > 1 and (
                    not first or (nearby[0][4].isdigit() and nearby[1][4].strip(".") in ("s", "8", "9"))
                ):
                    first = _money(nearby[0][4] + nearby[1][4])
                    consumed = 2
                if first:
                    label = first
                    if first.startswith("£"):
                        tail = nearby[consumed:]
                        if tail and _money(tail[0][4]).endswith("s."):
                            label += " " + _money(tail[0][4])
                        if "over" in compact:
                            label += " and over"
            if label.startswith("£") and "over" in compact and not label.endswith("and over"):
                label += " and over"
            # The upper endpoint is printed sixty points to the right of
            # the lower one. It resolves malformed lower-bound typography
            # without page-specific decrements or matching another row.
            endpoint = sorted((part for part in words
                               if nearby[0][0] + 45 <= part[0] <= nearby[0][0] + 100
                               and abs(_centre(part) - y) <= 3
                               and _money(part[4])), key=lambda part: part[0])
            if endpoint and label and label != "Under 1s." and "over" not in label:
                end = _money(endpoint[0][4])
                if end.endswith("s.") and not label.startswith("£"):
                    value = int(end[:-2])
                    if 2 <= value <= 40:
                        label = f"{value - 1}s."
                elif end.startswith("£") and label.startswith("£"):
                    tail = endpoint[1:]
                    shillings = int(_money(tail[0][4])[:-2]) if tail and _money(tail[0][4]).endswith("s.") else 0
                    amount = 20 * int(end[1:]) + shillings
                    lower_pounds = int(label.split()[0][1:])
                    if 40 < amount <= 100 and (
                        (amount - 5) // 20 == lower_pounds or 20 * lower_pounds >= amount
                    ):
                        amount -= 5
                        pounds, shillings = divmod(amount, 20)
                        label = f"£{pounds}" + (f" {shillings}s." if shillings else "")
        ident = _identity(label, room_table)
        if not ident:
            continue
        echo = next((other for other in rows if other["context"] == layout[0]
                     and other["identity"] == ident and abs(other["y"] - y) <= (
                         18 if ident == "aboriginal camps" else 3)), None)
        if echo is not None:
            values = _source_values(page, y, edges)
            if len(values) > len(echo["values"]):
                echo.update(y=y, values=values)
            continue
        rows.append({"page": page, "y": y, "label": label, "identity": ident,
                     "context": layout[0], "start": layout[1], "edges": edges,
                     "values": _source_values(page, y, edges)})
    return tuple(rows)


def _values(row: dict, printed: dict) -> dict[int, str]:
    """Align candidate figures to physical slots, not candidate leader tokens."""
    width = len(printed["edges"])
    cells = [cell for _, cell in sorted(row["cells"].items())]
    # Labels and their leader tokens occupy no numeric column. A full width
    # after the final rental token is the numeric run, even with false headers.
    rental = [index for index, cell in enumerate(cells) if _rental_label(cell["value"])]
    if rental and printed["start"] == 0:
        cells = cells[rental[-1] + 1:]
    elif rental:
        cells = cells[:rental[0]]
    if (printed["start"] == 0 and len(cells) == width + 4
            and all(PLACEHOLDER.fullmatch(cell["value"]) for cell in cells[:4])):
        # Four structural leader cells precede the ten-inmate grid on the
        # affected room leaves. They are outside the physical figure columns.
        cells = cells[4:]
    source = printed["values"]
    if (printed["start"] and len(cells) == width and printed["identity"].isdigit()
            and cells[-1]["value"] == printed["identity"]
            and cells[-2]["value"] == source.get(width - 1)):
        # Remove the repeated label, then anchor the shortened run. Copying
        # its remaining positions would move the real 20+ figure into 19.
        cells = cells[:-1]
    if len(cells) == width and printed["page"] < 72:
        if any(re.fullmatch(r"[0-9][0-9,]*", value) and
               re.search(r"\d", cells[index]["value"]) and
               cells[index]["value"].replace(" ", "") != value
               for index, value in source.items()):
            # Candidate y/labels can be displaced by one printed row. A
            # nominally full run contradicting the physical grid is not a
            # reading of this row.
            return {}
        # Once structural leaders and the repeated room label are excluded,
        # these fixed-width runs retain the printed slots, including dots
        # which the PDF's text layer omitted. Never let a candidate dot erase
        # an intact source count.
        return {index: cell["value"] for index, cell in enumerate(cells)
                if cell["value"].strip() and (
                    re.search(r"\d", cell["value"]) or PLACEHOLDER.fullmatch(cell["value"]))
                and not (PLACEHOLDER.fullmatch(cell["value"]) and
                         re.search(r"\d", source.get(index, "")))}
    if len(cells) == width and printed["page"] >= 72 and not any(
        re.fullmatch(r"[0-9][0-9,]*", value) and
        cells[index]["value"].replace(" ", "") != value.replace(" ", "")
        for index, value in source.items()
    ):
        # Nominal width is not evidence of alignment: damaged candidates can
        # pad a truncated run with leaders and duplicate the surviving figures.
        # A full run is usable only if no intact source figure contradicts it.
        return {index: cell["value"] for index, cell in enumerate(cells)
                if cell["value"].strip() and (
                    (re.search(r"\d", cell["value"]) and not _rental_label(cell["value"])) or (
                        PLACEHOLDER.fullmatch(cell["value"]) and not re.search(r"\d", source.get(index, ""))))}
    numbers = [(index, cell["value"]) for index, cell in enumerate(cells)
               if re.search(r"\d", cell["value"]) and not _rental_label(cell["value"])]
    anchors = []
    for index, value in numbers:
        matches = [slot for slot, text in source.items()
                   if text.replace(" ", "") == value.replace(" ", "")]
        if len(matches) == 1:
            anchors.append((index, matches[0]))
    offsets = Counter(slot - index for index, slot in anchors)
    ranked = offsets.most_common()
    offset = ranked[0][0] if ranked and ranked[0][1] >= 3 and (
        len(ranked) == 1 or ranked[0][1] > ranked[1][1]) else None
    result = {}
    row_text = row.get("source_row_text", "")
    row_figures = {value.replace(",", "") for value in re.findall(r"\d[\d,]*", row_text)}
    previous = -1
    for index, value in numbers:
        matches = [slot for slot, text in source.items() if slot > previous
                   and text.replace(" ", "") == value.replace(" ", "")]
        brackets = [(lower_slot - lower_index) for lower_index, lower_slot in anchors
                    for upper_index, upper_slot in anchors
                    if lower_index <= index <= upper_index and lower_index < upper_index
                    and upper_slot - lower_slot == upper_index - lower_index]
        bounded = brackets[0] if brackets and len(set(brackets)) == 1 else None
        if offset is not None and 0 <= index + offset < width and index + offset > previous:
            slot = index + offset
        elif bounded is not None and index + bounded > previous:
            # Preserve a damaged or repeated middle figure when two distinct
            # source anchors enclose it in the same contiguous physical run.
            slot = index + bounded
        elif len(matches) == 1:
            slot = matches[0]
        else:
            # Repeated small figures in a truncated run do not uniquely
            # identify a column. Leave the source-located reading unchanged.
            continue
        if row_text and (slot not in source or PLACEHOLDER.fullmatch(source[slot])) and (
            value.replace(",", "") not in row_figures
        ):
            # A spurious candidate figure cannot turn an unprinted slot into
            # a count merely because neighbouring figures establish an offset.
            continue
        result[slot] = value
        previous = slot
    if len(cells) == width and (offset == 0 or all(
        source.get(index) == value for index, value in numbers
    )):
        for index, cell in enumerate(cells):
            if cell["value"].strip() and PLACEHOLDER.fullmatch(cell["value"]) and not re.search(
                r"\d", source.get(index, "")
            ):
                result[index] = cell["value"]
    return result


def _recover_candidate_room_labels(number: int, printed: list[dict], source_rows: list[dict]) -> None:
    """Retain damaged label OCR only when the neighbouring printed room grid locates it."""
    if number > 38:
        return
    for row in source_rows:
        identity = _identity(row["label"] or row["resolved"], True)
        if not identity or identity not in tuple(str(value) for value in range(1, 21)) + ("20 and over",):
            continue
        layout = _layout(number, row["page"], row["y"])
        if layout is None:
            continue
        section = [part for part in printed if part["page"] == row["page"] and part["context"] == layout[0]]
        if any(part["identity"] == identity or abs(part["y"] - row["y"]) <= 4 for part in section):
            continue
        numeric = sorted((int(part["identity"]), part["y"]) for part in section if part["identity"].isdigit())
        pitches = [(upper_y - lower_y) / (upper - lower)
                   for (lower, lower_y), (upper, upper_y) in zip(numeric, numeric[1:])
                   if upper > lower and 5 <= (upper_y - lower_y) / (upper - lower) <= 10]
        if len(pitches) < 3:
            continue
        value = 20 if identity == "20 and over" else int(identity)
        nearest, nearest_y = min(numeric, key=lambda part: abs(part[0] - value))
        y = nearest_y + (value - nearest) * median(pitches)
        if abs(y - row["y"]) > 12 or _layout(number, row["page"], y) != layout:
            continue
        if any(abs(part["y"] - y) <= 4 for part in section):
            continue
        edges = _column_edges(row["page"], True)
        part = {"page": row["page"], "y": y, "label": identity, "identity": identity,
                "context": layout[0], "start": layout[1], "edges": edges,
                "values": _source_values(row["page"], y, edges)}
        part["values"].update(_values(row, part))
        printed.append(part)


def _recover_unlabelled_slots(number: int, printed: list[dict]) -> None:
    """Recover absent label OCR only where neighbouring facing rows locate a slot."""
    room_table = number <= 38
    original = tuple(printed)
    for page in sorted({part["page"] for part in original}):
        facing = page + 1 if page % 2 == 0 else page - 1
        own = [part for part in original if part["page"] == page]
        partners = [part for part in original if part["page"] == facing]
        for partner in partners:
            section = [part for part in own if part["context"] == partner["context"]]
            if any(part["identity"] == partner["identity"] for part in section):
                continue
            offsets = [part["y"] - other["y"] for part in section for other in partners
                       if other["context"] == partner["context"] and part["identity"] == other["identity"]
                       and abs(other["y"] - partner["y"]) <= 80 and abs(part["y"] - other["y"]) <= 24]
            if len(offsets) < 3:
                continue
            y = partner["y"] + median(offsets)
            layout = _layout(number, page, y)
            if layout is None or layout[0] != partner["context"]:
                continue
            if any(abs(part["y"] - y) <= 4 for part in section):
                continue
            edges = _column_edges(page, room_table)
            values = _source_values(page, y, edges)
            values.update(_printed_absences(page, y, edges))
            if not any(re.search(r"\d", value) for value in values.values()) and len(values) < 3:
                continue
            printed.append({"page": page, "y": y, "label": partner["label"], "identity": partner["identity"],
                            "context": layout[0], "start": layout[1], "edges": edges, "values": values})


def assemble_rent_panels(number: int, source_rows: list[dict],
                         schema: tuple[list[str], list[str], str],
                         panels: dict[int, list[tuple[float, str]]],
                         methods: dict[int, list[tuple[float, str]]]) -> tuple[list[str], list[list[str]]]:
    """Reconstruct rows by printed section, interval and facing-page position."""
    if not 30 <= number <= 48:
        raise ValueError(f"Not a rent/room panel table: {number}")
    dimension_fields, _, _ = schema
    room_table = number <= 38
    fields = [f"{'inmates' if room_table else 'rooms'}_{part}"
              for part in (INMATES if room_table else ROOMS)]
    headers = dimension_fields + fields
    first = 54 + 2 * (number - 30) if room_table else 72 + 4 * (number - 39)
    pages = range(first, first + (2 if room_table else 4))
    if number in (46, 47):
        pages = range(100, 102)
    elif number == 48:
        pages = range(102, 110)
    printed = [dict(row, values=dict(row["values"])) for page in pages
               for row in _printed_rows(number, page)]
    if not room_table:
        for part in printed:
            # A damaged "and over" on one leaf cannot invent a separate
            # closed interval when its facing lower bound is legibly open.
            if any(other["page"] == (part["page"] + 1 if part["page"] % 2 == 0 else part["page"] - 1)
                   and other["context"] == part["context"]
                   and other["identity"] == part["identity"] + " over"
                   for other in printed):
                part["identity"] += " over"
                part["label"] += " and over"
    _recover_candidate_room_labels(number, printed, source_rows)
    for key, y in SOURCE_ROW_BASELINES.items():
        table, page, context, identity = key
        if table != number:
            continue
        label = next((part["label"] for part in printed
                      if part["context"] == context and part["identity"] == identity),
                     {"under 1s": "Under 1s.", "unspecified": "Unspecified", "total": "Total",
                      "other camps": "Other Camps without Dwellings"}.get(identity, identity))
        printed = [part for part in printed if not (
            part["page"] == page and part["context"] == context
            and (part["identity"] == identity or abs(part["y"] - y) <= 4))]
        edges = _column_edges(page, room_table)
        printed.append({"page": page, "y": y, "label": label, "identity": identity,
                        "context": context, "start": _layout(number, page, y)[1],
                        "edges": edges, "values": _source_values(page, y, edges)})
    _recover_unlabelled_slots(number, printed)
    printed.sort(key=lambda part: (part["page"], part["y"]))
    for row in source_rows:
        candidate_numbers = {cell["value"].replace(" ", "") for cell in row["cells"].values()
                             if re.search(r"\d", cell["value"]) and not _rental_label(cell["value"])}
        choices = []
        for index, part in enumerate(printed):
            distance = abs(part["y"] - row["y"])
            if part["page"] != row["page"] or distance > 12:
                continue
            source_numbers = {value.replace(" ", "") for value in part["values"].values()
                              if re.search(r"\d", value)}
            common = len(candidate_numbers & source_numbers)
            # Distinct printed figures resolve skewed candidate coordinates
            # within one row spacing. A label alone cannot reach a distant row.
            if distance <= 6 or common >= 2:
                choices.append((-common, distance, index))
        if not choices:
            continue
        # An OCR box on the printed baseline must not be reassigned to an
        # adjacent row merely because repeated small counts overlap more.
        _, _, index = min(choices, key=lambda choice: (
            choice[1] > 3, choice[0] if choice[1] > 3 else choice[1], choice[1]))
        part = printed[index]
        mapped = _values(row, part)
        score = (sum(not PLACEHOLDER.fullmatch(value) for value in mapped.values()), len(mapped))
        if score > part.get("candidate_score", (-1, -1)):
            part["candidate_score"] = score
            part["candidate_values"] = mapped
    for part in printed:
        part["values"].update({slot: value for slot, value in part.get("candidate_values", {}).items()
                               if not re.fullmatch(r"[0-9]+(?:,[0-9]{3})*",
                                                   part["values"].get(slot, ""))})
        # The printed total's own midpoint prevents selecting the following
        # bracket (p77 Under 1s. 1,484, not the next row's 6,776).
        if not room_table and part["start"]:
            total = _source_values(part["page"], part["y"], part["edges"]).get(10)
            existing = part["values"].get(10, "")
            if total is not None and (
                re.fullmatch(r"[0-9][0-9,]*", total) or not re.fullmatch(r"[0-9][0-9,]*", existing)
            ):
                part["values"][10] = total
        part["values"].update(_printed_absences(part["page"], part["y"], part["edges"]))
        part["values"].update(SOURCE_READINGS.get(
            (number, part["page"], part["context"], part["identity"]), {}))
    body = []
    contexts = ROOM_CATEGORIES if room_table else METHODS if number == 48 else (PRIVATE, OTHER)
    for context in contexts:
        primary = [part for part in printed if part["context"] == context and part["start"] == 0]
        continuation = [part for part in printed if part["context"] == context and part["start"] != 0]
        offsets = [(left["y"], left["identity"], left["y"] - right["y"])
                   for left in primary for right in continuation
                   if left["identity"] == right["identity"] and abs(left["y"] - right["y"]) <= 24]
        taken = set()
        assembled = []
        for part in primary:
            neighbours = sorted((y, offset) for y, identity, offset in offsets
                                if identity != part["identity"] and abs(y - part["y"]) <= 80)
            before = [anchor for anchor in neighbours if anchor[0] < part["y"]]
            after = [anchor for anchor in neighbours if anchor[0] > part["y"]]
            displacement = 0
            if before and after:
                lower_y, lower_offset = before[-1]
                upper_y, upper_offset = after[0]
                fraction = (part["y"] - lower_y) / (upper_y - lower_y)
                displacement = lower_offset + fraction * (upper_offset - lower_offset)
            elif len(neighbours) >= 2:
                displacement = min(neighbours, key=lambda anchor: abs(anchor[0] - part["y"]))[1]
            matches = [(abs(other["y"] + displacement - part["y"]), index)
                       for index, other in enumerate(continuation)
                       if index not in taken and other["identity"] == part["identity"]
                       and abs(other["y"] + displacement - part["y"]) <= 6]
            mate = None
            if matches:
                _, index = min(matches)
                mate = continuation[index]
                taken.add(index)
            assembled.append((part, mate))
        assembled.extend((None, part) for index, part in enumerate(continuation) if index not in taken)
        assembled.sort(key=lambda pair: ((pair[0] or pair[1])["page"] // 2,
                                        (pair[0] or pair[1])["y"]))
        for left, right in assembled:
            part = left or right
            values = [""] * len(fields)
            for half in (left, right):
                if half is not None:
                    for offset, value in half["values"].items():
                        values[half["start"] + offset] = value
            dimensions = {field: (context if field in ("dwelling_class", "method_of_occupancy")
                                  else part["label"]) for field in dimension_fields}
            body.append([dimensions[field] for field in dimension_fields] + values)
    return headers, body
