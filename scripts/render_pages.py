import fitz, sys, pathlib

pdf = r"data\raw\abs_1911_census\1911_census_volume_iii_part_xiii_dwellings.pdf"
out_dir = pathlib.Path("data/intermediate/abs_1911_census_pages")
out_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(pdf)

pages = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [149]

zoom = 3.0  # ~216 dpi
mat = fitz.Matrix(zoom, zoom)

for p in pages:
    page = doc[p]
    pix = page.get_pixmap(matrix=mat)
    out = out_dir / f"page_{p:03d}.png"
    pix.save(str(out))
    print(f"Saved {out}  ({pix.width}x{pix.height})")
