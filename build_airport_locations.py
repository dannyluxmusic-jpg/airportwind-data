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

    upper = name.upper()

    if upper.endswith("APT.TXT"):
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

airport_count = 0

for line in lines:

    if not line.startswith("APT"):
        continue

    airport_count += 1

    try:

        matches = re.findall(
            r'[-]?\d+\.\d+',
            line
        )

        if len(matches) < 2:
            continue

        lat = None
        lon = None

        for value in matches:

            v = float(value)

            if lat is None and abs(v) <= 90:
                lat = v
                continue

            if lat is not None and abs(v) <= 180:
                lon = v
                break

        if lat is None or lon is None:
            continue

        ident_match = re.search(
            r'\b[A-Z0-9]{3,4}\b',
            line
        )

        if not ident_match:
            continue

        ident = ident_match.group(0).upper()

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

print("APT RECORDS:", airport_count)
print("WROTE:", len(out_rows))

print("\nCHECK ECP/JWN/BNA:\n")

for row in out_rows:

    if row[0] in ["ECP", "JWN", "BNA"]:

        print({
            "airport": row[0],
            "lat": row[1],
            "lon": row[2]
        })

print("\nDONE")
