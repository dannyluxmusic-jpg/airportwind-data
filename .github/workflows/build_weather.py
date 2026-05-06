import json
import requests
from datetime import datetime

METAR_URL = "https://aviationweather.gov/api/data/metar?format=raw&hours=2&taf=false"

def get_metars():
    r = requests.get(METAR_URL, timeout=30)
    return r.text.splitlines()

def parse_ceiling(metar):
    # very simplified ceiling detection
    import re
    matches = re.findall(r"(BKN|OVC)(\d{3})", metar)
    if not matches:
        return 10000

    # take lowest layer
    return min(int(h) * 100 for _, h in matches)

def parse_vis(metar):
    import re
    m = re.search(r"(\d+)\s?SM", metar)
    if not m:
        return 10
    return int(m.group(1))

def parse_wx(metar):
    for code in ["TS", "RA", "SN", "FG", "BR"]:
        if code in metar:
            return code
    return ""

def category(ceil, vis):
    if ceil < 500 or vis < 1:
        return "LIFR"
    if ceil < 1000 or vis < 3:
        return "IFR"
    if ceil < 3000 or vis < 5:
        return "MVFR"
    return "VFR"

def extract():
    lines = get_metars()

    airports = {}

    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue

        icao = parts[0]
        metar = " ".join(parts)

        ceil = parse_ceiling(metar)
        vis = parse_vis(metar)
        wx = parse_wx(metar)

        airports[icao] = {
            "cat": category(ceil, vis),
            "ceil": ceil,
            "vis": vis,
            "wx": wx
        }

    return airports

def main():
    airports = extract()

    output = {
        "meta": {
            "version": 2,
            "generated": datetime.utcnow().isoformat(),
            "source": "NOAA-METAR"
        },
        "airports": airports
    }

    with open("airport_weather.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Updated {len(airports)} airports")

if __name__ == "__main__":
    main()
