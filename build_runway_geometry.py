import io
import zipfile
import requests

NASR_URL = "https://nfdc.faa.gov/webContent/28DaySub/current/28DaySubscription_Effective.zip"

print("Downloading NASR...")

response = requests.get(NASR_URL, timeout=120)
response.raise_for_status()

print("Opening ZIP...")

zf = zipfile.ZipFile(io.BytesIO(response.content))

print("ZIP CONTENTS:")

for name in zf.namelist():
    print(name)

print("DONE")
