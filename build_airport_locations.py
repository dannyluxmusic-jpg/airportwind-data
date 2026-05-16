import csv
import io
import re
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"
OUTPUT_FILE = "airport_locations.csv"

coord_pattern = re.compile(
    r"\d{2,3}-\d{2}-\d{2}\.\d+[NS]|\d{3}-\d{2}-\d{2}\.\d+[EW]"
)

apt_ident_pattern = re.compile(r"\bAIRPORT\s+([A-Z0-9]{2,4})\b")


def dms_to_decimal(value):
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

rows = []
skipped = 0

for line in lines:
    if not line.startswith("APT"):
        continue

    match = apt_ident_pattern.search(line)
    if not match:
        skipped += 1
        continue

    airport = match.group(1).strip().upper()

    if len(airport) == 4 and airport.startswith("K"):
        airport = airport[1:]

    coords = coord_pattern.findall(line)

    if len(coords) < 2:
        skipped += 1
        continue

    lat = dms_to_decimal(coords[0])
    lon = dms_to_decimal(coords[1])

    if lat is None or lon is None:
        skipped += 1
        continue

    rows.append({
        "airport": airport,
        "lat": f"{lat:.8f}",
        "lon": f"{lon:.8f}",
    })

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "airport",
            "lat",
            "lon",
        ]
    )

    writer.writeheader()
    writer.writerows(rows)

print("WROTE:", OUTPUT_FILE)
print("AIRPORTS:", len(rows))
print("SKIPPED:", skipped)

print("\nCHECK ECP/KJWN:")

for row in rows:
    if row["airport"] in ["ECP", "JWN", "BNA"]:
        print(row)

print("\nDONE")
