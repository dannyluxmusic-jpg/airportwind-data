import json
import os
from datetime import datetime

print("🔥 BUILD WEATHER V2 RUNNING")

# always write to repo root file (GitHub Actions workspace)
output_file = os.path.join(os.getcwd(), "airport_weather.json")

print("📍 OUTPUT FILE:", output_file)
print("📁 WORKING DIR:", os.getcwd())

airports = {
    "KJFK": {
        "lat": 40.6413,
        "lon": -73.7781,
        "cat": "VFR"
    },
    "KLAX": {
        "lat": 33.9425,
        "lon": -118.4081,
        "cat": "MVFR"
    },
    "KJWN": {
        "lat": 36.1824,
        "lon": -86.8867,
        "cat": "IFR"
    }
}

output = {
    "meta": {
        "version": 2,
        "generated": datetime.utcnow().isoformat(),
        "source": "GITHUB_ACTIONS_V2"
    },
    "airports": airports
}

with open(output_file, "w") as f:
    json.dump(output, f, indent=2)

print("✅ WRITE COMPLETE")
print("AIRPORT COUNT:", len(airports))
