import csv
import requests
import zipfile
import io

NASR_URL = "https://aeronav.faa.gov/Upload_313-d/special/28DaySubscription_Effective_2026-05-15.zip"

print("Downloading NASR ZIP...")
r = requests.get(NASR_URL, timeout=300)
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

for line in lines:

    print("RAW LINE:", repr(line[:120]))
    break
