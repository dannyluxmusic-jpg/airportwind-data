import json
from datetime import datetime

def extract_simple_metar_data():
    return {
        "KBNA": {"ceil": 4500, "vis": 10, "wind": 320, "wind_spd": 10, "wx": "BR"},
        "KJWN": {"ceil": 1800, "vis": 4, "wind": 290, "wind_spd": 12, "wx": "RA"},
        "KMQY": {"ceil": 800, "vis": 2, "wind": 310, "wind_spd": 8, "wx": "FG"}
    }

def parse_category(ceiling, vis):
    if ceiling < 500 or vis < 1:
        return "LIFR"
    elif ceiling < 1000 or vis < 3:
        return "IFR"
    elif ceiling < 3000 or vis < 5:
        return "MVFR"
    return "VFR"

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

    for icao, d in airports.items():
        output["airports"][icao] = {
            "cat": parse_category(d["ceil"], d["vis"]),
            "ceil": d["ceil"],
            "vis": d["vis"],
            "wind": d["wind"],
            "wind_spd": d["wind_spd"],
            "wx": d["wx"]
        }

    with open("airport_weather.json", "w") as f:
        json.dump(output, f, indent=2)

    print("done")

if __name__ == "__main__":
    main()
