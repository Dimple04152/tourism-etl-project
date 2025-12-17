import os
import pandas as pd
import tabula
import camelot
from pathlib import Path
from utils import parse_filename

PDF_FOLDER = Path("../pdf_raw")
OUTPUT_FOLDER = Path("../data_raw")

OUTPUT_FOLDER.mkdir(exist_ok=True)

def extract_tables(pdf_path):
    """
    Try Tabula first, fallback to Camelot.
    Returns list of DataFrames.
    """

    # Attempt Tabula
    try:
        tables = tabula.read_pdf(
            str(pdf_path),
            pages='all',
            multiple_tables=True,
            lattice=False,
            stream=True
        )
        if tables:
            print(f"✔ Tabula extracted {len(tables)} tables from {pdf_path.name}")
            return tables
    except:
        print("⚠ Tabula failed, trying Camelot…")

    # Fallback: Camelot
    try:
        cam_tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")
        if cam_tables:
            print(f"✔ Camelot extracted {len(cam_tables)} tables from {pdf_path.name}")
            return [t.df for t in cam_tables]
    except:
        print("❌ Camelot failed too.")

    print(f"❌ No tables extracted from {pdf_path.name}")
    return []


def main():
    pdf_files = sorted(PDF_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDFs found in pdf_raw folder.")
        return

    for pdf in pdf_files:
        print(f"\n📄 Processing {pdf.name}")

        try:
            month, year = parse_filename(pdf.name)
        except ValueError as e:
            print(f"❌ Filename error: {e}")
            continue

        tables = extract_tables(pdf)

        for idx, table_df in enumerate(tables, start=1):
            output_name = f"{year}_{month}_table{idx}.csv"
            output_path = OUTPUT_FOLDER / output_name

            table_df.to_csv(output_path, index=False)
            print(f"   → Saved: {output_name}")

    print("\n🎉 Extraction complete!")


if __name__ == "__main__":
    main()
