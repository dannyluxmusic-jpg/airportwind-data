#!/usr/bin/env python3
import csv
import os
import re
import zipfile

OUT = "airport_frequencies.csv"
NASR_ZIP_PATH = "NASR.zip"

# Field locations are defined in Layout_Data/apt_rf.txt inside NASR.
# We use the APT record fields:
# - ICAO IDENTIFIER (A12) at positions 1211-1217 (length 7)
# - UNICOM FREQUENCY AVAILABLE (A82) at positions 982-988 (length 7)
# - COMMON TRAFFIC ADVISORY FREQUENCY (CTAF) (E100) at positions 989-995 (length 7)
#
# NOTE: NASR layout files are 1-based positions.
# Python slicing is 0-based and end-exclusive.
#
# So:
# 982..988 => [981:988]
# 989..995 => [988:995]
# 1211..1217 => [1210:1217]
SL_ICAO = (1210, 1217)
SL_UNICOM = (981, 988)
SL_CTAF = (988, 995)

def normalize_icao(s: str) -> str:
    return (s or "").strip().upper()

def normalize_freq(s: str) -> str:
    if not s:
        return ""
    s = (s or "").strip()
    # keep digits and dot only
    s = "".join(ch for ch in s if ch.isdigit() or ch == ".")
    # basic sanity: must contain at least 3 digits
    digits = sum(ch.isdigit() for ch in s)
    return s if digits >= 3 else ""

def open_nasr_zip() -> zipfile.ZipFile:
    path = os.path.abspath(NASR_ZIP_PATH)
    print("Opening NASR from:", path)
    if not os.path.exists(path):
        raise SystemExit(f"ERROR: {NASR_ZIP_PATH} not found in repo folder. Expected: {path}")
    return zipfile.ZipFile(path)

def find_member(z: zipfile.ZipFile, wanted_basename: str) -> str:
    want = wanted_basename.upper()
    for name in z.namelist():
        if name.upper().endswith("/" + want) or name.upper() == want:
            return name
    raise SystemExit(f"ERROR: {wanted_basename} not found inside NASR.zip")

def parse_from_apt_txt(z: zipfile.ZipFile) -> list[tuple[str, str, str]]:
    apt_name = find_member(z, "APT.txt")
    print("Reading:", apt_name)

    out_rows: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    with z.open(apt_name) as f:
        for raw in f:
            try:
                line = raw.decode("latin-1", errors="ignore")
            except Exception:
                continue

            # Only APT records
            if not line.startswith("APT"):
                continue

            icao = normalize_icao(line[SL_ICAO[0]:SL_ICAO[1]])
            if not icao:
                continue

            unicom = normalize_freq(line[SL_UNICOM[0]:SL_UNICOM[1]])
            ctaf = normalize_freq(line[SL_CTAF[0]:SL_CTAF[1]])

            if unicom:
                key = (icao, "UNICOM", unicom)
                if key not in seen:
                    seen.add(key)
                    out_rows.append(key)

            if ctaf:
                key = (icao, "CTAF", ctaf)
                if key not in seen:
                    seen.add(key)
                    out_rows.append(key)

    return out_rows

def write_csv(rows: list[tuple[str, str, str]]) -> None:
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ICAO", "TYPE", "VALUE"])
        w.writerows(rows)

def main() -> None:
    z = open_nasr_zip()
    rows = parse_from_apt_txt(z)
    write_csv(rows)
    print("Wrote", OUT, "rows:", len(rows))

if __name__ == "__main__":
    main()