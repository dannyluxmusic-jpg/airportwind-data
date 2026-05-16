import io
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/28DaySubscription_Effective_2026-04-16.zip"

print("Downloading NASR ZIP...")

response = requests.get(
    NASR_URL,
    timeout=120,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

response.raise_for_status()

print("Opening ZIP...")

zf = zipfile.ZipFile(io.BytesIO(response.content))

print("ZIP CONTENTS:")

for name in zf.namelist():
    print(name)

print("DONE")
