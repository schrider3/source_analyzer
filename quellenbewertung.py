"""
=============================================================
  Source Relevance Scoring Algorithm
  FOM Hackathon - Algorithms & Data Structures 2026
=============================================================

  Assumptions (documented, Phase 1):
    [A1] Sources are written in English
    [A2] PDFs are text-based (not scanned / image-based)

  Limitations (Phase 5):
    [L1] No distinction between upper/lowercase (case-insensitive)
    [L2] No stemming/lemmatization - "learning" ≠ "learn"
    [L3] Image-based PDFs return empty text → Score = 0
    [L4] Keyword order fully determines weighting
    [L5] Frequency ≠ relevance (context is not evaluated)
=============================================================

run first: pip install pypdf pandas tabulate openpyxl

| Modul    | Verwendung                                      |
| -------- | ----------------------------------------------- |
| pypdf    | Text aus PDFs extrahieren                       |
| pandas   | Tabelle erstellen & sortieren                   |
| tabulate | Tabellenausgabe in der Konsole                  |
| openpyxl | XLSX-Export mit Formatierung                    |
"""

import sys
import re
import time
from pathlib import Path
import pypdf
import pandas as pd
from tabulate import tabulate


# ─────────────────────────────────────────────────────────────
#  STEP 1 - Load keyword file
# ─────────────────────────────────────────────────────────────

def load_keywords(file_path: Path) -> list[str]:
    """
    Reads the keyword file line by line.
    Each line represents one keyword or key phrase.
    Empty lines are ignored.
    """
    if not file_path.exists():
        print(f"[ERROR] Keyword file not found: {file_path}")
        sys.exit(1)

    keywords = [
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not keywords:
        print("[ERROR] Keyword file is empty.")
        sys.exit(1)

    return keywords


# ─────────────────────────────────────────────────────────────
#  STEP 1b - Calculate weights
#  First keyword = n (highest weight), last = 1 (lowest)
# ─────────────────────────────────────────────────────────────

def calculate_weights(keywords: list[str]) -> dict[str, int]:
    n = len(keywords)
    return {keyword: (n - index) for index, keyword in enumerate(keywords)}


# ─────────────────────────────────────────────────────────────
#  STEP 2 - Load PDF folder
# ─────────────────────────────────────────────────────────────

def load_pdfs(folder_path: Path) -> list[Path]:
    """
    Returns all .pdf files in the given folder.
    Error case: no PDF found → program exits.
    """
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"[ERROR] Folder not found: {folder_path}")
        sys.exit(1)

    pdf_list = sorted(folder_path.glob("*.pdf"))

    # DECISION: PDFs found?
    if not pdf_list:
        print("[ERROR] No PDF files found in the folder.")
        sys.exit(1)

    return pdf_list


# ─────────────────────────────────────────────────────────────
#  STEP 3 - Extract text from PDF
#  Assumption [A2]: PDF is text-based
# ─────────────────────────────────────────────────────────────

def extract_text(pdf_path: Path) -> str:
    """
    Extracts raw text from a text-based PDF.
    Returns an empty string if no page contains readable text
    (image-based PDF or corrupted file).
    """
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        page_texts: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                page_texts.append(page_text)

        raw_text = "\n".join(page_texts)

        # FIX: Silbentrennung zusammenführen
        # "net-\nwork" → "network"
        raw_text = re.sub(r'-\n', '', raw_text)

        # FIX: einfache Zeilenumbrüche als Leerzeichen
        # verhindert "neu-\nral" style splits ohne Bindestrich
        raw_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', raw_text)

        return raw_text

    except Exception as error:
        print(f"  [WARNING] Could not read '{pdf_path.name}': {error}")
        return ""


# ─────────────────────────────────────────────────────────────
#  STEP 3b - Count exact occurrences of a keyword
#  1:1 match, case-insensitive [A3]
# ─────────────────────────────────────────────────────────────

def count_occurrences(keyword: str, text: str) -> int:
    """
    Counts how often 'keyword' appears exactly (1:1, case-insensitive)
    in 'text'. Works for single words and multi-word phrases.
    """
    pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
    return len(re.findall(pattern, text.lower()))


# ─────────────────────────────────────────────────────────────
#  MAIN ALGORITHM
#  Follows the flowchart exactly (draw.io schema)
# ─────────────────────────────────────────────────────────────

