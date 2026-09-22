import fitz, sys, json, pathlib

pdf = r"data\raw\abs_1911_census\1911_census_volume_iii_part_xiii_dwellings.pdf"
doc = fitz.open(pdf)

page_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 182
page = doc[page_idx]

# Extract words with bounding boxes
words = page.get_text("words")  # list of (x0, y0, x1, y1, word, block_no, line_no, word_no)

# Group by line (y0 rounded to nearest 2px)
from collections import defaultdict
lines = defaultdict(list)
for w in words:
    y_key = round(w[1] / 2) * 2
    lines[y_key].append(w)

# Print lines sorted by y, words sorted by x
print(f"Page index {page_idx}, size {page.rect.width:.1f} x {page.rect.height:.1f}")
print(f"Total words: {len(words)}\n")

for y in sorted(lines.keys()):
    row = sorted(lines[y], key=lambda w: w[0])
    x_positions = [f"{w[0]:.0f}:{w[4]}" for w in row]
    print(f"y={y:5.0f}  " + "  ".join(x_positions))
