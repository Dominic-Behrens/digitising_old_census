"""Reassemble Table 64's three printed room panels by physical county rows.

The page-local candidate column numbers are not a table-wide schema.  The
fixed source layout below also covers the two panels on pages 136/137 and
144/145, and the separate territory sections on pages 146–148.

The manifest contains 388 physical area/total rows, excluding split section
headings.  Geometry supplies ordinary cells; the page/room/name maps retain
image-read strings where OCR drops digits or merges a digit with a ruled border.
Printed absence marks and footnote symbols remain strings, not inferred zeros.
"""
from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import re

import pymupdf

_PDF = Path(__file__).resolve().parents[1] / "data/raw/abs_1911_census/1911_census_volume_iii_part_xiii_dwellings.pdf"
_NAMES = {
    "New South Wales": "Argyle|Arrawatta|Ashburnham|Auckland|Baradine|Barrona|Bathurst|Benarba|Beresford|Bland|Blaxland|Bligh|Booroondarra|Bourke|Boyd|Brisbane|Buccleuch|Buckland|Buller|Burnett|Cadell|Caira|Camden|Canbelego|Clarence|Clarendon|Clarke|Clive|Clyde|Cook|Cooper|Courallie|Cowley|Cowper|Culgoa|Cumberland|Cunningham|Dampier|Darling|Delalah|Denham|Denison|Dowling|Drake|Dudley|Durham|Evelyn|Ewenmar|Farnell|Finch|Fitzgerald|Fitzroy|Flinders|Forbes|Franklin|Georgiana|Gipps|Gloucester|Gordon|Gough|Goulburn|Gowen|Gregory|Gresham|Gunderbooka|Harden|Hardinge|Hawes|Hume|Hunter|Inglis|Irrara|Jamison|Kennedy|Kilfera|Killara|King|Landsborough|Leichhardt|Lincoln|Livingstone|Macquarie|Manara|Menindie|Mitchell|Monteagle|Mootwingee|Mossgiel|Mouramba|Murchison|Murray|Nandewar|Napier|Narran|Narromine|Nicholson|Northumberland|Oxley|Parry|Perry|Phillip|Poole|Pottinger|Raleigh|Rankin|Richmond|Robinson|Rous|Roxburgh|St. Vincent|Sandon|Selwyn|Stapylton|Sturt|Taila|Tandora|Tara|Thoulcanna|Tongowoko|Townsend|Ularara|Urana|Vernon|Wakool|Waljeers|Wallace|Waradgery|Wellesley|Wellington|Wentworth|Werunda|Westmoreland|White|Windeyer|Woore|Wynyard|Yancowinna|Yanda|Yantara|Young|Yungnulgra|Lord Howe Island|Total",
    "Victoria": "Anglesey|Benambra|Bendigo|Bogong|Borung|Bourke|Buln Buln|Croajingolong|Dalhousie|Dargo|Delatite|Dundas|Evelyn|Follett|Gladstone|Grant|Grenville|Gunbower|Hampden|Heytesbury|Kara Kara|Karkarooc|Lowan|Millewa|Moira|Mornington|Normanby|Polwarth|Ripon|Rodney|Talbot|Tambo|Tanjil|Tatchera|Villiers|Weeah|Wonnangatta|Total",
    "Queensland": "Aramac|Balonne|Blackall|Boulia|Bowen|Brisbane, North|Brisbane, South|Bundaberg|Burke|Burnett|Caboolture|Cairns|Cardwell|Charleville|Chillagoe|Clermont|Cloncurry|Cook|Croydon|Cunnamulla|Dalby|Darling Downs, C.|Darling Downs, E.|Darling Downs, N.|Darling Downs, W.|Diamantina|Enoggera|Etheridge|Fassifern|Gladstone|Gympie|Herberton|Highfields|Hughenden|Ipswich|Kennedy|Leichhardt|Logan|Mackay|Maranoa|Maryborough|Moreton, East|Moreton, West|Mount Morgan|Nundah|Oxley|Palmer|Peak Downs|Rockhampton|St. Lawrence|Somerset|Springsure|Stanley|Stanthorpe|Taroom|Tiaro|Toowong|Toowoomba|Townsville|Warrego|Warwick|Westwood|Wide Bay|Winton|Total",
    "South Australia": "Adelaide|Albert|Alfred|Blachford|Buccleuch|Buckingham|Burra|Buxton|Cardwell|Carnarvon|Chandos|Dalhousie|Daly|Derby|Dufferin|Eyre|Fergusson|Flinders|Frome|Gawler|Granville|Grey|Hamley|Hanson|Herbert|Hindmarsh|Hopetoun|Jervois|Kimberley|Kintore|Le Hunte|Light|Lytton|MacDonnell|Manchester|Musgrave|Newcastle|Robe|Robinson|Russell|Stanley|Sturt|Taunton|Victoria|Way|York|Young|Northern Division|North-Eastern Div.|North-Western Div.|Western Division|Total",
    "Western Australia": "Beverley|Coolgardie|Coolgardie, North|Esperance|Eucla|Gascoyne|Katanning|Kimberley, East|Kimberley, West|Magnet|Margaret|Murchison|Murchison, East|Narrogin|Northam|North-West|Phillips River|Pingelly|Plantagenet|Sussex|Swan|Tambellup|Victoria|Wagin|Wellington|Yilgarn|York|Total",
    "Tasmania": "Beaconsfield|Bothwell|Brighton|Bruni|Campbell Town|Circular Head|Clarence|Deloraine|Devonport|Emu Bay|Esperance|Evandale|Fingal|Flinders Island|George Town|Glamorgan|Glenorchy|Gormanston|Green Ponds|Hamilton|Hobart|Huon|Kentish|Kingborough|King Island|Latrobe|Launceston|Leven|Lilydale|Longford|New Norfolk|New Town|Oatlands|Penguin|Port Cygnet|Portland|Queenborough|Queenstown|Richmond|Ringarooma|Ross|St. Leonards|Scottsdale|Sorell|Spring Bay|Strahan|Table Cape|Tasman|Waratah|Westbury|Zeehan|Total",
    "Northern Territory": "Disraeli|Gladstone|Malmesbury|Palmerston|Rosebery|Remainder of Territory|Total",
    "Federal Territory": "Canberra|Jervis Bay|Total",
}


