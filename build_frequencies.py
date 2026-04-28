#!/usr/bin/env python3

import csv
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
PHONES_CSV = HERE / "awos_asos_phones.csv"
OUT_CSV = HERE / "airport_frequencies.csv"

VHF_MIN = 118.000
VHF_MAX = 136.975

def norm_freq(s):
    try:
        v = float(s)
    except:
        return None
    if v < VHF_MIN or v > VHF_MAX:
        return None
    return "%.3f" % v

def add_row(rows, seen, icao, typ, val):
    if not icao or len(icao) != 4:
        return
    key = (icao, typ, val)
    if key in seen:
        return
    seen.add(key)
    rows.append(key)

def main():
    if not NASR_ZIP.exists():
        print("ERROR: NASR.zip not found")
        sys.exit(1)

    rows = []
    seen = set()
    ident3_to_icao = {}

    # ---------------- NASR ----------------
    with zipfile.ZipFile(NASR_ZIP) as zf:

        # APT mapping
        with zf.open("APT.txt") as f:
            for raw in f:
                try:
                    line = raw.decode("latin-1")
                except:
                    continue

                if not line.startswith("APT") or " AIRPORT " not in line:
                    continue

                m3 = re.search(r"\bAIRPORT\s+([A-Z0-9]{3})\b", line)
                m4 = re.search(r"\bL([A-Z0-9]{4})\b", line)

                if not m3 or not m4:
                    continue

                ident3 = m3.group(1)
                icao = m4.group(1)
                ident3_to_icao[ident3] = icao

                if len(line) >= 995:
                    unicom = norm_freq(line[981:988])
                    ctaf = norm_freq(line[988:995])

                    if unicom:
                        add_row(rows, seen, icao, "unicom", unicom)
                    if ctaf:
                        add_row(rows, seen, icao, "ctaf", ctaf)

        # TWR
        if "TWR.txt" in zf.namelist():
            with zf.open("TWR.txt") as f:
                for raw in f:
                    try:
                        line = raw.decode("latin-1")
                    except:
                        continue

                    if not line.startswith("TWR"):
                        continue

                    parts = line.split()
                    if len(parts) < 2:
                        continue

                    freq = norm_freq(parts[1])
                    if not freq:
                        continue

                    icao = None
                    for tok in parts:
                        t = tok.strip().upper()
                        if len(t) == 3 and t in ident3_to_icao:
                            icao = ident3_to_icao[t]
                            break

                    if not icao:
                        continue

                    add_row(rows, seen, icao, "tower", freq)

    # ---------------- PHONES (TRUSTED) ----------------
    if PHONES_CSV.exists():
        with open(PHONES_CSV) as f:
            reader = csv.DictReader(f)
            for row in reader:
                add_row(
                    rows,
                    seen,
                    row["icao"].strip().upper(),
                    row["type"].strip(),
                    row["value"].strip()
                )

    # ---------------- WRITE ----------------
    with open(OUT_CSV, "w") as f:
        f.write("icao,type,value\n")
        for icao, typ, val in rows:
            f.write(f"{icao},{typ},{val}\n")

if __name__ == "__main__":
    main()
