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

    if upper.endswith("APT_BASE.csv"):
        apt_name = name
        break

    if upper.endswith("APT.txt"):
        apt_name = name

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

if apt_name.upper().endswith("APT.TXT"):

    for line in lines:

        if not line.startswith("APT"):
            continue

        try:
            ident = line[27:31].strip().upper()

            lat = line[538:550].strip()
            lon = line[565:578].strip()

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
# CSV FORMAT
# ------------------------------------------------------------------

else:

    reader = csv.DictReader(lines)

    possible_ident = [
        "ARPT_ID",
        "ARPT IDENTIFIER",
        "IDENT",
        "LOCATION_ID",
    ]

    possible_lat = [
        "LAT_DECIMAL",
        "LATITUDE",
        "ARP_LATITUDE",
    ]

    possible_lon = [
        "LONG_DECIMAL",
        "LONGITUDE",
        "ARP_LONGITUDE",
    ]

    def pick(cols):
        for c in cols:
            if c in reader.fieldnames:
                return c
        return None

    ident_col = pick(possible_ident)
    lat_col = pick(possible_lat)
    lon_col = pick(possible_lon)

    if not ident_col or not lat_col or not lon_col:
        raise RuntimeError("Could not locate FAA CSV columns")

    for row in reader:

        try:
            ident = row[ident_col].strip().upper()

            lat = float(row[lat_col])
            lon = float(row[lon_col])

            if not ident:
                continue

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
