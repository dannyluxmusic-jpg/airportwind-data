import io
import re
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"

coord_pattern = re.compile(r"\d{2,3}-\d{2}-\d{2}\.\d{4}[NSEW]")

response = requests.get(
    NASR_URL,
    timeout=120,
    headers={"User-Agent": "Mozilla/5.0"}
)
response.raise_for_status()

zf = zipfile.ZipFile(io.BytesIO(response.content))

with zf.open("APT.txt") as f:
    lines = f.read().decode("latin-1", errors="ignore").splitlines()

count = 0

for line in lines:
    if not line.startswith("RWY"):
        continue

    if "16/34" not in line:
        continue

    coords = coord_pattern.findall(line)

    print("\n===================")
    print("RAW:", line[:120])
    print("COORDS:", coords)
    print(f"Valid runway geometries: {valid_count}")
    print(f"Skipped malformed rows: {skipped_count}")

    count += 1
    if count >= 10:
        break

print("\nDONE")
