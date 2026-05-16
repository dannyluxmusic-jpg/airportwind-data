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

    print("RAW LINE:")
    print(repr(line))

    print("LINE LENGTH:", len(line))

    airport_id = line[3:10].strip()
    runway_id = line[13:20].strip()

    end1_lat = line[83:97].strip()
    end1_lon = line[98:113].strip()

    end2_lat = line[286:300].strip()
    end2_lon = line[301:316].strip()

    print("\nPARSED FIELDS")

    print("AIRPORT:", airport_id)
    print("RUNWAY:", runway_id)

    print("END1 LAT:", end1_lat)
    print("END1 LON:", end1_lon)

    print("END2 LAT:", end2_lat)
    print("END2 LON:", end2_lon)

    print("\nRAW SLICES")

    print("AIRPORT RAW :", repr(line[3:10]))
    print("RUNWAY RAW  :", repr(line[13:20]))

    print("END1 LAT RAW:", repr(line[83:97]))
    print("END1 LON RAW:", repr(line[98:113]))

    print("END2 LAT RAW:", repr(line[286:300]))
    print("END2 LON RAW:", repr(line[301:316]))

    print("===================")

    count += 1

    if count >= 5:
        break

print("\nDONE")
