#!/usr/bin/env python3

import csv
from pathlib import Path
import datetime

HERE = Path(__file__).resolve().parent
AWOS_FILE = HERE / "AWOS.csv"
OUT_CSV = HERE / "airport_frequencies.csv"

def add_row(rows, seen, icao, typ, val):
    key = (icao, typ, val)
    if key in seen:
        return
    seen.add(key)
    rows.append(key)

def main():
    rows = []
    seen = set()

    if not AWOS_FILE.exists():
        print("AWOS.csv NOT FOUND")
        return

    print("Reading AWOS.csv...")

    with open(AWOS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)

        for r in reader:
            if len(r) < 3:
                continue

            ident = r[0].strip().upper()
            kind = r[1].strip().upper()
            phone1 = r[2].strip()
            phone2 = r[3].strip() if len(r) > 3 else ""

            if not ident:
                continue

            # ICAO normalization
            icao = "K" + ident if len(ident) == 3 else ident

            if "AWOS" in kind:
                typ = "awos_phone"
            elif "ASOS" in kind:
                typ = "asos_phone"
            else:
                continue

            if phone1:
                add_row(rows, seen, icao, typ, phone1)

            if phone2:
                add_row(rows, seen, icao, typ, phone2)

    with open(OUT_CSV, "w") as f:
        # FORCE UPDATE EVERY RUN
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for icao, typ, val in sorted(rows):
            f.write(f"{icao},{typ},{val}\n")

    print(f"Wrote {len(rows)} phone numbers")

if __name__ == "__main__":
    main()
