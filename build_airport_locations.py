import csv
import requests
import zipfile
import io

NASR_URL = "https://aeronav.faa.gov/aero_data/NASR_Subscription.zip"

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Downloading NASR ZIP...")

r = requests.get(
    NASR_URL,
    headers=headers,
    timeout=300,
    allow_redirects=True
)

r.raise_for_status()

z = zipfile.ZipFile(io.BytesIO(r.content))

print("FILES FOUND:")

for name in z.namelist()[:20]:
    print(name)

apt_name = None

for name in z.namelist():

    upper = name.upper()

    if upper.endswith("APT.TXT"):
        apt_name = name
        break

if not apt_name:
    raise RuntimeError("APT file not found")

print("Opening", apt_name)

with z.open(apt_name) as f:
    raw = f.read().decode("latin1", errors="ignore")

lines = raw.splitlines()

print("TOTAL LINES:", len(lines))

for line in lines[:5]:
    print("RAW:", repr(line[:120]))

print("DONE")
