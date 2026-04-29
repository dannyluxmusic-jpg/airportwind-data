#!/usr/bin/env python3

import zipfile
from pathlib import Path
import datetime
import csv

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
OUT = HERE / "airport_frequencies.csv"

def add(rows, seen, icao, typ, val):
    key = (icao, typ, val)
    if key in seen:
        return
    seen.add(key)
    rows.append(key)

def main():
    rows = []
    seen = set()

    # unzip NASR
    with zipfile.ZipFile(NASR_ZIP) as z:
        z.extractall("nasr")

    # find inner CSV zip
    csv_zip = None
    for p in Path("nasr").rglob("*.zip"):
        if "CSV" in p.name.upper():
            csv_zip = p
            break

    if not csv_zip:
        print("NO CSV ZIP FOUND")
        return

    # unzip inner CSV zip
    with zipfile.ZipFile(csv_zip) as z:
        z.extractall("csv")

    # -----------------------
    # LOAD COM.csv (frequencies)
    # -----------------------
    com_path = next(Path("csv").rglob("COM.csv"), None)

    if com_path:
        with open(com_path) as f:
            reader = csv.DictReader(f)
            for r in reader:
                icao = r.get("ARPT_ID", "").strip()
                freq = r.get("FREQ", "").strip()
                typ = r.get("COMM_TYPE", "").lower()

                if not icao or not freq:
                    continue

                if "ground" in typ:
                    t = "ground"
                elif "tower" in typ:
                    t = "tower"
                elif "approach" in typ:
                    t = "approach"
                elif "departure" in typ:
                    t = "departure"
                elif "clearance" in typ:
                    t = "clearance"
                else:
                    continue

                add(rows, seen, icao, t, freq)

    # -----------------------
    # LOAD AWOS.csv (phones)
    # -----------------------
    awos_path = next(Path("csv").rglob("AWOS.csv"), None)

    if awos_path:
        with open(awos_path) as f:
            reader = csv.DictReader(f)
            for r in reader:
                icao = r.get("ARPT_ID", "").strip()
                phone = r.get("PHONE", "").strip()

                if not icao or not phone:
                    continue

                add(rows, seen, icao, "awos_phone", phone)

    # -----------------------
    # WRITE OUTPUT
    # -----------------------
    with open(OUT, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for r in sorted(rows):
            f.write(f"{r[0]},{r[1]},{r[2]}\n")

    print("ROWS:", len(rows))

if __name__ == "__main__":
    main()
