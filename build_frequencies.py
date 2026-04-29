#!/usr/bin/env python3

import csv
import datetime
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
OUT = HERE / "airport_frequencies.csv"

def clean(s):
    return (s or "").strip().strip('"').strip()

def norm_header(s):
    return re.sub(r"[^A-Z0-9]", "", clean(s).upper())

def site_keys(s):
    s = clean(s).upper()
    if not s:
        return []
    keys = {s, s.rstrip(".")}
    m = re.match(r"^(\d{5})(?:\.\d+)?", s.rstrip("."))
    if m:
        keys.add(m.group(1))
    return list(keys)

def norm_airport_id(s):
    s = clean(s).upper()
    if not s:
        return ""
    if len(s) == 4:
        return s
    if len(s) == 3:
        return "K" + s
    return s

def norm_freq(s):
    s = clean(s)
    try:
        v = float(s)
    except:
        return None
    if 118.000 <= v <= 136.975:
        return f"{v:.3f}"
    return None

def add(rows, seen, icao, typ, val):
    icao = clean(icao).upper()
    typ = clean(typ).lower()
    val = clean(val)

    if not icao or not typ or not val:
        return

    key = (icao, typ, val)
    if key in seen:
        return

    seen.add(key)
    rows.append(key)

def find_file(root, name):
    return next(Path(root).rglob(name), None)

def row_get(row, header_map, names):
    for name in names:
        key = norm_header(name)
        if key in header_map:
            return clean(row.get(header_map[key], ""))
    return ""

def classify_comm(text):
    u = text.upper()

    if "ATIS" in u:
        return "atis"
    if "AWOS" in u:
        return "awos"
    if "ASOS" in u:
        return "asos"
    if "UNICOM" in u:
        return "unicom"
    if "CTAF" in u:
        return "ctaf"
    if "GROUND" in u or "GND" in u:
        return "ground"
    if "CLEARANCE" in u or "CLNC" in u or "DELIVERY" in u:
        return "clearance"
    if "TOWER" in u or "TWR" in u:
        return "tower"
    if "APPROACH" in u or "APCH" in u or "APP" in u:
        return "approach"
    if "DEPARTURE" in u or "DEP" in u:
        return "departure"
    if "CENTER" in u or "CTR" in u:
        return "center"

    return ""

def main():
    rows = []
    seen = set()

    with zipfile.ZipFile(NASR_ZIP) as z:
        z.extractall("nasr")

    csv_zip = None
    for p in Path("nasr").rglob("*.zip"):
        if "CSV" in p.name.upper():
            csv_zip = p
            break

    if not csv_zip:
        print("NO CSV ZIP FOUND")
        return

    with zipfile.ZipFile(csv_zip) as z:
        z.extractall("csv")

    apt_path = find_file("csv", "APT.csv")
    com_path = find_file("csv", "COM.csv")
    awos_path = find_file("csv", "AWOS.csv")

    site_to_airport = {}

    # -------------------------
    # APT.csv → SITE_NO to airport ID map
    # -------------------------
    if apt_path:
        print("Using APT:", apt_path)

        with open(apt_path, newline="", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            header_map = {norm_header(h): h for h in reader.fieldnames or []}
            print("APT HEADER:", reader.fieldnames)

            for row in reader:
                site = row_get(row, header_map, [
                    "SITE_NO", "ARPT_SITE_NO", "AIRPORT_SITE_NO", "LANDING_FACILITY_SITE_NO"
                ])

                ident = row_get(row, header_map, [
                    "ICAO_ID", "ICAO", "ARPT_ID", "LOC_ID", "FAA_ID", "LID"
                ])

                ident = norm_airport_id(ident)

                if site and ident:
                    for k in site_keys(site):
                        site_to_airport[k] = ident

                # CTAF/UNICOM if present in APT.csv
                for h in reader.fieldnames or []:
                    hu = h.upper()
                    val = norm_freq(row.get(h, ""))

                    if not val:
                        continue

                    if "CTAF" in hu:
                        add(rows, seen, ident, "ctaf", val)
                    elif "UNICOM" in hu:
                        add(rows, seen, ident, "unicom", val)

        # -------------------------
    # COM.csv → radio frequencies (FIXED)
    # -------------------------
    if com_path:
        print("Using COM:", com_path)

        with open(com_path, newline="", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            header_map = {norm_header(h): h for h in reader.fieldnames or []}
            print("COM HEADER:", reader.fieldnames)

            for row in reader:

                # ✅ DIRECT airport ID (not SITE_NO)
                icao = row_get(row, header_map, [
                    "ARPT_ID", "ICAO_ID", "LOC_ID", "FAA_ID", "LID"
                ])
                icao = norm_airport_id(icao)

                if not icao:
                    continue

                # ✅ frequency
                freq = row_get(row, header_map, [
                    "FREQ", "FREQUENCY", "COMM_FREQ"
                ])
                freq = norm_freq(freq)

                if not freq:
                    continue

                # ✅ description → type
                desc = " ".join(clean(v) for v in row.values())
                typ = classify_comm(desc)

                if not typ:
                    continue

                add(rows, seen, icao, typ, freq)

    # -------------------------
    # AWOS.csv → AWOS/ASOS phone numbers
    # -------------------------
    if awos_path:
        print("Using AWOS:", awos_path)

        with open(awos_path, newline="", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            header_map = {norm_header(h): h for h in reader.fieldnames or []}
            print("AWOS HEADER:", reader.fieldnames)

            for row in reader:
                site = row_get(row, header_map, [
                    "SITE_NO", "ARPT_SITE_NO", "AIRPORT_SITE_NO", "LANDING_FACILITY_SITE_NO"
                ])

                icao = ""
                for k in site_keys(site):
                    if k in site_to_airport:
                        icao = site_to_airport[k]
                        break

                if not icao:
                    ident = row_get(row, header_map, [
                        "ASOS_AWOS_ID", "AWOS_ID", "ARPT_ID", "LOC_ID", "FAA_ID", "LID"
                    ])
                    icao = norm_airport_id(ident)

                if not icao:
                    continue

                kind_text = " ".join(clean(v) for v in row.values()).upper()

                if "ASOS" in kind_text:
                    typ = "asos_phone"
                elif "AWOS" in kind_text:
                    typ = "awos_phone"
                else:
                    continue

                phone_cols = [
                    "PHONE_NO", "SECOND_PHONE_NO", "PHONE", "PHONE_NUMBER",
                    "TEL", "TELEPHONE"
                ]

                phones = []
                for col in phone_cols:
                    val = row_get(row, header_map, [col])
                    if val:
                        phones.append(val)

                for phone in phones:
                    if re.search(r"\d{3}[-)\s.]?\d{3}[-.\s]?\d{4}", phone):
                        add(rows, seen, icao, typ, phone)

    with open(OUT, "w") as f:
        f.write(f"# updated {datetime.datetime.utcnow()}\n")
        f.write("icao,type,value\n")

        for icao, typ, val in sorted(rows):
            f.write(f"{icao},{typ},{val}\n")

    print("TOTAL ROWS:", len(rows))

if __name__ == "__main__":
    main()