def main_algorithm(folder_path: Path, keyword_file: Path) -> pd.DataFrame:

    # ── STEP 1 ─────────────────────────────────────────────
    print("\n[1/5] Loading keywords ...")
    keywords = load_keywords(keyword_file)
    weights  = calculate_weights(keywords)

    print(f"      {len(keywords)} keyword(s) loaded:")
    for keyword, weight in weights.items():
        print(f"        '{keyword}'  →  Weight {weight}")

    # ── STEP 2 ─────────────────────────────────────────────
    print("\n[2/5] Loading PDF folder ...")
    pdf_list = load_pdfs(folder_path)
    print(f"      {len(pdf_list)} PDF(s) found.")

    # ── STEP 3 ─────────────────────────────────────────────
    print("\n[3/5] Extracting text and counting keywords ...")

    # Data structure: hits[filename][keyword] = count
    hits: dict[str, dict[str, int]] = {}

    # LOOP: Select next PDF
    for pdf_path in pdf_list:
        filename = pdf_path.name
        print(f"\n  → Processing: {filename}")

        # Extract text from PDF
        text = extract_text(pdf_path)

        hits[filename] = {}

        # LOOP: Select next keyword
        for keyword in keywords:

            # Count exact occurrences (1:1 match, case-insensitive)
            count = count_occurrences(keyword, text)

            # Store hit
            hits[filename][keyword] = count

            print(f"     '{keyword}': {count}× found")

    # ── STEP 4 - Calculate score ───────────────────────────
    print("\n[4/5] Calculating scores ...")
    scores: dict[str, int] = {}

    for filename, keyword_hits in hits.items():
        score = sum(
            keyword_hits[keyword] * weights[keyword]
            for keyword in keywords
        )
        scores[filename] = score
        print(f"  '{filename}'  →  Score: {score}")

    # ── STEP 5 - Build and sort table ─────────────────────
    print("\n[5/5] Building and sorting table ...")

    rows = []
    for filename in hits:
        row = {"Source": filename}
        for keyword in keywords:
            row[keyword] = hits[filename][keyword]
        row["Score"] = scores[filename]
        rows.append(row)

    table = pd.DataFrame(rows)

    # Sort descending by score
    table = table.sort_values(by="Score", ascending=False)
    table = table.reset_index(drop=True)
    table.index += 1  # Rank starts at 1

    return table


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── Configure paths ────────────────────────────────────
    # Adjust these two paths to match your folder structure:
    FOLDER_PATH  = Path("sources")          # Folder containing PDF sources
    KEYWORD_FILE = Path("stichpunkte.txt")  # Text file with keywords

    print("=" * 60)
    print("  Source Relevance Scoring Algorithm")
    print("  FOM Hackathon 2026")
    print("=" * 60)
    print(f"  PDF folder   : {FOLDER_PATH.resolve()}")
    print(f"  Keyword file : {KEYWORD_FILE.resolve()}")

    # ── Timer Start ────────────────────────────────────────────
    start_time = time.perf_counter()

    # ── Run algorithm ──────────────────────────────────────────
    result_table = main_algorithm(FOLDER_PATH, KEYWORD_FILE)

    # ── Timer Stop + Ausgabe ───────────────────────────────────
    end_time = time.perf_counter()
    elapsed  = end_time - start_time
    print(f"\n[TIMER] Runtime: {elapsed:.4f} seconds")

    # ── Output ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESULT - Sources ranked by relevance")
    print("=" * 60 + "\n")

    print(tabulate(
        result_table,
        headers="keys",
        tablefmt="rounded_outline",
        showindex=True
    ))

    # CSV export
    csv_path = Path("result.csv")
    result_table.to_csv(csv_path, index=True, encoding="utf-8")
    print("=" * 60)
    print(f"[INFO] Begin CSV export ...")
    print(f"[INFO] Result saved to: {csv_path.resolve()}")
    print("=" * 60 + "\n")

    # XLSX export
    xlsx_path = Path("result.xlsx")
    result_table.to_excel(xlsx_path, sheet_name="Results", index=True)
    print("=" * 60)
    print(f"[INFO] Begin EXCEL export ...")
    print(f"[INFO] Result saved to: {xlsx_path.resolve()}")
    print("=" * 60)