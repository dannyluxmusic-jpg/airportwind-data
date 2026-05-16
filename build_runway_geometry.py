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

for line in lines:
    if line.startswith("RWY") and "16/34" in line:
        print(line)

print("DONE")
