#!/usr/bin/env python3

import zipfile
from pathlib import Path
import datetime
import re

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

        # 🔥 LIST FILES (debug once)
        print("FILES IN ZIP:")
        for name in zf.namelist():
            if "AWOS" in name.upper():
                print("FOUND:", name)

        # 🔥 CORRECT FILE (FAA)
        target = None
        for name in zf.namelist():
            if "AWOS" in name.upper():
                target = name
                break

        if not target:
            print("NO AWOS FILE FOUND")
            return

        print("USING:", target)

        with zf.open(target) as f:
            for raw in f:
                try:
                    line = raw.decode("latin-1")
                except:
                    continue

                # FAA format example:
                # IDENT TYPE ... PHONE
                if "AWOS" not in line and "ASOS" not in line:
                    continue

                # extract phone
                match = re.search(r"\d{3}-\d{3}-\d{4}", line)
                if not match:
                    continue

                phone = match.group()

                ident = line[0:4].strip().upper()

                if not ident:
                    continue

                icao = "K" + ident if len(ident) == 3 else ident

                if "AWOS" in line:
                    typ = "awos_phone"
                else:
                    typ = "asos_phone"

                add_row(rows, seen, icao, typ, phone)

    with open(OUT_CSV, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for icao, typ, val in sorted(rows):
            f.write(f"{icao},{typ},{val}\n")

    print(f"Wrote {len(rows)} phone numbers")

if __name__ == "__main__":
    main()