def _paired(start, minor, major, count):
    return [start] + [edge for i in range(count) for edge in (minor + 50 * i, major + 50 * i)]


_EDGES = {
    (130, 1): _paired(106, 140, 157, 8), (131, 1): _paired(108, 140, 157, 8),
    (132, 9): _paired(132, 159, 181, 7), (133, 9): _paired(132, 163, 181, 7),
    (134, 16): list(range(117, 418, 25)) + [454, 480, 503],
    (135, 16): list(range(120, 421, 25)) + [458, 484, 504],
    (136, 1): _paired(106, 139, 158, 8), (136, 9): _paired(134, 167, 186, 7),
    (137, 9): _paired(134, 167, 186, 7),
    (137, 16): list(range(120, 421, 25)) + [458, 484, 502],
    (138, 1): [128,156,175,198,220,249,270,299,320,349,371,399,421,449,470,491,510],
    (139, 9): _paired(134, 167, 185, 7),
    (140, 16): list(range(122, 423, 25)) + [461, 487, 509],
    (141, 1): [122,150,169,200,219,250,269,300,319,350,369,400,419,441,458,482,502],
    (142, 9): _paired(122, 153, 172, 7),
    (143, 16): list(range(118, 419, 25)) + [454, 480, 502],
    (144, 1): [116,150,168,200,219,250,269,300,319,350,369,400,419,440,458,481,502],
    (144, 9): _paired(132, 158, 176, 7), (145, 9): _paired(137, 167, 185, 7),
    (145, 16): list(range(124, 425, 25)) + [461, 487, 506],
    (146, 1): [115,146,166,196,216,246,266,296,316,346,366,396,416,438,458,480,500],
    (147, 9): _paired(127, 156, 176, 6) + [457, 489],
    (148, 16): list(range(120, 421, 25)) + [458, 484, 502],
}
for _panel in ((136,9),(139,9),(142,9),(144,9),(145,9)):
    _EDGES[_panel][-1] = 510
# page, first room, state, first/last body ordinate, label-column right edge,
# first/last canonical row (end exclusive).
_PANELS = [
    (130,1,"New South Wales",245,825,106,0,65), (131,1,"New South Wales",190,830,108,65,143),
    (132,9,"New South Wales",190,820,132,0,65), (133,9,"New South Wales",180,820,132,65,143),
    (134,16,"New South Wales",180,820,117,0,65), (135,16,"New South Wales",180,820,120,65,143),
    (136,1,"Victoria",185,550,106,0,38), (136,9,"Victoria",655,815,134,0,15),
    (137,9,"Victoria",188,385,134,15,38), (137,16,"Victoria",487,805,120,0,38),
    (138,1,"Queensland",198,805,128,0,65), (139,9,"Queensland",206,830,134,0,65),
    (140,16,"Queensland",198,805,122,0,65),
    (141,1,"South Australia",267,808,122,0,52), (142,9,"South Australia",267,810,122,0,52),
    (143,16,"South Australia",257,800,118,0,52),
    (144,1,"Western Australia",263,540,116,0,28), (144,9,"Western Australia",665,814,132,0,15),
    (145,9,"Western Australia",248,400,137,15,28), (145,16,"Western Australia",514,795,124,0,28),
    (146,1,"Tasmania",207,637,115,0,52), (147,9,"Tasmania",212,643,127,0,52),
    (148,16,"Tasmania",198,631,120,0,52),
    (146,1,"Northern Territory",670,746,115,0,7), (147,9,"Northern Territory",675,747,127,0,7),
    (148,16,"Northern Territory",657,733,120,0,7),
    (146,1,"Federal Territory",777,815,115,0,3), (147,9,"Federal Territory",772,810,127,0,3),
    (148,16,"Federal Territory",757,795,120,0,3),
]
_AREA_TYPES = {"New South Wales":"County", "Victoria":"County", "Queensland":"Census District",
               "South Australia":"County or Division", "Western Australia":"Statistical District",
               "Tasmania":"Municipality", "Northern Territory":"County", "Federal Territory":"District"}

