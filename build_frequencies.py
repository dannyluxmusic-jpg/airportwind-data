#!/usr/bin/env python3
"""
Build airport_frequencies.csv from a local NASR.zip.

Extracts:
- CTAF + UNICOM from APT.txt
- Tower/Approach/Departure/etc best-effort from TWR.txt

Output:
ICAO,TYPE,VALUE
"""

from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
OUT = HERE / "airport_frequencies.csv"

FREQ_RE = re.compile(r"\b(\d{2,3}\.\d{1,3})\b")


def norm_station(s: str) -> str:
    return (s or "").strip().upper()


def norm_freq(s: str) -> Optional[str]:
    if s is None:
        return None
    m = FREQ_RE.search(str(s))
    if not m:
        return None
    f = m.group(1)
    a, b = f.split(".", 1)
    b = (b + "000")[:3]
    return f"{a}.{b}"


def add_row(rows: List[Tuple[str, str, str]], seen: Set[Tuple[str, str, str]], icao: str, typ: str, freq: str):
    key = (icao, typ, freq)
    if key in seen:
        return
    seen.add(key)
    rows.append(key)


# ----- APT.txt slices (CTAF/UNICOM) -----
APT_ICAO = slice(27, 31)        # e.g. KLAX
APT_UNICOM = slice(981, 988)    # 7 chars
APT_CTAF = slice(988, 995)      # 7 chars


def parse_apt(zf: zipfile.ZipFile) -> Tuple[List[Tuple[str, str, str]], Dict[str, str]]:
    if "APT.txt" not in zf.namelist():
        raise SystemExit("ERROR: APT.txt not found inside NASR.zip")

    rows: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()
    ident3_to_icao: Dict[str, str] = {}

    print("Reading: APT.txt")
    with zf.open("APT.txt") as f:
        for raw in f:
            try:
                line = raw.decode("latin-1")
            except Exception:
                continue
            if not line.startswith("APT"):
                continue

            icao = norm_station(line[APT_ICAO])
            if not icao:
                continue

            # helpful map for TWR file (often uses 3-letter ids)
            if len(icao) == 4 and icao.startswith("K"):
                ident3_to_icao[icao[1:]] = icao

            unicom = norm_freq(line[APT_UNICOM].strip())
            ctaf = norm_freq(line[APT_CTAF].strip())

            if unicom:
                add_row(rows, seen, icao, "UNICOM", unicom)
            if ctaf:
                add_row(rows, seen, icao, "CTAF", ctaf)

    return rows, ident3_to_icao


# ----- TWR.txt parsing -----

def classify(line: str) -> str:
    u = line.upper()
    # order matters: some lines have both APCH and DEP
    if "ATIS" in u:
        return "ATIS"
    if "GND" in u or "GROUND" in u:
        return "GROUND"
    if "CLNC" in u or "CLEARANCE" in u or "CLR " in u:
        return "CLEARANCE"
    if "APCH" in u or "APPROACH" in u or " APP " in u:
        return "APPROACH"
    if " DEP" in u or "DEPARTURE" in u:
        return "DEPARTURE"
    if "CENTER" in u or " CTR" in u:
        return "CENTER"
    # default
    return "TOWER"


def best_effort_icao(ident: str, ident3_to_icao: Dict[str, str]) -> str:
    s = norm_station(ident).replace("*", "")
    if len(s) == 3 and s in ident3_to_icao:
        return ident3_to_icao[s]
    if len(s) == 3 and s.isalpha():
        return "K" + s
    return s


def parse_twr(zf: zipfile.ZipFile, ident3_to_icao: Dict[str, str]) -> List[Tuple[str, str, str]]:
    if "TWR.txt" not in zf.namelist():
        print("NOTE: TWR.txt not found; skipping tower/approach/etc")
        return []

    rows: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()

    print("Reading: TWR.txt")
    with zf.open("TWR.txt") as f:
        for raw in f:
            try:
                line = raw.decode("latin-1")
            except Exception:
                continue
            if not line.startswith("TWR"):
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            freq = norm_freq(parts[1])
            if not freq:
                continue

            # Find first plausible station token after the freq
            ident = None
            for tok in parts[2:25]:
                t = tok.strip().upper().replace("*", "")
                # skip region codes
                if t in {"AWP", "ASW", "AEA", "ACE", "AGL", "AAL", "ANM", "ASO"}:
                    continue
                if len(t) in (3, 4) and t.isalnum():
                    ident = t
                    break

            if not ident:
                continue

            icao = best_effort_icao(ident, ident3_to_icao)
            if not icao:
                continue

            typ = classify(line)
            add_row(rows, seen, icao, typ, freq)

    return rows


def main() -> int:
    if not NASR_ZIP.exists():
        print("ERROR: NASR.zip not found at:", NASR_ZIP)
        return 2

    with zipfile.ZipFile(NASR_ZIP, "r") as zf:
        apt_rows, ident_map = parse_apt(zf)
        twr_rows = parse_twr(zf, ident_map)

    rows = apt_rows + twr_rows
    rows.sort(key=lambda r: (r[0], r[1], r[2]))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ICAO", "TYPE", "VALUE"])
        w.writerows(rows)

    print(f"Wrote {OUT.name} rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())