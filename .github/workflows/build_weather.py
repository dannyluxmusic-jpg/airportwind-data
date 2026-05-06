import json
import requests
from datetime import datetime

# 🌍 more reliable aviation METAR feed
URL = "https://tgftp.nws.noaa.gov/data/observations/metar/stations.txt"


def parse_line(line):
    parts = line.split()
    if len(parts) < 3:
        return None
    return parts[0], line


def main():

    try:
        r = requests.get(URL, timeout=30)
        data = r.text
    except Exception as e:
        print("REQUEST FAILED:", e)
        return

    print("RAW SIZE:", len(data))

    airports = {}

    for line in data.splitlines():

        parsed = parse_line(line)
        if not parsed:
            continue

        icao, full = parsed
        airports[icao] = {"raw": full}

    print("AIRPORT COUNT:", len(airports))

    output = {
        "meta": {
            "generated": datetime.utcnow().isoformat(),
            "source": "NOAA-
