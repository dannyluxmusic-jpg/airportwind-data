import json
import requests
from datetime import datetime

METAR_URL = "https://aviationweather.gov/api/data/metar?format=raw&hours=2&taf=false"


def fetch_metars():
    try:
        r = requests.get(METAR_URL, timeout=30)
        r.raise_for_status()
        return r.text.splitlines()
    except Exception as e:
        print("❌ METAR fetch failed:", e)
        return []


def get_icao(line):
    parts = line.split()
    if len(parts) < 3:
        return None
    return parts[0]


def parse_ceiling(metar):
    import re
    hits = re.findall(r"(BKN|OVC)(\d{3})", metar)
    if not hits:
        return 10000
    return min(int(h) * 100 for _, h in hits)


def parse_vis(metar):
    import re
    m = re.search(r"(\d+)\s?SM", metar)
    if not m:
        return 10
    return int(m.group(1))


def classify(ceil, vis):
    if ceil < 500 or vis < 1:
        return "LIFR"
    if ceil < 1000 or vis < 3:
        return "IFR"
    if ceil < 3000 or vis < 5:
        return "MVFR"
    return "VFR"


def build():
    lines = fetch_metars()

    print("📡 METAR LINES RECEIVED:", len(lines))

    airports = {}

    for line in lines:

        icao = get_icao(line)
        if not icao:
            continue

        print("ICAO:", icao)

        ceil = parse_ceiling(line)
        vis = parse_vis(line)

        airports[icao] = {
            "cat": classify(ceil, vis),
            "ceil": ceil,
            "vis": vis
        }

    print("🛬 TOTAL AIRPORTS BUILT:", len(airports))

    return airports


def main():

    airports = build()

    output = {
        "meta": {
            "version": 2,
            "generated": datetime.utcnow().isoformat(),
            "source": "METAR"
        },
        "airports": airports
    }

    with open("airport_weather.json", "w") as f:
        json.dump(output, f, indent=2)

    print("✅ JSON WRITTEN")


if __name__ == "__main__":
    main()