# Read directly from the printed images at the stated physical page/panel.
# These are damaged OCR/rule intersections, not calculated totals or zeros.
_PRINTED = {
    (131,1,"Total"): "20,321 171 14,596 84 24,288 119 70,241 280 75,063 677 54,369 1340 26,993 1117 14,766 900",
    (133,9,"Total"): "7,016 763 4,487 637 1,987 507 1,626 509 684 404 643 483 324 318",
    (135,16,"Total"): "293 300 157 215 138 186 52 108 382 1,637 1340 *455 319,766 *11,210 1865",
    (136,1,"Total"): "9,679 62 9,429 60 18,054 80 61,913 173 58,107 424 48,927 769 26,452 824 14,307 860",
    (137,9,"Total"): "6,688 712 4,115 656 1,595 529 1,270 569 543 350 517 389 250 301",
    (137,16,"Total"): "182 244 100 190 71 173 40 96 276 1,229 1119 *359 263,634 *9,049 812",
    (138,1,"Total"): "16,198 39 7,656 40 7,601 61 22,979 95 24,648 203 19,366 231 10,779 264 5,650 254",
    (139,9,"Total"): "2,812 212 1,710 228 665 157 509 214 178 154 183 206 98 135",
    (140,16,"Total"): "74 142 29 102 23 92 18 76 91 836 486 *342 121,753 *4,083 998",
    (141,1,"Total"): "3,248 10 4,119 19 9,630 17 21,151 82 16,821 146 14,048 219 6,364 166 3,149 151",
    (142,9,"Total"): "1,387 111 829 96 307 81 299 99 115 63 117 109 60 66",
    (143,16,"Total"): "44 85 29 39 25 49 6 26 57 349 303 *88 82,108 *2,071 258",
    (144,1,"Total"): "13,893 13 6,418 26 8,316 62 17,656 154 9,680 172 5,620 169 2,215 142 1,149 159",
    (145,9,"Total"): "536 139 336 139 124 98 129 112 56 70 46 85 19 62",
    (145,16,"Total"): "23 65 13 48 7 47 3 33 23 393 291 *129 66,553 *2,317 1449",
    (146,1,"Total"): "2,431 5 2,939 5 3,301 16 11,613 66 6,444 52 5,442 77 2,603 57 1,626 90",
    (147,9,"Total"): "812 61 585 61 217 37 211 78 101 44 94 41 43 32",
    (148,16,"Total"): "34 38 22 29 13 27 7 15 30 221 382 *23 38,950 *1,075 86",
    (132,9,"Delalah"): ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
    (137,9,"Tatchera"): "33 4 16 1 10 2 3 3 3 2 3 5 .. 3",
    (137,9,"Villiers"): "124 6 77 5 32 5 25 10 10 2 13 6 9 3",
    (137,9,"Weeah"): "1 .. 1 1 1 .. .. .. .. .. .. 2 .. ..",
    (137,9,"Wonnangatta"): "9 1 6 1 2 2 2 1 .. 1 .. 2 .. ..",
    (139,9,"Oxley"): "62 .. 45 1 13 .. 10 2 7 .. 7 1 1 1",
    (139,9,"Palmer"): "1 .. .. .. .. 1 .. 2 .. .. .. 2 .. 1",
    (139,9,"Peak Downs"): "2 .. 2 .. 1 .. .. .. .. .. .. .. .. 1",
    (139,9,"Rockhampton"): "104 4 61 4 34 5 17 8 5 5 4 9 4 3",
    (139,9,"St. Lawrence"): "4 .. 1 1 2 .. 8 .. .. 1 .. .. 1 ..",
    (139,9,"Somerset"): ".. 4 1 5 2 1 .. .. .. 1 .. .. .. 1",
    (139,9,"Springsure"): "21 4 11 1 9 .. 2 .. .. 1 2 1 .. 2",
    (139,9,"Stanley"): "24 1 21 2 4 .. 2 5 1 2 .. .. 1 2",
    (139,9,"Stanthorpe"): "17 .. 2 .. 1 1 .. 4 .. .. .. 2 .. 1",
    (139,9,"Taroom"): "10 .. 4 .. 1 .. 7 .. .. .. 3 1 1 1",
    (139,9,"Tiaro"): "16 .. 12 .. 10 .. 2 .. .. .. 1 .. .. 1",
    (139,9,"Toowong"): "82 .. 50 .. 25 3 19 1 9 2 6 .. 2 ..",
    (139,9,"Toowoomba"): "168 14 97 11 30 4 34 9 8 2 6 10 8 11",
    (139,9,"Townsville"): "59 6 38 9 9 7 8 6 6 6 2 6 1 6",
    (139,9,"Warrego"): "1 2 2 .. 1 1 1 2 1 1 2 2 3 ..",
    (139,9,"Warwick"): "40 3 29 5 6 2 8 2 3 2 1 5 .. 1",
    (139,9,"Westwood"): "41 2 33 3 17 4 11 7 2 5 4 4 1 4",
    (139,9,"Wide Bay"): "46 1 26 .. 13 .. 2 3 .. 4 .. 4 1 5",
    (139,9,"Winton"): "14 2 7 3 2 1 .. 2 .. .. 1 1 .. ..",
    (142,9,"Buccleuch"): ".. 1 .. .. .. .. .. .. .. .. .. .. .. ..",
    (142,9,"Buxton"): ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
    (142,9,"Dufferin"): ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
    (142,9,"Kintore"): ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
    (142,9,"Le Hunte"): ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
    (142,9,"Western Division"): ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
}
_PRINTED.update({(133,9,name): values for name,values in (
    ("Harden","44 1 32 7 11 2 10 2 11 4 6 4 2 2"),
    ("Hardinge","22 3 15 1 3 1 7 1 6 .. 3 .. 4 3"),
    ("Hawes","4 .. 1 .. .. .. 2 .. .. .. 1 .. .. .."),
    ("Hume","44 3 32 1 13 3 14 4 6 2 4 1 6 3"),
    ("Hunter","16 .. 5 .. 5 .. 5 1 1 .. 2 1 .. .."),
    ("Inglis","41 7 23 10 14 5 14 2 5 3 2 3 3 2"),
    ("Irrara","1 .. 2 .. 2 .. 1 .. 1 .. .. .. .. .."),
    ("Jamison","14 .. 14 .. 10 .. 3 2 2 .. 1 .. 1 1"),
    ("Kennedy","10 .. 14 .. 4 .. 5 .. 2 .. .. 1 2 1"),
    ("Kilfera",".. .. 1 1 .. .. .. 1 .. .. .. .. .. .."),
    ("Killara","2 .. .. .. .. .. 1 .. .. 1 .. .. 1 .."),
    ("King","53 2 37 7 9 3 18 .. 10 6 6 2 2 2"),
    ("Landsborough",".. .. .. .. .. .. .. .. .. .. .. .. .. .."),
    ("Leichhardt","18 2 14 .. 13 1 5 1 3 1 1 1 4 .."),
    ("Lincoln","31 3 29 3 15 8 16 3 8 4 1 5 3 1"),
    ("Livingstone","1 .. 1 .. 1 1 1 .. 1 .. .. .. .. .."),
    ("Macquarie","107 5 53 7 24 6 17 5 6 2 6 3 .. 4"),
    ("Manara","1 .. 1 .. .. .. .. 1 1 .. .. .. 1 .."),
    ("Menindie","1 .. 1 .. .. .. .. .. .. .. .. 1 .. .."),
    ("Mitchell","18 .. 15 3 9 .. 4 .. 3 .. 2 .. 2 2"),
    ("Monteagle","45 2 32 6 19 6 16 5 9 1 5 3 3 3"),
    ("Mootwingee","2 1 1 .. .. .. 1 .. 1 .. 1 .. 1 .."),
    ("Mossgiel","3 .. 5 1 1 .. .. .. 1 1 .. .. .. .."),
    ("Mouramba","2 1 4 .. 3 .. 1 1 .. 2 1 .. .. .."),
    ("Murchison","24 .. 13 2 8 1 5 .. 5 2 1 .. 3 .."),
    ("Murray","47 2 37 4 24 4 9 1 4 6 5 .. 1 2"),
    ("Nandewar","25 3 13 2 7 1 2 .. 5 2 5 3 .. 1"),
    ("Napier","8 2 4 1 2 1 .. 1 1 .. 2 .. 1 1"),
    ("Narran","3 .. 4 3 4 .. 1 .. 2 1 .. 1 1 2"),
    ("Narromine","24 .. 13 2 5 3 10 2 2 1 1 1 3 .."),
    ("Nicholson","4 .. 3 .. 1 3 .. 1 .. .. 1 .. .. .."),
    ("Northumberland","321 46 179 43 89 27 69 32 25 32 29 36 15 24"),
    ("Oxley","10 3 5 2 6 3 6 1 2 1 3 5 2 2"),
    ("Parry","24 2 9 .. 4 1 7 .. 1 1 1 .. .. 2"),
    ("Perry","2 1 2 .. .. 2 .. .. 1 .. .. .. .. .."),
    ("Phillip","31 3 12 3 7 1 3 3 .. 1 1 3 2 1"),
    ("Poole",".. .. 1 .. .. .. .. .. .. .. .. .. .. .."),
    ("Pottinger","40 1 23 1 11 .. 9 2 3 2 5 1 3 3"),
    ("Raleigh","30 4 10 2 6 .. 4 .. 1 .. 1 3 .. 1"),
    ("Rankin","1 .. 1 .. .. .. 1 .. .. .. .. .. .. .."),
    ("Richmond","40 2 21 2 7 2 6 3 2 .. 2 1 .. 3"),
    ("Robinson","9 3 5 6 .. 4 1 2 1 1 3 3 .. .."),
    ("Rous","240 11 150 15 63 8 31 14 11 8 16 8 5 6"),
    ("Roxburgh","31 4 28 2 10 1 17 4 4 1 7 2 .. .."),
    ("St. Vincent","76 2 40 4 29 2 17 4 7 3 6 3 1 2"),
    ("Sandon","72 9 51 3 21 1 19 1 6 2 6 2 5 6"),
    ("Selwyn","12 1 12 .. 2 .. 1 .. 2 2 1 1 2 2"),
    ("Stapylton","7 .. 8 .. 4 .. 3 1 2 .. 4 .. .. 1"),
    ("Sturt","6 2 4 .. 1 .. 1 .. 1 .. .. .. 1 .."),
    ("Taila","3 .. 2 .. .. .. 1 .. .. .. .. .. .. .."),
    ("Tandora","1 .. .. 1 .. .. .. .. .. 1 .. .. .. .."),
    ("Tara","3 .. .. .. .. .. 1 .. .. .. 2 .. .. .."),
    ("Thoulcanna","3 .. .. .. .. .. .. .. .. .. .. .. .. .."),
    ("Tongowoko",".. 1 .. 1 1 .. 1 .. .. .. .. .. .. .."),
    ("Townsend","31 1 12 1 8 1 10 7 3 2 5 4 4 1"),
    ("Ularara",".. .. 1 .. 1 .. .. .. .. .. .. 1 .. .."),
    ("Urana","24 1 21 2 6 2 7 .. 6 2 11 .. 4 4"),
    ("Vernon","24 .. 9 2 8 .. 5 1 .. 1 1 2 2 .."),
    ("Wakool","7 .. 6 .. 3 .. 4 .. 2 1 2 1 2 .."),
    ("Waljeers","2 .. .. .. 2 1 1 .. 1 .. 1 .. 1 .."),
    ("Wallace","18 .. 13 .. 8 1 7 .. 3 2 1 .. 1 2"),
    ("Waradgery","11 1 14 1 5 .. 6 2 2 .. 3 1 1 2"),
    ("Wellesley","25 1 25 1 12 4 8 4 5 1 5 1 2 1"),
    ("Wellington","81 8 67 7 28 8 19 11 8 6 11 16 7 5"),
    ("Wentworth","9 1 3 .. 3 1 1 .. 2 1 .. .. .. 2"),
    ("Westmoreland","25 1 10 .. 5 1 2 2 2 .. 1 2 .. 1"),
    ("White","6 4 5 .. 1 1 .. .. .. 1 .. .. .. 2"),
    ("Windeyer","3 .. 1 .. .. .. .. .. .. .. .. 1 .. .."),
    ("Woore",".. .. 1 .. .. .. .. .. .. .. 1 .. .. .."),
    ("Wynyard","75 1 52 3 31 2 17 6 8 5 5 3 7 7"),
    ("Yancowinna","36 28 22 14 6 9 1 11 2 14 3 12 .. 10"),
    ("Yanda","1 .. .. .. 3 1 1 .. .. .. .. .. 1 1"),
    ("Yantara","1 .. 1 .. 1 1 .. .. .. .. .. .. .. .."),
    ("Young","5 1 4 3 .. .. .. 1 .. .. .. .. .. 1"),
    ("Yungnulgra","2 .. 1 2 .. 1 .. 2 .. .. 1 1 .. 1"),
    ("Lord Howe Island",".. .. .. .. .. .. .. .. .. .. .. .. .. .."),
)})
_PRINTED.update({(137,16,name): values for name,values in (
    ("Anglesey",".. 1 1 3 .. 3 1 1 1 20 .. 5 1,812 74 12"),
    ("Benambra","1 1 .. 1 1 2 .. 1 .. 6 7 5 1,327 47 7"),
    ("Bendigo","4 13 5 5 .. 5 1 5 3 38 52 9 11,865 374 40"),
    ("Bogong","5 6 3 5 1 6 .. 2 2 27 35 12 5,532 174 18"),
    ("Borung","5 5 2 1 3 1 1 .. 1 50 33 15 6,068 174 30"),
    ("Bourke","96 106 49 72 43 69 23 32 141 407 537 170 121,664 4,766 109"),
    ("Buln Buln","2 5 .. 4 .. 3 .. 6 4 40 44 5 8,622 189 53"),
    ("Croajingolong",".. .. .. 1 .. .. .. 1 .. 3 2 1 595 22 2"),
    ("Dalhousie","2 7 .. 5 1 7 .. 3 3 23 11 8 3,806 140 16"),
    ("Dargo",".. 2 .. 5 .. 1 .. .. .. 6 3 1 1,275 32 4"),
    ("Delatite","3 4 1 8 1 2 1 1 3 25 19 12 4,421 137 18"),
    ("Dundas","1 1 1 1 1 1 2 2 7 18 7 8 2,048 69 18"),
    ("Evelyn","5 5 .. 6 1 2 1 2 4 35 22 2 3,725 192 10"),
    ("Follett",".. .. 1 .. .. .. 1 .. .. 1 3 2 532 18 4"),
    ("Gladstone","1 8 1 2 .. 2 .. 3 1 18 6 4 3,632 107 34"),
    ("Grant","11 17 6 12 4 4 .. 3 15 75 74 11 14,895 405 41"),
    ("Grenville","8 8 6 4 .. 7 .. 4 6 54 31 1 9,172 273 41"),
    ("Gunbower","1 1 2 1 .. 1 .. .. .. 12 6 .. 1,799 53 13"),
    ("Hampden","3 1 4 2 1 1 1 .. 25 13 14 6 2,503 69 9"),
    ("Heytesbury","1 2 .. 2 .. .. .. .. 1 3 4 1 1,376 28 3"),
    ("Kara Kara",".. 3 .. 3 .. 3 .. 2 2 21 11 7 3,129 100 10"),
    ("Karkarooc",".. 2 .. 2 1 6 .. 2 .. 14 26 5 3,221 77 38"),
    ("Lowan","2 3 1 2 .. 3 .. 1 3 13 3 8 2,465 61 4"),
    ("Millewa",".. .. .. .. .. .. .. .. .. .. .. .. 19 .. .."),
    ("Moira","2 6 3 2 1 5 .. 6 5 48 25 11 6,118 178 46"),
    ("Mornington","4 6 4 8 2 8 4 3 13 61 23 4 7,609 252 35"),
    ("Normanby",".. 2 2 2 2 3 1 .. 3 12 15 3 2,457 60 19"),
    ("Polwarth","3 .. 2 2 1 1 .. 3 1 16 11 4 2,755 77 30"),
    ("Ripon","3 3 2 1 2 2 1 1 9 18 6 1 2,653 85 11"),
    ("Rodney","1 2 1 5 1 6 .. 3 2 24 12 7 4,035 111 35"),
    ("Talbot","4 11 .. 10 1 9 .. 2 4 35 33 8 10,423 310 43"),
    ("Tambo",".. 1 1 1 .. .. .. .. .. 11 .. 6 597 35 5"),
    ("Tanjil","4 5 .. 4 1 4 1 3 4 31 22 5 4,044 146 10"),
    ("Tatchera","1 2 1 1 .. .. .. .. 1 8 6 4 2,074 57 7"),
    ("Villiers","7 4 1 5 1 5 1 3 11 34 15 4 4,414 123 28"),
    ("Weeah",".. .. .. .. .. .. .. .. .. 1 2 6 536 13 3"),
    ("Wonnangatta","1 1 .. 2 .. .. .. .. .. 6 .. 1 416 21 6"),
)})
_PRINTED.update({
    (135,16,"Tandora"): ".. .. .. .. .. .. .. .. .. .. 1 .. 64 1 3",
    (132,9,"Gunderbooka"): "1 1 .. 1 .. 1 1 1 .. 2 .. .. .. 1",
    (147,9,"Spring Bay"): "4 .. 2 1 1 .. 5 .. .. .. .. .. .. ..",
    (148,16,"Zeehan"): ".. .. .. .. .. 3 .. 1 .. 14 16 .. 1,506 40 ..",
    (136,1,"Dundas"): "76 1 101 .. 121 1 507 .. 371 1 360 3 204 5 122 6",
    (136,1,"Gladstone"): "329 1 215 .. 206 .. 810 2 745 8 631 6 342 3 202 4",
    (136,1,"Follett"): "30 1 31 .. 33 .. 128 .. 88 1 100 .. 41 1 35 ..",
    (137,16,"Follett"): ".. .. 1 .. .. 1 .. .. 1 3 2 .. 532 18 4",
    (143,16,"Burra"): "2 .. 2 1 .. .. .. .. .. 7 5 .. 818 23 ..",
    (143,16,"Buxton"): ".. .. .. .. .. .. .. .. .. .. .. .. 3 .. 7",
    (143,16,"Eyre"): ".. .. .. .. .. .. .. 1 .. 4 6 .. 1,198 25 ..",
    (143,16,"Grey"): "4 3 1 1 1 2 .. .. 5 16 8 .. 2,796 50 10",
    (143,16,"Herbert"): ".. .. .. 1 .. .. .. .. .. .. 1 3 201 7 1",
    (143,16,"MacDonnell"): ".. .. .. .. .. 1 .. .. .. 1 1 .. 275 4 ..",
    (143,16,"Newcastle"): ".. .. 1 .. .. 1 .. .. .. 4 2 1 519 14 ..",
    (143,16,"Robe"): "1 .. 2 2 2 1 .. .. 1 5 6 .. 783 17 7",
    (143,16,"Russell"): ".. .. .. .. .. .. .. .. 1 1 1 1 581 12 ..",
    (143,16,"Stanley"): "1 .. .. 1 .. 1 1 .. 4 4 37 2 2,159 42 5",
    (143,16,"Sturt"): ".. 2 .. .. .. 2 .. 1 .. 6 10 1 1,675 37 4",
    (143,16,"Taunton"): ".. 1 .. 1 .. .. .. .. .. .. .. 2 97 7 6",
    (141,1,"Taunton"): "18 .. 14 .. 11 .. 24 1 12 .. 9 1 6 .. .. ..",
    (141,1,"Hopetoun"): "8 .. 10 .. 7 .. 12 .. 5 .. 10 .. 3 .. 1 ..",
})
_PRINTED_CELLS = {
    (131,1,"Landsborough"): {7:".."}, (131,1,"Mitchell"): {9:".."},
    (134,16,"Dampier"): {13:"60"}, (134,16,"Farnell"): {0:".."},
    (134,16,"Fitzgerald"): {0:".."}, (134,16,"Gregory"): {3:"..",4:"..",5:".."},
    (135,16,"Sandon"): {12:"2,541"}, (135,16,"Tandora"): {11:".."},
    (137,16,"Grenville"): {11:"1"}, (137,16,"Weeah"): {0:".."},
    (138,1,"Westwood"): {1:"..",3:".."}, (138,1,"Wide Bay"): {3:".."},
    (138,1,"Winton"): {1:"..",3:"..",4:"60",9:".."},
    (140,16,"Moreton, West"): {14:"26"},
    (143,16,"Daly"): {11:"11"},
    (143,16,"Way"): {0:".."}, (143,16,"Young"): {0:".."},
    (144,1,"Margaret"): {15:"5"},
    (132,9,"Ashburnham"): {0:"77"},
    (131,1,"Yancowinna"): {0:"302"}, (131,1,"Yantara"): {0:"14"},
    (135,16,"Irrara"): {13:"9"}, (131,1,"Rankin"): {12:"1",13:".."},
    (133,9,"Tara"): {2:"3"},
    (141,1,"Adelaide"): {11:"110"}, (142,9,"Adelaide"): {13:"34"},
    (133,9,"Tandora"): {8:"1",9:".."},
    (136,1,"Croajingolong"): {9:"2"}, (136,1,"Delatite"): {1:".."},
    (136,1,"Lowan"): {11:"5"}, (136,1,"Normanby"): {7:"1"},
    (137,16,"Dargo"): {11:".."}, (137,16,"Polwarth"): {4:"2"},
    (137,16,"Tambo"): {0:"1"}, (137,16,"Tatchera"): {7:"1"},
    (138,1,"Taroom"): {15:".."},
    (133,9,"Werunda"): {12:"..",13:".."},
    (136,9,"Croajingolong"): {9:".."}, (137,16,"Gladstone"): {6:"1"},
    (136,1,"Hampden"): {11:"12"}, (137,9,"Hampden"): {1:"1"},
    (140,16,"Cook"): {5:"1"}, (140,16,"Croydon"): {3:"1"},
    (140,16,"Fassifern"): {7:"2"}, (140,16,"Highfields"): {7:"1"},
    (141,1,"Dufferin"): {15:".."},
    (141,1,"Hamley"): {13:"1"}, (141,1,"Jervois"): {7:".."},
    (142,9,"Kimberley"): {4:"1"}, (141,1,"MacDonnell"): {9:".."},
    (141,1,"Robe"): {7:"..",11:".."}, (143,16,"York"): {11:"..",13:"1"},
    (141,1,"Northern Division"): {4:"36"}, (141,1,"North-Eastern Div."): {4:"60"},
    (141,1,"North-Western Div."): {9:"1"},
    (144,1,"Swan"): {11:"92"}, (148,16,"Spring Bay"): {9:".."},
    (146,1,"Zeehan"): {4:"173"},
    (143,16,"Robinson"): {0:"..",1:"1",3:".."},
    (143,16,"Lytton"): {14:".."},
}
_TERRITORIES = {
    ("Northern Territory",1): [
        ".. .. .. .. .. .. 1 .. .. .. .. .. 1 .. .. ..",
        "2 .. 1 .. 1 .. .. 1 .. 1 .. .. .. .. .. ..",
        "12 .. 10 .. 2 .. 1 .. .. .. .. .. .. .. .. ..",
        "116 .. 128 2 42 .. 44 2 18 .. 16 3 7 .. 5 1",
        "222 .. 96 .. 44 1 20 1 17 .. 4 .. .. .. .. ..",
        "261 1 48 3 22 2 15 1 10 .. 11 1 5 .. 4 1",
        "613 1 283 5 111 3 81 5 45 1 31 4 13 .. 9 2",
    ],
    ("Northern Territory",9): [
        ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
        ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
        ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
        ".. .. 1 .. .. .. .. .. .. .. .. .. .. ..",
        ".. .. .. 1 .. .. .. .. .. 1 .. .. .. ..",
        "1 2 .. .. .. 1 .. .. .. .. .. .. .. 1",
        "1 2 1 1 .. 1 .. .. .. 1 .. .. .. 1",
    ],
    ("Northern Territory",16): [
        ".. .. .. .. .. .. .. .. .. .. .. .. 2 .. ..",
        ".. .. .. .. .. .. .. .. .. .. .. .. 4 2 ..",
        ".. .. .. .. .. .. .. .. .. .. .. .. 25 .. 3",
        ".. 1 .. .. .. .. .. .. .. 3 .. 2 377 14 3",
        ".. .. .. .. .. .. .. .. .. .. 1 1 404 5 10",
        ".. .. .. .. .. .. .. .. .. .. 5 20 382 33 44",
        ".. 1 .. .. .. .. .. .. .. 3 6 †23 1,194 *54 60",
    ],
    ("Federal Territory",1): [
        "136 2 25 1 19 .. 60 .. 55 3 49 1 29 .. 19 1",
        ".. .. .. .. .. .. .. .. 2 .. .. .. 1 .. .. ..",
        "136 2 25 1 19 .. 60 .. 57 3 49 1 30 .. 19 1",
    ],
    ("Federal Territory",9): [
        "7 .. 8 .. 6 .. 2 .. .. .. 2 2 .. ..",
        ".. .. .. .. .. .. .. .. .. .. .. .. .. ..",
        "7 .. 8 .. 6 .. 2 .. .. .. 2 2 .. ..",
    ],
    ("Federal Territory",16): [
        "1 .. .. .. .. .. 1 .. 3 1 6 .. 428 11 2",
        ".. .. .. .. .. .. .. .. .. .. .. .. 3 .. ..",
        "1 .. .. .. .. .. 1 .. 3 1 6 .. 431 11 2",
    ],
}


