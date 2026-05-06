import json
import os
from datetime import datetime

def fetch_airports():
    """
    TEMP SAFE TEST DATA
    (we will replace with FAA/NASR later once pipeline is stable)
    """

    return {
        "KJFK": {
            "name": "John F Kennedy Intl",
            "lat": 40.6413,
            "lon": -73.7781,
            "metar": "VFR"
        },
        "KLAX": {
            "name": "Los Angeles Intl",
            "lat": 33.9425,
            "lon": -118.4081,
            "metar": "MVFR"
        },
        "KJWN": {
            "name": "John C Tune",
            "lat": 36.1824,
            "lon": -86.8867,
            "metar": "IFR"
        }
    }

def build():
    print("=== WEATHER V2 START ===")
    print("cwd:", os.getcwd())

    airports = fetch_airports()

    output = {
        "meta": {
            "version": 2,
            "generated": datetime.utcnow().isoformat(),
            "source": "V2_FIXED_PIPELINE"
        },
        "airports": airports
    }

    out_file = "airport_weather.json"

    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print("WROTE FILE:", out_file)
    print("AIRPORT COUNT:", len(airports))

if __name__ == "__main__":
    build()
