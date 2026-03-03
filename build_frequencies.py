#!/usr/bin/env python3
import csv
import re
import zipfile
from pathlib import Path

NASR_ZIP = Path("NASR.zip")
OUTPUT_FILE = Path("airport_frequencies.csv")

# Offsets from Layout_Data/apt_rf.txt (1-based -> convert to 0-based slices)
LOC_ID_START, LOC_ID_LEN = 28, 4
UNICOM_START, UNICOM_LEN = 982, 7
CTAF_START, CTAF_LEN     = 989, 7
ICAO_START, ICAO_LEN     = 1211, 7

def sl(line: str, start_1based: int, length: int) -> str:
    i = start_1based - 1
    return line[i:i+length].strip()

def norm_freq(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return ""
    # Normalize common forms like 122900 -> 122.900
    if "." not in s and len(s) >= 5:
        s = s[:-3] + "." + s[-3:]
    # Remove trailing zeros after decimal, but keep at least one decimal digit
    if "." in s:
        left, right = s.split(".", 1)
        right = right.rstrip("0")
        if right == "":
            right = "0"
        s = left + "." + right
    return s

def main():
    if not NASR_ZIP.exists():
        raise SystemExit(f"ERROR: {NASR_ZIP} not found. (You already downloaded it once; put it in this folder.)")

    with zipfile.ZipFile(NASR_ZIP, "r") as z:
        # APT.txt exists at root in your zip listing
        members = [n for n in z.namelist() if n.upper().endswith("APT.TXT")]
        if not members:
            raise SystemExit("ERROR: APT.txt not found in NASR.zip")
        apt_name = members[0]
        print("Reading:", apt_name)

        out = []
        seen = set()

        with z.open(apt_name, "r") as f:
            for raw in f:
                try:
                    line = raw.decode("latin-1", errors="ignore")
                except Exception:
                    continue

                if not line.startswith("APT"):
                    continue

                icao = sl(line, ICAO_START, ICAO_LEN)
                loc  = sl(line, LOC_ID_START, LOC_ID_LEN)

                # ICAO field is preferred; fallback to loc id if it already looks like ICAO (Kxxx/Pxxx etc)
                if not icao:
                    icao = loc if (loc and len(loc) == 4) else ""

                if not icao:
                    continue

                unicom = norm_freq(sl(line, UNICOM_START, UNICOM_LEN))
                ctaf   = norm_freq(sl(line, CTAF_START, CTAF_LEN))

                if unicom:
                    key = (icao, "UNICOM", unicom)
                    if key not in seen:
                        seen.add(key)
                        out.append(key)

                if ctaf:
                    key = (icao, "CTAF", ctaf)
                    if key not in seen:
                        seen.add(key)
                        out.append(key)

        out.sort()
        with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f2:
            w = csv.writer(f2)
            w.writerow(["ICAO","TYPE","VALUE"])
            w.writerows(out)

        print(f"Wrote {OUTPUT_FILE} rows: {len(out)}")

if __name__ == "__main__":
    main()
