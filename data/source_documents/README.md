# Fictional supplier source documents

These five files are generated specifically for the BidLens demo and contain no real supplier information:

- `supplier_a_deccan_packaging.xlsx` — complete baseline Excel quote; GST treatment is stated in the Cover sheet.
- `supplier_b_charminar_boxes.pdf` — PDF quote with three unquoted items and an unconfirmed discount note; tax treatment is not stated.
- `supplier_c_musi_cartons_scan.png` — scanned quote with one intentionally ambiguous price. `supplier_c_musi_cartons_scan_ocr_reference.txt` is a reproducible synthetic transcript used when local OCR cannot recover enough rows; the app discloses when it uses this fallback.
- `supplier_d_metro_pack.eml` — email with partial item pricing and freight/tax treatment not stated.
- `supplier_e_telanganaboxworks.docx` — Word quote with USD prices and a mixture of per-item and per-100 price bases; tax treatment is not stated.

`data/gold_standard_quotes.csv` records expected values for automated tests. It is a test oracle, not a source used by the runtime parser.
