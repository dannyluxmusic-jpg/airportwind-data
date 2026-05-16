import io
import re
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"

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

pattern = r"\d{2,3}-\d{2}-\d{2}\.\d+[NS]|\d{3}-\d{2}-\d{2}\.\d+[EW]"

valid_count = 0
skipped_count = 0

for line in lines:

    if not line.startswith("RWY"):
        continue

    coords = re.findall(pattern, line)

    if len(coords) < 4:
        skipped_count += 1
        continue

    lat1, lon1, lat2, lon2 = coords[:4]

    print("\n===================")
    print("RAW:", line[:140])

    print("LAT1:", lat1)
    print("LON1:", lon1)

    print("LAT2:", lat2)
    print("LON2:", lon2)

    valid_count += 1

    if valid_count >= 10:
        break

print("\n===================")
print("VALID:", valid_count)
print("SKIPPED:", skipped_count)

print("\nDONE")
