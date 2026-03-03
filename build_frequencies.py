#!/usr/bin/env python3
import csv
import re
import zipfile
from pathlib import Path

OUTPUT_FILE = "airport_frequencies.csv"
NASR_ZIP_PATH = "NASR.zip"

# --- helpers ---
def norm_freq(s):
    if s is None:
        return ""
    s = str(s).strip()
    # keep digits + dot only
    s = "".join(c for c in s if c.isdigit() or c == ".")
    # basic sanity: must contain at least 3 digits
    if len(re.sub(r"\D", "", s)) < 3:
        return ""
    return s

def norm_type(s):
    if not s:
        return ""
    s = str(s).strip().upper()
    s = re.sub(r"\s+", " ", s)

    # common cleanups
    # take first "word-ish" token like ATIS, TWR, GND, CTAF, UNICOM, RCO, AWOS, ASOS, APP, DEP, CLR, etc.
    token = re.split(r"[^A-Z0-9]+", s)[0].strip()

    # map a few variants
    mapping = {
        "TOWER": "TWR",
        "GROUND": "GND",
        "APPROACH": "APP",
        "DEPARTURE": "DEP",
        "CLEARANCE": "CLR",
        "UNICOM": "UNICOM",
        "CTAF": "CTAF",
        "ATIS": "ATIS",
        "AWOS": "AWOS",
        "ASOS": "ASOS",
        "RCO": "RCO",
    }
    return mapping.get(token, token)

def to_icao(ident):
    ident = (ident or "").strip().upper()
    if not ident:
        return ""
    # If already looks like ICAO (4 chars), keep it
    if len(ident) == 4:
        return ident
    # If 3-letter FAA/IATA style, most US airports are K + ident
    if len(ident) == 3 and ident.isalnum():
        return "K" + ident
    # Otherwise keep as-is (some facilities use different formats)
    return ident

def open_nasr_zip():
    zp = Path(NASR_ZIP_PATH)
    if not zp.exists():
        raise SystemExit(f"ERROR: {NASR_ZIP_PATH} not found in {Path.cwd()}. Download it first.")
    print("Opening NASR from:", zp.resolve())
    return zipfile.ZipFile(zp)

def find_apt_com(zip_file):
    for name in zip_file.namelist():
        if name.upper().endswith("APT_COM.TXT") or "APT_COM.TXT" in name.upper():
            print("Found:", name)
            return name
    raise SystemExit("ERROR: APT_COM.txt not found inside NASR.zip")

def parse_apt_com(zip_file, member_name):
    out = []
    seen = set()

    # NOTE: APT_COM is fixed-width; these slices match what you already had.
    # If FAA shifts widths in the future, we’ll adjust.
    with zip_file.open(member_name) as f:
        for raw in f:
            try:
                line = raw.decode("latin-1", errors="ignore")
            except Exception:
                continue

            # skip headers/blank
            if not line.startswith("APT"):
                continue

            ident = line[27:31].strip()
            freq  = line[53:60].strip()
            typ   = line[121:140].strip()

            icao = to_icao(ident)
            freq = norm_freq(freq)
            typ  = norm_type(typ)

            if not icao or not freq or not typ:
                continue

            key = (icao, typ, freq)
            if key in seen:
                continue
            seen.add(key)
            out.append(key)

    return out

def write_csv(rows):
    rows.sort()
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ICAO","TYPE","VALUE"])
        w.writerows(rows)
    print(f"Wrote {OUTPUT_FILE} rows: {len(rows)}")

def main():
    z = open_nasr_zip()
    member = find_apt_com(z)
    rows = parse_apt_com(z, member)
    write_csv(rows)

if __name__ == "__main__":
    main()
