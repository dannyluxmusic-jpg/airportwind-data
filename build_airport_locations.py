import csv
import requests
import zipfile
import io
import re

INDEX_URL = "https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Fetching FAA NASR page...")

html = requests.get(
    INDEX_URL,
    headers=headers,
    timeout=300
).text

match = re.search(
    r'https://[^"]+?\.zip',
    html,
    re.IGNORECASE
)

if not match:
    raise RuntimeError("Could not locate NASR ZIP URL")

NASR_URL = match.group(0)

print("FOUND ZIP:", NASR_URL)

r = requests.get(
    NASR_URL,
    headers=headers,
    timeout=300,
    allow_redirects=True
)

r.raise_for_status()

z = zipfile.ZipFile(io.BytesIO(r.content))

apt_name = None

for name in z.namelist():

    if name.upper().endswith("APT.TXT"):
        apt_name = name
        break

if not apt_name:
    raise RuntimeError("APT.txt not found")

print("Opening", apt_name)

with z.open(apt_name) as f:
    raw = f.read().decode("latin1", errors="ignore")

lines = raw.splitlines()

out_rows = []
seen = set()

def dms_to_decimal(value, hemisphere):

    value = value.strip()

    if hemisphere in ["N", "S"]:

        degrees = int(value[0:2])
        minutes = int(value[2:4])
        seconds = float(value[4:])

    else:

        degrees = int(value[0:3])
        minutes = int(value[3:5])
        seconds = float(value[5:])

    decimal = (
        degrees +
        (minutes / 60.0) +
        (seconds / 3600.0)
    )

    if hemisphere in ["S", "W"]:
        decimal *= -1

    return decimal

apt_records = 0

for line in lines:

    if not line.startswith("APT"):
        continue

    apt_records += 1

    try:

        ident = line[27:31].strip().upper()

        if not ident:
            continue

        lat_raw = line[538:550]
        lat_hemi = line[550:551]

        lon_raw = line[565:578]
        lon_hemi = line[578:579]

        if not lat_raw.strip():
            continue

        if not lon_raw.strip():
            continue

        lat = dms_to_decimal(
            lat_raw,
            lat_hemi
        )

        lon = dms_to_decimal(
            lon_raw,
            lon_hemi
        )

        if ident in seen:
            continue

        seen.add(ident)

        out_rows.append([
            ident,
            lat,
            lon
        ])

    except:
        continue

with open("airport_locations.csv", "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "airport",
        "lat",
        "lon"
    ])

    writer.writerows(out_rows)

print("")
print("APT RECORDS:", apt_records)
print("AIRPORTS:", len(out_rows))
print("")
print("CHECK ECP/JWN/BNA:")
print("")

found = False

for row in out_rows:

    if row[0] in ["ECP", "JWN", "BNA"]:

        found = True

        print({
            "airport": row[0],
            "lat": row[1],
            "lon": row[2]
        })

if not found:

    print("NO TEST AIRPORTS FOUND")

print("")
print("DONE")
