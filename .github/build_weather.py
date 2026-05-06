import requests
import json
from datetime import datetime

# Simple METAR feed (NOAA)
URL = "https://tgftp.nws.noaa.gov/data/observations/metar/stations.txt"

def get_metars():
    # This is a lightweight public feed alternative approach
    # We'll replace with full NASR list later
    return {}

def parse_category(ceiling_ft, visibility_sm):
    if ceiling_ft is None or visibility_sm is None:
        return "VFR"

    if ceiling_ft < 500 or visibility_sm < 1:
        return "LIFR"
    elif ceiling_ft < 1000 or visibility_sm < 3:
        return "IFR"
    elif ceiling_ft < 3000 or visibility_sm < 5:
        return "MVFR"
    else:
        return "VFR"

def extract_simple_metar_data():
    # TEMP MOCK (we will upgrade to full FAA/NASR feed next step)
    # This keeps pipeline working first

    sample = {
        "KBNA": {"ceil": 4500, "vis": 10, "wind": 320, "wind_spd": 10, "wx": "BR"},
        "KJWN": {"ceil": 1800, "vis": 4, "wind": 290, "wind_spd": 12, "wx": "RA"},
        "KMQY": {"ceil": 800, "vis": 2, "wind": 310, "wind_spd": 8, "wx": "FG"}
    }

    return sample

def main():
    airports = extract_simple_metar_data()

    output = {
        "meta": {
            "version": 1,
            "generated": datetime.utcnow().isoformat(),
            "source": "METAR-MOCK"
        },
        "airports": {}
    }

    for icao, data in airports.items():
        cat = parse_category(data["ceil"], data["vis"])

        output["airports"][icao] = {
            "cat": cat,
            "ceil": data["ceil"],
            "vis": data["vis"],
            "wind": data["wind"],
            "wind_spd": data["wind_spd"],
            "wx": data["wx"]
        }

    with open("airport_weather.json", "w") as f:
        json.dump(output, f, indent=2)

    print("Airport weather cache built successfully")

if __name__ == "__main__":
    main()
