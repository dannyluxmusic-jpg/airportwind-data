import csv
import requests
import zipfile
import io

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"

print("Downloading NASR ZIP...")
r = requests.get(NASR_URL, timeout=300)
r.raise_for_status()

z = zipfile.ZipFile(io.BytesIO(r.content))

apt_name = None

for name in z.namelist():

    upper = name.upper()

    if upper.endswith("APT.TXT"):
        apt_name = name
        break

print("FILES FOUND:")

for n in z.namelist()[:20]:
    print(n)

if not apt_name:
    raise RuntimeError("APT file not found")

print("Opening", apt_name)

with z.open(apt_name) as f:
    raw = f.read().decode("latin1", errors="ignore")

lines = raw.splitlines()

out_rows = []
seen = set()

# ------------------------------------------------------------------
# FAA FIXED WIDTH APT.txt FORMAT
# ------------------------------------------------------------------

for line in lines:

    try:

        print(line[:20])
break

        ident = line[1210:1217].strip().upper()

        lat = line[523:535].strip()
        lon = line[550:564].strip()

        if not ident:
            continue

        lat = float(lat)
        lon = float(lon)

        if abs(lat) > 90:
            lat = lat / 3600.0

        if abs(lon) > 180:
            lon = lon / 3600.0

        if abs(lat) > 90 or abs(lon) > 180:
            continue

        if ident in seen:
            continue

        seen.add(ident)

        out_rows.append([ident, lat, lon])

    except:
        continue

# ------------------------------------------------------------------
# WRITE CSV
# ------------------------------------------------------------------

with open("airport_locations.csv", "w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow(["airport", "lat", "lon"])

    writer.writerows(out_rows)

print("WROTE: airport_locations.csv")
print("AIRPORTS:", len(out_rows))

print("\nCHECK ECP/KJWN:\n")

for row in out_rows:
    if row[0] in ["ECP", "JWN", "BNA"]:
        print({
            "airport": row[0],
            "lat": row[1],
            "lon": row[2]
        })

print("\nDONE")
