import csv
import io
import re
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"
OUTPUT_FILE = "runway_geometry.csv"

coord_pattern = re.compile(
    r"\d{2,3}-\d{2}-\d{2}\.\d+[NS]|\d{3}-\d{2}-\d{2}\.\d+[EW]"
)

icao_pattern = re.compile(r"\bK[A-Z0-9]{3}\b")


def dms_to_decimal(value):
    # Examples:
    # 30-21-40.2600N
    # 085-47-44.1680W
    match = re.match(r"^(\d{2,3})-(\d{2})-(\d{2}\.\d+)([NSEW])$", value)

    if not match:
        return None

    degrees = float(match.group(1))
    minutes = float(match.group(2))
    seconds = float(match.group(3))
    direction = match.group(4)

    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

    if direction in ["S", "W"]:
        decimal *= -1

    return decimal


def runway_pair_from_line(line):
    # Example near front of FAA RWY line:
    # RWY03430.3*A FL16/34 ...
    match = re.search(r"\b[A-Z]{2}([0-9A-Z]{1,3}/[0-9A-Z]{1,3})\b", line[:80])

    if not match:
        return None

    pair = match.group(1)
    parts = pair.split("/")

    if len(parts) != 2:
        return None

    return parts[0].strip(), parts[1].strip()


print("Downloading NASR ZIP...")

response = requests.get(
    NASR_URL,
    timeout=120,
    headers={"User-Agent": "Mozilla/5.0"}
)

response.raise_for_status()

zf = zipfile.ZipFile(io.BytesIO(response.content))

print("Opening APT.txt...")

with zf.open("APT.txt") as f:
    lines = f.read().decode("latin-1", errors="ignore").splitlines()


# Build FAA site-number -> airport ident map.
# RWY records use site numbers like 03430.3.
# APT records contain the airport identifier like KECP.
site_to_ident = {}

for line in lines:
    if not line.startswith("APT"):
        continue

    site_number = line[3:10].strip()

    match = icao_pattern.search(line)

    if not match:
        continue

    icao = match.group(0)

    # Store as FAA-style 3-letter for U.S. airports:
    # KECP -> ECP
    faa_id = icao[1:] if icao.startswith("K") else icao

    site_to_ident[site_number] = faa_id


print("Mapped airports:", len(site_to_ident))

rows = []
valid_count = 0
skipped_count = 0

for line in lines:
    if not line.startswith("RWY"):
        continue

    site_number = line[3:10].strip()
    airport_id = site_to_ident.get(site_number)

    if not airport_id:
        skipped_count += 1
        continue

    runway_pair = runway_pair_from_line(line)

    if not runway_pair:
        skipped_count += 1
        continue

    rwy_a, rwy_b = runway_pair

    coords = coord_pattern.findall(line)

    if len(coords) < 4:
        skipped_count += 1
        continue

    lat1_raw, lon1_raw, lat2_raw, lon2_raw = coords[:4]

    lat1 = dms_to_decimal(lat1_raw)
    lon1 = dms_to_decimal(lon1_raw)
    lat2 = dms_to_decimal(lat2_raw)
    lon2 = dms_to_decimal(lon2_raw)

    if None in [lat1, lon1, lat2, lon2]:
        skipped_count += 1
        continue

    rows.append({
        "airport": airport_id,
        "runway": rwy_a,
        "lat": f"{lat1:.8f}",
        "lon": f"{lon1:.8f}",
        "reciprocal": rwy_b,
        "reciprocal_lat": f"{lat2:.8f}",
        "reciprocal_lon": f"{lon2:.8f}",
    })

    rows.append({
        "airport": airport_id,
        "runway": rwy_b,
        "lat": f"{lat2:.8f}",
        "lon": f"{lon2:.8f}",
        "reciprocal": rwy_a,
        "reciprocal_lat": f"{lat1:.8f}",
        "reciprocal_lon": f"{lon1:.8f}",
    })

    valid_count += 1


with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "airport",
            "runway",
            "lat",
            "lon",
            "reciprocal",
            "reciprocal_lat",
            "reciprocal_lon",
        ]
    )

    writer.writeheader()
    writer.writerows(rows)


print("WROTE:", OUTPUT_FILE)
print("VALID RUNWAY PAIRS:", valid_count)
print("OUTPUT ROWS:", len(rows))
print("SKIPPED:", skipped_count)

print("\nKECP/ECP CHECK:")

for row in rows:
    if row["airport"] == "ECP":
        print(row)

print("\nDONE")