def _key(text):
    return re.sub(r"[^a-z]", "", text.lower()).replace("totali", "total")


def _labels(words, top, bottom, cutoff):
    groups = []
    for word in sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        y = (word[1] + word[3]) / 2
        if not top < y < bottom or word[2] >= cutoff or not re.search(r"[A-Za-z]", word[4]):
            continue
        if word[4] in ("I", "l", "f"):
            continue  # recognised vertical rules, not printed geographical names
        if groups and abs(groups[-1][0] - y) < 3:
            groups[-1][1].append(word)
        else:
            groups.append([y, [word]])
    labels = [(y, " ".join(w[4] for w in sorted(ws, key=lambda w:w[0]))) for y, ws in groups]
    result = []
    for y, text in labels:
        key = _key(text)
        if key in ("remainderof", "state", "statei"):
            continue
        if key == "territory":
            text = "Remainder of Territory"
        result.append((y, text))
    return result


def _value(text):
    text = re.sub(r"\s+", "", text)
    if re.search(r"\d",text):
        text = text.strip(".·_-")
    if text and not re.search(r"[0-9A-Za-z]", text):
        return ".."
    if re.fullmatch(r"[*†t]?\d[\d,]*", text):
        return text.replace("t", "†")
    return ""


def _geometry(chars, y, edges):
    values = []
    for left, right in zip(edges, edges[1:]):
        selected = []
        for char in chars:
            x0,y0,x1,y1 = char["bbox"]
            x = (x0 + x1) / 2
            if not left < x < right or abs((y0 + y1) / 2 - y) >= 3.8:
                continue
            # Vertical ruling and OCR of its crossings are often read as 1/I.
            if re.search(r"[A-Za-z0-9]",char["c"]) and (
                y1-y0 > 13 or y1-y0 < 7 and char["c"] in "1Il"
            ):
                continue
            selected.append(char)
        values.append(_value("".join(c["c"] for c in sorted(selected,key=lambda c:c["bbox"][0]))))
    return values


