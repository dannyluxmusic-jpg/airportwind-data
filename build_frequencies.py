#!/usr/bin/env python3

import zipfile
from pathlib import Path
import datetime
import re
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

    # -------------------------
    # UNZIP NASR
    # -------------------------
    with zipfile.ZipFile(NASR_ZIP) as z:
        z.extractall("nasr")

    # -------------------------
    # FREQUENCIES (WORKING LOGIC)
    # -------------------------

    # TWR.txt → tower / ground / approach / departure / clearance
    for name in Path("nasr").rglob("TWR.txt"):
        print("Using TWR:", name)

        with open(name, encoding="latin-1") as f:
            for line in f:

                parts = line.split()
                if len(parts) < 3:
                    continue

                ident = parts[0].strip().upper()

                if len(ident) == 3:
                    ident = "K" + ident

                # find frequency
                freq = None
                for p in parts:
                    try:
                        v = float(p)
                        if 118.0 <= v <= 136.975:
                            freq = f"{v:.3f}"
                            break
                    except:
                        continue

                if not freq:
                    continue

                u = line.upper()

                if "GND" in u:
                    typ = "ground"
                elif "CLNC" in u or "CLEAR" in u:
                    typ = "clearance"
                elif "APP" in u:
                    typ = "approach"
                elif "DEP" in u:
                    typ = "departure"
                else:
                    typ = "tower"

                add(rows, seen, ident, typ, freq)

    # APT.txt → CTAF / UNICOM
    for name in Path("nasr").rglob("APT.txt"):
        print("Using APT:", name)

        with open(name, encoding="latin-1") as f:
            for line in f:

                ident = line[27:31].strip().upper()

                if len(ident) == 3:
                    ident = "K" + ident

                try:
                    unicom = float(line[981:988])
                    if 118.0 <= unicom <= 136.975:
                        add(rows, seen, ident, "unicom", f"{unicom:.3f}")
                except:
                    pass

                try:
                    ctaf = float(line[988:995])
                    if 118.0 <= ctaf <= 136.975:
                        add(rows, seen, ident, "ctaf", f"{ctaf:.3f}")
                except:
                    pass

    # -------------------------
    # UNZIP CSV_Data (THIS IS WHAT'S MISSING)
    # -------------------------

    csv_zip = None
    for p in Path("nasr").rglob("*.zip"):
        if "CSV" in p.name.upper():
            csv_zip = p
            break

    if csv_zip:
        print("Using CSV ZIP:", csv_zip)

        with zipfile.ZipFile(csv_zip) as z:
            z.extractall("csv")
    else:
        print("NO CSV ZIP FOUND")
    
       # -------------------------
    # PHONES (AWOS.csv) — EXACT ORIGINAL WORKING VERSION
    # -------------------------

    awos_path = next(Path("csv").rglob("AWOS.csv"), None)

    if awos_path:
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
                
    # -------------------------
    # WRITE OUTPUT
    # -------------------------
    with open(OUT, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for r in sorted(rows):
            f.write(f"{r[0]},{r[1]},{r[2]}\n")

    print("TOTAL ROWS:", len(rows))


if __name__ == "__main__":
    main()
