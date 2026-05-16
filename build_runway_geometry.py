
import csv
import io
import zipfile
import requests

NASR_URL = "https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/current/NASR_Subscription.zip"

print("Downloading NASR...")

response = requests.get(NASR_URL, timeout=120)
response.raise_for_status()

print("Opening ZIP...")

zf = zipfile.ZipFile(io.BytesIO(response.content))

csv_name = None

for name in zf.namelist():
    upper = name.upper()

    if "APT_RWY" in upper and upper.endswith(".CSV"):
        csv_name = name
        break

print("FOUND:", csv_name)

if not csv_name:
    raise RuntimeError("APT_RWY.csv not found")

with zf.open(csv_name) as f:
    text = io.TextIOWrapper(f, encoding="latin-1")

    reader = csv.reader(text)

    matches = 0

    for row in reader:
        joined = ",".join(row)

        if "KECP" in joined:
            print(joined)
            matches += 1

            if matches >= 5:
                break

print("DONE")
