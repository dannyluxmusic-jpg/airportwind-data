#!/usr/bin/env python3

import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
OUT_CSV = HERE / "airport_frequencies.csv"

VHF_MIN = 118.000
VHF_MAX = 136.975

# -----------------------
# HELPERS
# -----------------------

def norm_freq(s):
    try:
        v = float(s)
    except:
        return None
    if v < VHF_MIN or v > VHF_MAX:
        return None
    return "%.3f" % v


def extract_phone(raw):
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    return None


def add_row(rows, seen, icao, typ, val):
    if not icao or len(icao) != 4:
        return
    key = (icao, typ, val)
    if key in seen:
        return
    seen.add(key)
    rows.append(key)


# -----------------------
# MAIN
# -----------------------

def main():
    if not NASR_ZIP.exists():
        print("ERROR: NASR.zip not found")
        sys.exit(1)

    rows = []
    seen = set()
    ident3_to_icao = {}

    with zipfile.ZipFile(NASR_ZIP) as zf:

        # -------- APT: ICAO mapping + CTAF/UNICOM --------
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

        # -------- TWR frequencies --------
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

        # -------- AWOS / ASOS (REAL SOURCE) --------
        if "AWOS.txt" in zf.namelist():
            with zf.open("AWOS.txt") as f:
                for raw in f:
                    try:
                        line = raw.decode("latin-1")
                    except:
                        continue

                    parts = line.split("|")
                    if len(parts) < 10:
                        continue

                    ident = parts[0].strip()
                    phone_raw = parts[9].strip()
                    type_raw = parts[2].strip().upper()

                    phone = extract_phone(phone_raw)
                    if not phone:
                        continue

                    # Map type correctly
                    if "AWOS" in type_raw:
                        typ = "awos_phone"
                    elif "ASOS" in type_raw:
                        typ = "asos_phone"
                    else:
                        continue

                    # Convert 3-letter → ICAO
                    icao = ident3_to_icao.get(ident)
                    if not icao:
                        continue

                    add_row(rows, seen, icao, typ, phone)

    # -------- WRITE CSV --------
    with open(OUT_CSV, "w") as f:
        f.write("icao,type,value\n")
        for icao, typ, val in rows:
            f.write(f"{icao},{typ},{val}\n")


if __name__ == "__main__":
    main()
