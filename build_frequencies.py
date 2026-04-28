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

# -----------------------
# HELPERS
# -----------------------

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


def extract_phone(line):
    phones = re.findall(r'\b\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}\b', line)
    out = []
    for p in phones:
        p = re.sub(r'\D', '', p)
        if len(p) == 10:
            out.append(f"{p[0:3]}-{p[3:6]}-{p[6:10]}")
    return out


def add_row(rows, seen, icao, typ, val):
    if not re.match(r"^[A-Z0-9]{4}$", icao):
        return
    key = (icao, typ, val)
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


def detect_weather_type(line):
    u = line.upper()
    if "ATIS" in u:
        return "atis_phone"
    if "AWOS" in u:
        return "awos_phone"
    if "ASOS" in u:
        return "asos_phone"
    return None


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

        # -------- APT: ICAO + CTAF/UNICOM --------
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

        # -------- TWR --------
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

                    icao = pick_airport_ident(parts, ident3_to_icao)
                    if not icao:
                        continue

                    for typ in classify_twr(line):
                        add_row(rows, seen, icao, typ, freq)

        # -------- WEATHER PHONES (FIXED LOGIC) --------
        with zf.open("APT.txt") as f:
            current_icao = None

            for raw in f:
                try:
                    line = raw.decode("latin-1")
                except:
                    continue

                if line.startswith("APT") and " AIRPORT " in line:
                    m4 = re.search(r"\bL([A-Z0-9]{4})\b", line)
                    if m4:
                        current_icao = m4.group(1)

                if not current_icao:
                    continue

                typ = detect_weather_type(line)
                if not typ:
                    continue

                phones = extract_phone(line)
                for p in phones:
                    add_row(rows, seen, current_icao, typ, p)

    # -------- WRITE CSV --------
    with open(OUT_CSV, "w") as f:
        f.write("icao,type,value\n")
        for icao, typ, val in rows:
            f.write(f"{icao},{typ},{val}\n")


if __name__ == "__main__":
    main()
