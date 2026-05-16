import re

valid_count = 0
skipped_count = 0

def extract_coords(raw_line):
    """
    Extract FAA runway endpoint coordinates from malformed NASR rows.
    Returns:
        [lat1, lon1, lat2, lon2]
    or []
    """

    # FAA coords look like:
    # 61-12-56.4587Nimport io
import re
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"

coord_pattern = re.compile(
    r"\d{2,3}-\d{2}-\d{2}\.\d+[NS]|\d{3}-\d{2}-\d{2}\.\d+[EW]"
)

valid_count = 0
skipped_count = 0

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

    for line in lines:

        if not line.startswith("RWY"):
            continue

        coords = coord_pattern.findall(line)

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
print(f"Valid runway geometries: {valid_count}")
print(f"Skipped malformed rows: {skipped_count}")

print("\nDONE")
    # 149-51-09.0466W

    pattern = r'\d{2,3}-\d{2}-\d{2}\.\d+[NS]|\d{3}-\d{2}-\d{2}\.\d+[EW]'

    matches = re.findall(pattern, raw_line)

    if len(matches) >= 4:
        return matches[:4]

    return []


with open("APT_RWY.txt", "r", encoding="latin-1") as f:
    for line in f:

        if not line.startswith("RWY"):
            continue

        coords = extract_coords(line)

        print("\n===================")
        print("RAW:", line.strip())
        print("COORDS:", coords)

        if len(coords) < 4:
            skipped_count += 1
            continue

        lat1, lon1, lat2, lon2 = coords

        # ---------------------------------
        # YOUR EXISTING GEOMETRY CODE HERE
        # ---------------------------------

        valid_count += 1


print("\n===================")
print(f"Valid runway geometries: {valid_count}")
print(f"Skipped malformed rows: {skipped_count}")