def _align(direct, candidates):
    """Align only observed strings; leader cells may occur within a proposal."""
    n, k = len(direct), len(candidates)
    cost = [[float("inf")] * (k+1) for _ in range(n+1)]
    path = {}
    cost[0][0] = 0
    for i in range(n+1):
        for j in range(k+1):
            current = cost[i][j]
            steps = []
            if i < n:
                steps.append((i+1,j,current+2,"missing"))
            if j < k:
                steps.append((i,j+1,current+2,"leader"))
            if i < n and j < k:
                d,c = direct[i],candidates[j]
                penalty = 0 if not d or d == c else 2 if not c else 12
                steps.append((i+1,j+1,current+penalty,"cell"))
            for a,b,new,action in steps:
                if new < cost[a][b]:
                    cost[a][b] = new
                    path[a,b] = (i,j,action)
    aligned = [""] * n
    i,j = n,k
    while i or j:
        a,b,action = path[i,j]
        if action == "cell":
            aligned[a] = candidates[b]
        i,j = a,b
    return aligned, cost[n][k]


def _candidate(rows, page, y, name, direct):
    choices = []
    for row in rows:
        if row["page"] != page or abs(row["y"]-y) > 3.5:
            continue
        label = row["label"] or row["resolved"]
        similarity = SequenceMatcher(None,_key(label),_key(name)).ratio()
        if similarity < .65:
            continue
        values = [_value(cell["value"]) for _,cell in sorted(row["cells"].items())]
        leading = len(values)-len(direct)
        if (page == 136 or page == 137 and len(direct) == 14) and (
            0 <= leading <= 2 and all(v == ".." for v in values[:leading])
        ):
            # Fully delimited Victoria panels retain readable numbers where
            # PDF OCR joins a border or drops an entire low-contrast cell.
            values = values[leading:]
            direct[:] = values
            return values
        aligned, cost = _align(direct,values)
        choices.append((cost,-similarity,abs(row["y"]-y),aligned))
    return min(choices,key=lambda v:v[:3])[3] if choices else [""] * len(direct)


