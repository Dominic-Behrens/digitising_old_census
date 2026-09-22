"""Report unresolved NSW extraction issues using the same strict checks as validate.

The old digit-length heuristic missed plausible-looking OCR errors and silently
ignored missing rows. Source-backed corrections and publication discrepancies
remain separate audit tables, not outstanding data issues.
Inputs: data/intermediate/nsw_1911_lga_dwellings.csv and
        output/extract_table68/published_totals.csv.
Output: output/check_issues/issues.csv.
"""
from extract_table68 import AUDIT_DIR, OUT, ROOT, write_csv
from validate import CHECK_FIELDS, collect_checks, load_rows


def main():
    rows = load_rows(OUT)
    totals = load_rows(AUDIT_DIR / "published_totals.csv")
    issues = [check for check in collect_checks(rows, totals) if check["status"] != "pass"]
    issue_path = ROOT / "output/check_issues/issues.csv"
    write_csv(issue_path, CHECK_FIELDS, issues)
    print(f"Unresolved extraction/data issues: {len(issues)}")
    for issue in issues:
        print(f"  PDF page {issue['source_pdf_page']} {issue['scope']}: "
              f"{issue['check']} {issue['field']} = {issue['observed']!r}; "
              f"expected {issue['expected']!r}")
    print(f"Source-backed fixes: {AUDIT_DIR / 'corrections.csv'}")
    print("Separate publication discrepancy: physical PDF page 186 (index 185) prints Table 69; "
          "contents and adjacent headings print 68. Numeric data are not adjusted.")
    print(f"Issue report: {issue_path}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
