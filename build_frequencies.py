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
