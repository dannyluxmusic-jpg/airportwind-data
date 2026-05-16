import io
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"

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

    print("\n===================")

    print("AIRPORT:", line[3:10].strip())

    print("RUNWAY:", line[13:20].strip())

    print("END1 LAT:", line[83:97].strip())
    print("END1 LON:", line[98:113].strip())

    print("END2 LAT:", line[286:300].strip())
    print("END2 LON:", line[301:316].strip())

    count += 1

    if count >= 5:
        break

print("\nDONE")
