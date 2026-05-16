import io
import zipfile
import requests

# FAA always redirects this page to current cycle
INDEX_URL = "https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/"

print("Fetching FAA page...")

html = requests.get(INDEX_URL, timeout=120).text

zip_url = None

for token in html.split('"'):
    if "28DaySubscription_Effective_" in token and token.endswith(".zip"):
        if token.startswith("http"):
            zip_url = token
        else:
            zip_url = "https://nfdc.faa.gov" + token
        break

print("ZIP URL:", zip_url)

if not zip_url:
    raise RuntimeError("Could not find FAA NASR ZIP")

print("Downloading NASR ZIP...")

response = requests.get(zip_url, timeout=120)
response.raise_for_status()

print("Opening ZIP...")

zf = zipfile.ZipFile(io.BytesIO(response.content))

print("ZIP CONTENTS:")

for name in zf.namelist():
    print(name)

print("DONE")
