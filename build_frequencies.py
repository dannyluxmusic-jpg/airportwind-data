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

def add_row(rows, seen, icao, typ, freq):
    key = (icao, typ, freq)
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

def weather_kind_from_line(filename, line):
    u = line.upper()

    if "ATIS" in u:
        return "atis"
    if "ASOS" in u:
        return "asos"
    if "AWOS" in u:
        return "awos"

    if filename.upper().startswith("AWOS"):
        return "awos"
    if filename.upper().startswith("WXL"):
        return "atis"

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

        # ---------------------------
        # APT.txt (Fixed-width UNICOM / CTAF)
        # ---------------------------
        if "APT.txt" not in zf.namelist():
            print("ERROR: APT.txt missing")
            sys.exit(1)

        print("Reading: APT.txt")

        with zf.open("APT.txt") as f:
            for raw in f:
                try:
                    line = raw.decode("latin-1")
                except:
                    continue

                if not line.startswith("APT"):
                    continue
                if " AIRPORT " not in line:
                    continue

                m3 = re.search(r"\bAIRPORT\s+([A-Z0-9]{3})\b", line)
                if not m3:
                    continue
                ident3 = m3.group(1)

                m4 = re.search(r"\bL([A-Z0-9]{4})\b", line)
                if not m4:
                    continue
                icao = m4.group(1)

                ident3_to_icao[ident3] = icao

                # FAA Layout_Data/apt_rf.txt positions:
                # UNICOM freq: cols 982–988 (1-based)
                # CTAF freq:   cols 989–995 (1-based)

                if len(line) >= 995:
                    unicom_raw = line[981:988]
                    ctaf_raw   = line[988:995]

                    unicom = norm_freq(unicom_raw)
                    ctaf   = norm_freq(ctaf_raw)

                    if unicom:
                        add_row(rows, seen, icao, "unicom", unicom)
                    if ctaf:
                        add_row(rows, seen, icao, "ctaf", ctaf)

        # ---------------------------
        # TWR.txt
        # ---------------------------
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

        # ---------------------------
        # Weather files
        # ---------------------------
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

                    kind = weather_kind_from_line(weather_file, line)
                    if not kind:
                        continue

                    parts = line.split()
                    icao = pick_airport_ident(parts, ident3_to_icao)
                    if not icao:
                        continue

                    for fr in extract_vhf(line):
                        add_row(rows, seen, icao, kind, fr)

    print("Writing:", OUT_CSV.name)

    with open(OUT_CSV, "w") as f:
        f.write("icao,type,value\n")
        for icao, typ, val in rows:
            f.write("%s,%s,%s\n" % (icao, typ, val))

    print("Done. Total rows:", len(rows))


if __name__ == "__main__":
    main()
