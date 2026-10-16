# Historical NSW census roster source rows

`historical_roster_source_rows.csv` is the retained extraction/transcription input for the panel builder. It covers 1921–1976; the builder reads the reviewed 1911 roster and extracts 1981 directly from the original PDF.

Each record retains the PDF page, printed row/index number or text position, extracted name, publication type, raw text and review status. Semicolon-separated index references are council parts merged into one council. These references are not stable LGA codes.

Source PDFs and page ranges are documented in `data-notes.md` and resolved by the builder's map manifest. OCR fixes remove scanning errors; year-specific printed names and categories remain. Source-row labels still need independent review where the generated panel flags `name_review_required=yes`.

This CSV is an input with review decisions, not a disposable output. Keep it in version control. Generated panels and review images are in the producing exploration's output folder.


`sydney_membership_source_rows.csv` records the user-selected historical Sydney extent. It links each year/name/type council key to the dedicated metropolitan or Sydney SD roster, marks whole/part inclusion, and gives membership and map source pages. Record-specific label aliases match within a year only. Keep the separate Outer Sydney division out of the 1971 main panel.
