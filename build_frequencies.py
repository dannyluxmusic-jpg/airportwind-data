import csv
import requests

OUTPUT_FILE = "airport_frequencies.csv"

BASE_URL = "https://services6.arcgis.com/ssFJjBXIUyZDrSYZ/arcgis/rest/services/Frequencies/FeatureServer/0/query"

params = {
    "where": "1=1",
    "outFields": "*",
    "f": "json",
    "resultRecordCount": 2000
}

def fetch_all():
    all_rows = []
    offset = 0

    while True:
        params["resultOffset"] = offset
        r = requests.get(BASE_URL, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()

        features = data.get("features", [])
        if not features:
            break

        all_rows.extend(features)
        offset += len(features)

    return all_rows

def normalize(freq):
    return "".join(c for c in str(freq) if c.isdigit() or c == ".")

def main():
    print("Fetching FAA frequencies...")
    features = fetch_all()

    seen = set()
    rows = []

    for feat in features:
        attr = feat["attributes"]

        icao = attr.get("IDENT")
        freq = normalize(attr.get("FREQ_TRANS") or attr.get("FREQ_REC"))
        type_code = attr.get("TYPE_CODE")

        if not icao or not freq or not type_code:
            continue

        key = (icao, type_code, freq)
        if key in seen:
            continue

        seen.add(key)
        rows.append(key)

    print("Rows:", len(rows))

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ICAO","TYPE","VALUE"])
        w.writerows(rows)

    print("Wrote airport_frequencies.csv")

if __name__ == "__main__":
    main()
import os
import csv
import zipfile
import requests
import io

OUTPUT_FILE = "airport_frequencies.csv"

NASR_URL = "https://aeronav.faa.gov/Upload_313-d/28DaySubscription_Effective.zip"

def download_nasr():
    print("Downloading NASR...")
    r = requests.get(NASR_URL, timeout=120)
    r.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(r.content))

def find_apt_com(zip_file):
    for name in zip_file.namelist():
        if "APT_COM.txt" in name.upper():
            print("Found:", name)
            return name
    raise Exception("APT_COM.txt not found in NASR zip")

def parse_apt_com(zip_file, file_name):
    rows = []
    seen = set()

    with zip_file.open(file_name) as f:
        for line in f:
            try:
                line = line.decode("latin-1")
            except:
                continue

            if not line.startswith("APT"):
                continue

            icao = line[27:31].strip()
            freq = line[53:60].strip()
            type_code = line[121:140].strip()

            if not icao or not freq:
                continue

            freq = "".join(c for c in freq if c.isdigit() or c == ".")

            key = (icao, type_code, freq)
            if key in seen:
                continue

            seen.add(key)
            rows.append(key)

    return rows

def write_csv(rows):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ICAO", "TYPE", "VALUE"])
        writer.writerows(rows)

def main():
    zip_file = download_nasr()
    apt_com_file = find_apt_com(zip_file)
    rows = parse_apt_com(zip_file, apt_com_file)
    print("Parsed rows:", len(rows))
    write_csv(rows)
    print("Wrote airport_frequencies.csv")

if __name__ == "__main__":
    main()
