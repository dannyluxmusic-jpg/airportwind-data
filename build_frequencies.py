#!/usr/bin/env python3

import zipfile
import re
from typing import Dict, List, Tuple, Set, Optional

NASR_ZIP = "NASR.zip"
OUTPUT_CSV = "airport_frequencies.csv"


# -----------------------------
# Utilities
# -----------------------------

def norm_station(s: str) -> str:
    s = s.strip().upper()
    if len(s) == 3:
        return "K" + s
    return s


def norm_freq(s: str) -> Optional[str]:
    s = s.strip()
    try:
        v = float(s)
    except:
        return None

    # Civil VHF COM band
    if 118.000 <= v <= 136.975:
        return f"{v:.3f}"

    return None


def add_row(rows: List[Tuple[str, str, str]],
            seen: Set[Tuple[str, str, str]],
            icao: str,
            typ: str,
            freq: str):

    key = (icao, typ, freq)
    if key not in seen:
        rows.append(key)
        seen.add(key)


# -----------------------------
# APT.txt (CTAF / UNICOM)
# -----------------------------

def parse_apt_txt(zf: zipfile.ZipFile):
    rows: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    ident3_to_icao: Dict[str, str] = {}

    print("Reading: APT.txt")

    with zf.open("APT.txt") as f:
        for raw in f:
            line = raw.decode("latin-1")

            if not line.startswith("APT"):
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            ident3 = parts[2].strip().upper()
            icao = norm_station(ident3)

            ident3_to_icao[ident3] = icao

            # Find frequency-like tokens (e.g. 122.700)
            freqs = re.findall(r"\d{3}\.\d{3}", line)

            for freq in freqs:
                f2 = norm_freq(freq)
                if f2:
                    # For now, treat first valid APT frequency as CTAF
                    add_row(rows, seen, icao, "CTAF", f2)

    return rows, ident3_to_icao


# -----------------------------
# TWR.txt (Tower / Approach / Departure)
# -----------------------------

def classify_twr_line(line: str) -> str:
    u = line.upper()

    if "GROUND" in u or " GND" in u:
        return "GROUND"

    if "CLEAR" in u or "CLR" in u:
        return "CLEARANCE"

    if "DEP" in u:
        return "DEPARTURE"

    if "APP" in u:
        return "APPROACH"

    if "TWR" in u:
        return "TOWER"

    return "APPROACH"


def parse_twr_txt(zf: zipfile.ZipFile, ident3_to_icao: Dict[str, str]):
    rows: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()

    if "TWR.txt" not in zf.namelist():
        print("TWR.txt not found.")
        return rows

    print("Reading: TWR.txt")

    with zf.open("TWR.txt") as f:
        for raw in f:
            line = raw.decode("latin-1")

            if not line.startswith("TWR"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            freq = norm_freq(parts[1])
            if not freq:
                continue

            ident = None

            for tok in parts:
                t = tok.strip().upper().replace("*", "")
                if len(t) == 3 and t in ident3_to_icao:
                    ident = t
                    break

            if not ident:
                continue

            icao = ident3_to_icao.get(ident)
            if not icao:
                continue

            typ = classify_twr_line(line)
            add_row(rows, seen, icao, typ, freq)

    return rows


# -----------------------------
# Main
# -----------------------------

def main():
    print("Opening:", NASR_ZIP)

    with zipfile.ZipFile(NASR_ZIP) as zf:
        apt_rows, ident_map = parse_apt_txt(zf)
        twr_rows = parse_twr_txt(zf, ident_map)

    all_rows = apt_rows + twr_rows

    print("Writing:", OUTPUT_CSV)

    with open(OUTPUT_CSV, "w") as f:
        f.write("icao,type,value\n")
        for icao, typ, freq in sorted(all_rows):
            f.write(f"{icao},{typ},{freq}\n")

    print("Done. Total rows:", len(all_rows))


if __name__ == "__main__":
    main()