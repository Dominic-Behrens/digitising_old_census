"""
Download 1911 ABS census PDFs from the ABS catalogue page.

Excludes the Notes of the Commonwealth Statistician and Volume I Statistician's
Report, leaving the detailed table indexes and Volume II/III parts.

Output manifest: data/raw/abs_1911_census/abs_1911_download_manifest.csv
"""

from __future__ import annotations

import csv
import html
import pathlib
import re
import urllib.parse
import urllib.request


PAGE_URL = "https://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/2112.01911?OpenDocument"
OUT_DIR = pathlib.Path("data/raw/abs_1911_census")
MANIFEST = OUT_DIR / "abs_1911_download_manifest.csv"

EXCLUDE_TITLE_PATTERNS = [
    "notes of the commonwealth statistician",
    "statistician's report",
    "statisticians report",
]


def get_page_html() -> str:
    request = urllib.request.Request(PAGE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def safe_filename(value: str) -> str:
    value = html.unescape(value)
    value = urllib.parse.unquote(value)
    value = value.replace("Dewllings", "Dwellings")
    value = re.sub(r"[\\/:*?\"<>|]", "_", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_publication_links(page_html: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r'<tr\s+class="listentry".*?<td\s+align="left"\s*>(?P<title>.*?)</td>.*?'
        r'<a\s+href="(?P<href>/AUSSTATS/free\.nsf/log\?openagent&(?P<file>.*?\.pdf)&.*?)"',
        re.IGNORECASE | re.DOTALL,
    )
    records = []
    for match in pattern.finditer(page_html):
        title = clean_text(match.group("title"))
        href = html.unescape(match.group("href"))
        file_name = safe_filename(match.group("file"))
        url = urllib.parse.urljoin(PAGE_URL, href)
        lower_title = title.lower()
        excluded = any(pattern in lower_title for pattern in EXCLUDE_TITLE_PATTERNS)
        records.append(
            {
                "title": title,
                "source_url": url,
                "file_name": file_name,
                "excluded": str(excluded),
                "exclude_reason": "statistician notes/report" if excluded else "",
            }
        )
    return records


def download_file(url: str, path: pathlib.Path) -> int:
    parsed = urllib.parse.urlsplit(url)
    safe_url = urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            urllib.parse.quote(parsed.path, safe="/"),
            urllib.parse.quote(parsed.query, safe="=&?"),
            parsed.fragment,
        )
    )
    request = urllib.request.Request(safe_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        data = response.read()
    path.write_bytes(data)
    return len(data)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    page_html = get_page_html()
    records = parse_publication_links(page_html)

    for record in records:
        local_path = OUT_DIR / record["file_name"]
        record["local_path"] = str(local_path)
        if record["excluded"] == "True":
            record["status"] = "excluded"
            record["bytes"] = ""
            print(f"excluded: {record['title']}")
            continue
        if local_path.exists() and local_path.stat().st_size > 0:
            record["status"] = "exists"
            record["bytes"] = str(local_path.stat().st_size)
            print(f"exists: {local_path}")
            continue
        size = download_file(record["source_url"], local_path)
        record["status"] = "downloaded"
        record["bytes"] = str(size)
        print(f"downloaded: {local_path} ({size:,} bytes)")

    fields = [
        "title",
        "source_url",
        "file_name",
        "local_path",
        "excluded",
        "exclude_reason",
        "status",
        "bytes",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    included = [record for record in records if record["excluded"] == "False"]
    print(f"\nFound {len(records)} PDF links; included {len(included)}; manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
