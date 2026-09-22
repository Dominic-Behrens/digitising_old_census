import fitz, sys

pdf = r"data\raw\abs_1911_census\1911_census_volume_iii_part_xiii_dwellings.pdf"
doc = fitz.open(pdf)

start = int(sys.argv[1]) if len(sys.argv) > 1 else 148
end = int(sys.argv[2]) if len(sys.argv) > 2 else 151

for i in range(start, min(end, doc.page_count)):
    print(f"\n========== PDF page index {i} (printed {i+1849}) ==========\n")
    print(doc[i].get_text())
