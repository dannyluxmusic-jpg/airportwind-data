#!/usr/bin/env python3

import re
import sys
import zipfile
import csv
from pathlib import Path
import datetime

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
AWOS_CSV = HERE / "AWOS.csv"
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
    rows = []
    seen = set()

    # ======================
    # NASR FREQUENCIES
    # ======================
    if NASR_ZIP.exists():
        with zipfile.ZipFile(NASR_ZIP) as zf:

            if "APT.txt" in zf.namelist():
                with zf.open("APT.txt") as f:
                    for raw in f:
                        try:
                            line = raw.decode("latin-1")
                        except:
                            continue

                        if not line.startswith("APT") or " AIRPORT " not in line:
                            continue

                        m4 = re.search(r"\bL([A-Z0-9]{4})\b", line)
                        if not m4:
                            continue

                        icao = m4.group(1)

                        if len(line) >= 995:
                            unicom = norm_freq(line[981:988])
                            ctaf = norm_freq(line[988:995])

                            if unicom:
                                add_row(rows, seen, icao, "unicom", unicom)
                            if ctaf:
                                add_row(rows, seen, icao, "ctaf", ctaf)

    # ======================
    # 🔥 AWOS PHONES (WORKS NO MATTER WHAT YOUR CSV LOOKS LIKE)
    # ======================
    if AWOS_CSV.exists():
        with open(AWOS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)

            for row in reader:
                if len(row) < 3:
                    continue

                ident = row[0].strip().upper()
                kind = row[1].strip().upper()
                phone1 = row[2].strip()

                phone2 = row[3].strip() if len(row) > 3 else ""

                if not ident:
                    continue

                # 🔥 FORCE ICAO (this is the fix)
                if len(ident) <= 3:
                    icao = "K" + ident
                else:
                    icao = ident

                # type
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

    # ======================
    # WRITE OUTPUT (FORCE UPDATE EVERY RUN)
    # ======================
    with open(OUT_CSV, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for icao, typ, val in sorted(rows):
            f.write(f"{icao},{typ},{val}\n")

if __name__ == "__main__":
    main()
