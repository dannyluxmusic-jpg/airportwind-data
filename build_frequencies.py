#!/usr/bin/env python3

import re
import zipfile
from pathlib import Path
import datetime

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
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

    if not NASR_ZIP.exists():
        print("NASR.zip missing")
        return

    with zipfile.ZipFile(NASR_ZIP) as zf:

        # -------------------------
        # 🔥 FIND AWOS FILE AUTOMATICALLY
        # -------------------------
        awos_file = None
        for name in zf.namelist():
            if "AWOS" in name.upper():
                awos_file = name
                break

        if not awos_file:
            print("NO AWOS FILE FOUND IN NASR")
            return

        print("Using:", awos_file)

        with zf.open(awos_file) as f:
            for raw in f:
                try:
                    line = raw.decode("latin-1")
                except:
                    continue

                # -------------------------
                # 🔥 REAL FAA FORMAT PARSING
                # -------------------------
                # Example format:
                # 06C AWOS 847-895-2887

                parts = line.split()

                if len(parts) < 3:
                    continue

                ident = parts[0].strip().upper()
                kind = parts[1].upper()
                phone = parts[-1]

                if not re.match(r"\d{3}-\d{3}-\d{4}", phone):
                    continue

                # FORCE ICAO
                if len(ident) <= 3:
                    icao = "K" + ident
                else:
                    icao = ident

                if "AWOS" in kind:
                    typ = "awos_phone"
                elif "ASOS" in kind:
                    typ = "asos_phone"
                else:
                    continue

                add_row(rows, seen, icao, typ, phone)

    # -------------------------
    # WRITE OUTPUT
    # -------------------------
    with open(OUT_CSV, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for icao, typ, val in sorted(rows):
            f.write(f"{icao},{typ},{val}\n")

if __name__ == "__main__":
    main()
