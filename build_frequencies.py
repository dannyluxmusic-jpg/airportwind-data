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

def find_column(header, options):
    for opt in options:
        if opt in header:
            return opt
    return None

def main():
    rows = []
    seen = set()

    # -------------------------
    # UNZIP NASR
    # -------------------------
    with zipfile.ZipFile(NASR_ZIP) as z:
        z.extractall("nasr")

    # -------------------------
    # FIND CSV ZIP
    # -------------------------
    csv_zip = None
    for p in Path("nasr").rglob("*.zip"):
        if "CSV" in p.name.upper():
            csv_zip = p
            break

    if not csv_zip:
        print("NO CSV ZIP FOUND")
        return

    # -------------------------
    # UNZIP CSV DATA
    # -------------------------
    with zipfile.ZipFile(csv_zip) as z:
        z.extractall("csv")

    # -------------------------
    # COM.csv (FREQUENCIES)
    # -------------------------
    com_path = next(Path("csv").rglob("COM.csv"), None)

    if com_path:
        print("Using COM:", com_path)

        with open(com_path, newline='', encoding='latin-1') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames

            print("COM HEADER:", header)

            icao_col = find_column(header, ["ARPT_ID", "APT_ID", "SITE_NO"])
            freq_col = find_column(header, ["FREQ", "FREQUENCY"])
            type_col = find_column(header, ["COMM_TYPE", "TYPE", "COMM_NAME"])

            for r in reader:
                icao = (r.get(icao_col) or "").strip()
                freq = (r.get(freq_col) or "").strip()
                desc = (r.get(type_col) or "").lower()

                if not icao or not freq:
                    continue

                if "ground" in desc:
                    typ = "ground"
                elif "tower" in desc:
                    typ = "tower"
                elif "approach" in desc:
                    typ = "approach"
                elif "departure" in desc:
                    typ = "departure"
                elif "clearance" in desc:
                    typ = "clearance"
                else:
                    continue

                add(rows, seen, icao, typ, freq)

    # -------------------------
    # AWOS.csv (PHONES)
    # -------------------------
    awos_path = next(Path("csv").rglob("AWOS.csv"), None)

    if awos_path:
        print("Using AWOS:", awos_path)

        with open(awos_path, newline='', encoding='latin-1') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames

            print("AWOS HEADER:", header)

            icao_col = find_column(header, ["ARPT_ID", "APT_ID", "SITE_NO"])
            phone_col = find_column(header, ["PHONE_NO", "PHONE", "TEL"])

            for r in reader:
                icao = (r.get(icao_col) or "").strip()
                phone = (r.get(phone_col) or "").strip()

                if not icao or not phone:
                    continue

                if "-" not in phone:
                    continue

                add(rows, seen, icao, "awos_phone", phone)

    # -------------------------
    # WRITE OUTPUT
    # -------------------------
    with open(OUT, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for r in sorted(rows):
            f.write(f"{r[0]},{r[1]},{r[2]}\n")

    print("TOTAL ROWS:", len(rows))


if __name__ == "__main__":
    main()
