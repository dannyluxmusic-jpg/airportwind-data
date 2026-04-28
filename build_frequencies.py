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

FREQ_RE = re.compile(r"(?:^|[^0-9])((?:\d{2,3})\.\d{1,3})(?:[^0-9]|$)")
PHONE_RE = re.compile(r"\b\d{3}[-\.]?\d{3}[-\.]?\d{4}\b")

def norm_freq(s):
    s = s.strip()
    if not re.match(r"^\d{2,3}\.\d{1,3}$", s):
        return None
    try:
        v = float(s)
    except:
        return None
    if v < VHF_MIN or v > VHF_MAX:
        return None
    return "%.3f" % v

def extract_vhf(line):
    out = []
    for m in FREQ_RE.finditer(line):
        f = norm_freq(m.group(1))
        if f:
            out.append(f)
    return out

def extract_phone(line):
    phones = []
    for m in PHONE_RE.findall(line):
        digits = re.sub(r"\D", "", m)
        if len(digits) == 10:
            phones.append(f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}")
    return phones

def add_row(rows, seen, icao, typ, value):
    key = (icao, typ, value)
    if key in seen:
        return
    seen.add(key)
    rows.append(key)

def classify_twr(line):
    u = line.upper()
    types = []

    if "APCH" in u or "APP" in u:
        types.append("approach")
    if "DEP" in u:
        types.append("departure")
    if "GND" in u or "GROUND" in u:
        types.append("ground")
    if "CLNC" in u or "CLEAR" in u or "CD/" in u:
        types.append("clearance")
    if "CTR" in u or "CENTER" in u:
        types.append("center")

    if not types:
        types.append("tower")

    return list(dict.fromkeys(types))

def pick_airport_ident(parts, ident3_to_icao):
    for tok in parts:
        t = tok.strip().upper().replace("*", "")
        if len(t) == 3 and t in ident3_to_icao:
            return ident3_to_icao[t]
    for tok in parts:
        t = tok.strip().upper().replace("*", "")
        if len(t) == 4 and t.isalnum():
            return t
    return None

def main():
    if not NASR_ZIP.exists():
        print("ERROR: NASR.zip not found")
        sys.exit(1)

    rows = []
    seen = set()
    ident3_to_icao = {}

    print("Opening:", NASR_ZIP.name)

    with zipfile.ZipFile(NASR_ZIP) as zf:

        # -------- APT.txt --------
        print("Reading: APT.txt")

        with zf.open("APT.txt") as f:
            for raw in f:
                try:
                    line = raw.decode("latin-1")
                except:
                    continue

                if not line.startswith("APT"):
                    continue

                # ICAO mapping
                m3 = re.search(r"\bAIRPORT\s+([A-Z0-9]{3})\b", line)
                m4 = re.search(r"\bL([A-Z0-9]{4})\b", line)

                if m3 and m4:
                    ident3_to_icao[m3.group(1)] = m4.group(1)

                # extract ICAO
                icao = None
                for k, v in ident3_to_icao.items():
                    if k in line:
                        icao = v
                        break

                if not icao:
                    continue

                # CTAF / UNICOM fixed positions
                if len(line) >= 995:
                    unicom = norm_freq(line[981:988])
                    ctaf = norm_freq(line[988:995])

                    if unicom:
                        add_row(rows, seen, icao, "unicom", unicom)
                    if ctaf:
                        add_row(rows, seen, icao, "ctaf", ctaf)

                # PHONE extraction (NEW)
                phones = extract_phone(line)
                for p in phones:
                    add_row(rows, seen, icao, "wx_phone", p)

        # -------- TWR.txt --------
        if "TWR.txt" in zf.namelist():
            print("Reading: TWR.txt")

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

                    icao = pick_airport_ident(parts, ident3_to_icao)
                    if not icao:
                        continue

                    for typ in classify_twr(line):
                        add_row(rows, seen, icao, typ, freq)

        # -------- Weather files --------
        for weather_file in ["AWOS.txt", "WXL.txt"]:
            if weather_file not in zf.namelist():
                continue

            print("Reading:", weather_file)

            with zf.open(weather_file) as f:
                for raw in f:
                    try:
                        line = raw.decode("latin-1")
                    except:
                        continue

                    parts = line.split()
                    icao = pick_airport_ident(parts, ident3_to_icao)
                    if not icao:
                        continue

                    for fr in extract_vhf(line):
                        add_row(rows, seen, icao, "awos", fr)

    print("Writing:", OUT_CSV.name)

    with open(OUT_CSV, "w") as f:
        f.write("icao,type,value\n")
        for icao, typ, val in rows:
            f.write(f"{icao},{typ},{val}\n")

    print("Done. Total rows:", len(rows))


if __name__ == "__main__":
    main()
