"""Download official Malaysian donation history for HemoLink forecasting.

Run once with an internet connection:
    python scripts/download_data.py
Or pass an existing official CSV:
    python scripts/download_data.py --local path/to/blood_donations_state.csv
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
import tempfile
import pandas as pd
import requests

# 1) MOH Malaysia's own GitHub repository (wide layout: daily, blood_a, blood_b, blood_o, blood_ab)
# 2) data.gov.my storage (long layout: date, state, blood_type, donations)
SOURCES = [
    ("https://raw.githubusercontent.com/MoH-Malaysia/data-darah-public/main/donations_state.csv", "donations_state.csv"),
    ("https://storage.data.gov.my/healthcare/blood_donations_state.csv", "blood_donations_state.csv"),
]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEST = DATA_DIR / "donations_state.csv"
LAYOUTS = [{"date", "state", "daily", "blood_a", "blood_b", "blood_o", "blood_ab"}, {"date", "state", "blood_type", "donations"}]


def validate(path):
    df = pd.read_csv(path, nrows=300)
    if not any(layout.issubset(set(df.columns)) for layout in LAYOUTS):
        raise ValueError(f"Unexpected columns {list(df.columns)}; expected the MOH blood donation layout")
    if len(df)<20:
        raise ValueError("The CSV is unexpectedly short")
    date_check = pd.to_datetime(df["date"],errors="coerce")
    if date_check.notna().sum()<20:
        raise ValueError("Dates in this file cannot be parsed")


def main():
    parser=argparse.ArgumentParser(description="Import the official KKMNOW state-level donation dataset")
    parser.add_argument("--local",type=Path,help="Use an existing local CSV rather than downloading")
    args=parser.parse_args()
    DATA_DIR.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=DATA_DIR,suffix=".csv",delete=False) as f:
        tmp=Path(f.name)
    try:
        dest=DEST
        if args.local:
            if not args.local.is_file():raise FileNotFoundError(args.local)
            shutil.copyfile(args.local,tmp)
        else:
            last_error=None
            for url,name in SOURCES:
                try:
                    print(f"Downloading from {url} ...")
                    with requests.get(url,timeout=90,stream=True) as response:
                        response.raise_for_status()
                        with open(tmp,"wb") as target:
                            total=0
                            for chunk in response.iter_content(1024*256):
                                total+=len(chunk)
                                if total>100*1024*1024:raise ValueError("Dataset unexpectedly large (>100 MB)")
                                target.write(chunk)
                    dest=DATA_DIR/name
                    break
                except Exception as exc:  # try the next source
                    last_error=exc
                    print(f"  failed: {exc}")
            else:
                raise RuntimeError(f"All sources failed: {last_error}")
        validate(tmp)
        tmp.replace(dest)
        DEST_USED=dest
        print(f"Official CSV imported: {DEST_USED}")
        print("Data source: Ministry of Health Malaysia / National Blood Centre (CC BY 4.0)")
        print("Next: python scripts/train_models.py   (trains and saves every model, writes docs/MODEL_REPORT.md)")
        print("These are collection counts, not actual blood inventory or patient demand.")
    finally:
        tmp.unlink(missing_ok=True)

if __name__=="__main__":
    try:main()
    except Exception as ex:
        print(f"Import failed: {ex}",file=sys.stderr)
        sys.exit(1)
