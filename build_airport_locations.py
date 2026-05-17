import csv
import requests
import zipfile
import io
import re

INDEX_URL = "https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Fetching FAA NASR page...")

html = requests.get(
    INDEX_URL,
    headers=headers,
    timeout=300
).text

match = re.search(
    r'https://[^"]+?\.zip',
    html,
    re.IGNORECASE
)

if not match:
    raise RuntimeError("Could not locate NASR ZIP URL")

NASR_URL = match.group(0)

print("FOUND ZIP:", NASR_URL)

r = requests.get(
    NASR_URL,
    headers=headers,
    timeout=300,
    allow_redirects=True
)

r.raise_for_status()

z = zipfile.ZipFile(io.BytesIO(r.content))
