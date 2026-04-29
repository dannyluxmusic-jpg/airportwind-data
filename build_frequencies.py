#!/usr/bin/env python3

import zipfile
from pathlib import Path
import datetime
import csv

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
OUT = HERE / "airport_frequencies.csv"

def add(rows, seen, icao, typ, val):
    key = (icao, typ, val)
    if key in seen:
        return
    seen.add(key)
    rows.append(key)

def main():
    rows = []
    seen = set()

    # unzip NASR
    with zipfile.ZipFile(NASR_ZIP) as z:
        z.extractall("nasr")

    # unzip CSV_Data
    csv_zip = None
    for p in Path("nasr").rglob("*.zip"):
        if "CSV" in p.name.upper():
            csv_zip = p
            break

    if not csv_zip:
        print("NO CSV ZIP FOUND")
        return

    with zipfile.ZipFile(csv_zip) as z:
        z.extractall("csv")

    # -------------------------
    # PHONES ONLY (this is what worked before)
    # -------------------------

    awos_path = next(Path("csv").rglob("AWOS.csv"), None)

    if not awos_path:
        print("NO AWOS.csv FOUND")
        return

    print("Using AWOS:", awos_path)

    with open(awos_path, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ident = (row.get("ARPT_ID") or "").strip().upper()
            phone = (row.get("PHONE_NO") or "").strip()

            if not ident or not phone:
                continue

            if len(ident) == 3:
                ident = "K" + ident

            if "ASOS" in str(row).upper():
                typ = "asos_phone"
            else:
                typ = "awos_phone"

            add(rows, seen, ident, typ, phone)

    # write output
    with open(OUT, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for r in sorted(rows):
            f.write(f"{r[0]},{r[1]},{r[2]}\n")

    print("TOTAL ROWS:", len(rows))


if __name__ == "__main__":
    main()
