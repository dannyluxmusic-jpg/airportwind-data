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

def norm_freq(val):
    try:
        f = float(val)
        if 118.0 <= f <= 136.975:
            return f"{f:.3f}"
    except:
        return None
    return None

def main():
    rows = []
    seen = set()

    if not NASR_ZIP.exists():
        print("NASR.zip missing")
        return

    with zipfile.ZipFile(NASR_ZIP) as zf:

        # -------------------------
        # APT (UNICOM / CTAF)
        # -------------------------
        if "APT.txt" in zf.namelist():
            with zf.open("APT.txt") as f:
                for raw in f:
                    line = raw.decode("latin-1")

                    ident = line[27:31].strip().upper()
                    if not ident:
                        continue

                    unicom = norm_freq(line[981:988])
                    ctaf = norm_freq(line[988:995])

                    if unicom:
                        add_row(rows, seen, ident, "unicom", unicom)
                    if ctaf:
                        add_row(rows, seen, ident, "ctaf", ctaf)

        # -------------------------
        # TWR (ALL COM FREQUENCIES)
        # -------------------------
        if "TWR.txt" in zf.namelist():
            with zf.open("TWR.txt") as f:
                for raw in f:
                    line = raw.decode("latin-1")

                    parts = line.split()
                    if len(parts) < 3:
                        continue

                    ident = parts[0].strip().upper()
                    freq = norm_freq(parts[1])

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

                    add_row(rows, seen, ident, typ, freq)

        # -------------------------
        # AWOS / ASOS PHONES
        # -------------------------
        for name in zf.namelist():
            if "AWOS" in name.upper() or "ASOS" in name.upper():

                with zf.open(name) as f:
                    for raw in f:
                        line = raw.decode("latin-1")

                        if "AWOS" not in line and "ASOS" not in line:
                            continue

                        phone_match = re.search(r"\d{3}-\d{3}-\d{4}", line)
                        if not phone_match:
                            continue

                        phone = phone_match.group()

                        ident = line[0:4].strip().upper()
                        if not ident:
                            continue

                        if "AWOS" in line:
                            typ = "awos_phone"
                        else:
                            typ = "asos_phone"

                        add_row(rows, seen, ident, typ, phone)

    # -------------------------
    # WRITE OUTPUT
    # -------------------------
    with open(OUT_CSV, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for r in sorted(rows):
            f.write(f"{r[0]},{r[1]},{r[2]}\n")

    print(f"TOTAL ROWS: {len(rows)}")

if __name__ == "__main__":
    main()