def assemble_county_rooms(source_rows, schema, states, area_types):
    """Return one row per printed area; missing evidence remains an empty string."""
    dimensions, fields, row_field = schema
    names = {state:text.split("|") for state,text in _NAMES.items()}
    records = {(state,name):{} for state,areas in names.items() for name in areas}
    by_page = defaultdict(list)
    for row in source_rows:
        by_page[row["page"]].append(row)
    with pymupdf.open(_PDF) as document:
        words = {page:document[page-1].get_text("words") for page in range(130,149)}
        chars = {page:[c for b in document[page-1].get_text("rawdict")["blocks"]
                       for line in b.get("lines",[]) for span in line["spans"] for c in span["chars"]]
                 for page in range(130,149)}
        for page,room,state,top,bottom,cutoff,first,last in _PANELS:
            labels = _labels(words[page],top,bottom,cutoff)
            expected = names[state][first:last]
            if page == 133:
                # This panel's OCR fuses seven late county labels.  Its facing
                # total panel retains every row.  Interpolate only physical
                # ordinate offsets, never numerical values.
                reference = _labels(words[135],180,820,120)
                anchors = [(i,y) for i,(_,name) in enumerate(reference)
                           for y,label in labels if _key(name)==_key(label)]
                projected = []
                for i,(reference_y,name) in enumerate(reference):
                    before = max((a for a in anchors if a[0] <= i),default=anchors[0])
                    after = min((a for a in anchors if a[0] >= i),default=anchors[-1])
                    if before[0] == after[0]:
                        delta = before[1]-reference[before[0]][0]
                    else:
                        weight = (i-before[0])/(after[0]-before[0])
                        delta = ((1-weight)*(before[1]-reference[before[0]][0])
                                 + weight*(after[1]-reference[after[0]][0]))
                    projected.append((reference_y+delta,name))
                labels = projected
            if len(labels) != len(expected):
                raise ValueError(f"Table 64 page {page} {state}: {len(labels)} physical rows, expected {len(expected)}")
            edges = _EDGES[page,room]
            panel_fields = fields[:16] if room == 1 else fields[16:30] if room == 9 else fields[30:]
            for (y,_),name in zip(labels,expected):
                row_candidates = [
                    row for row in by_page[page]
                    if abs(row["y"]-y) < 3.5
                    and SequenceMatcher(None,_key(row["label"] or row["resolved"]),_key(name)).ratio() >= .65
                ]
                numeric_y = min(row_candidates,key=lambda row:abs(row["y"]-y))["y"] if row_candidates else y
                direct = _geometry(chars[page],numeric_y,edges)
                candidate = _candidate(by_page[page],page,numeric_y,name,direct)
                values = [d or c for d,c in zip(direct,candidate)]
                printed = _TERRITORIES.get((state,room))
                if printed is not None:
                    values = printed[names[state].index(name)].split()
                elif (page,room,name) in _PRINTED:
                    values = _PRINTED[page,room,name].split()
                for column,value in _PRINTED_CELLS.get((page,room,name),{}).items():
                    values[column] = value
                records[state,name].update(zip(panel_fields,values))
    body = []
    for state,areas in names.items():
        for name in areas:
            dims = {"state":state,"area_type":_AREA_TYPES[state],row_field:name}
            body.append([dims.get(field,"") for field in dimensions]
                        + [records[state,name].get(field,"") for field in fields])
    return dimensions + fields, body
