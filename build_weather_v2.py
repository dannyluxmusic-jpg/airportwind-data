print("🔥 V2 SCRIPT EXECUTING")

import json

print("STEP 1 REACHED")

data = {
    "meta": {
        "version": 2,
        "generated": "TEST",
        "source": "FORCED_DEBUG"
    },
    "airports": {
        "TEST": {"cat": "VFR"}
    }
}

print("STEP 2 REACHED")

with open("airport_weather.json", "w") as f:
    json.dump(data, f, indent=2)

print("STEP 3 FILE WRITTEN")
