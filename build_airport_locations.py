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
    r'https://nfdc\.faa\.gov/webContent/28DaySub/[^"]+?\.zip',
    html,
    re.IGNORECASE
)

if not match:
    raise RuntimeError("Could not locate NASR ZIP")

NASR_URL = match.group(0)

print("FOUND ZIP:", NASR_URL)

r = requests.get(
    NASR_URL,
    headers=headers,
    timeout=300
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

def dms_to_decimal(deg, mins, secs, hemi):

    value = (
        float(deg)
        + float(mins) / 60.0
        + float(secs) / 3600.0
    )

    if hemi in ["S", "W"]:
        value *= -1

    return value

apt_count = 0

for line in lines:

    if not line.startswith("APT"):
        continue

    apt_count += 1

    try:

        ident = line[27:31].strip().upper()

        if not ident:
            continue

        lat_match = re.search(
            r'(\d{2})-(\d{2})-(\d{2}\.\d+)([NS])',
            line
        )

        lon_match = re.search(
            r'(\d{3})-(\d{2})-(\d{2}\.\d+)([EW])',
            line
        )

        if not lat_match or not lon_match:
            continue

        lat = dms_to_decimal(
            lat_match.group(1),
            lat_match.group(2),
            lat_match.group(3),
            lat_match.group(4)
        )

        lon = dms_to_decimal(
            lon_match.group(1),
            lon_match.group(2),
            lon_match.group(3),
            lon_match.group(4)
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
print("APT RECORDS:", apt_count)
print("AIRPORTS:", len(out_rows))
print("")

print("CHECK ECP/JWN/BNA:")
print("")

for row in out_rows:

    if row[0] in ["ECP", "JWN", "BNA"]:

        print({
            "airport": row[0],
            "lat": row[1],
            "lon": row[2]
        })

print("")
print("DONE")
