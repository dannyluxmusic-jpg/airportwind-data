import json
from datetime import datetime

def main():

    airports = {
        "KJFK": {
            "lat": 40.6413,
            "lon": -73.7781,
            "cat": "VFR"
        },
        "KLAX": {
            "lat": 33.9425,
            "lon": -118.4081,
            "cat": "VFR"
        },
        "KJWN": {
            "lat": 36.1824,
            "lon": -86.8867,
            "cat": "VFR"
        }
    }

    output = {
        "meta": {
            "version": 1,
            "generated": datetime.utcnow().isoformat(),
            "source": "STATIC_TEST"
        },
        "airports": airports
    }

    with open("airport_weather.json", "w") as f:
        json.dump(output, f, indent=2)

    print("AIRPORTS WRITTEN:", len(airports))


if __name__ == "__main__":
    main()
