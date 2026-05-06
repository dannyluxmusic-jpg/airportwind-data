import json
import os

print("🔥 BUILD WEATHER V2 STARTED")
print("FILE:", __file__)
print("CWD:", os.getcwd())

output_file = "airport_weather.json"

print("📍 OUTPUT PATH:", os.path.abspath(output_file))

data = {
    "meta": {
        "version": 2,
        "status": "DEBUG_RUN",
        "note": "if you see this in GitHub, script is working"
    },
    "airports": {
        "TEST": {
            "cat": "VFR",
            "lat": 0,
            "lon": 0
        }
    }
}

with open(output_file, "w") as f:
    json.dump(data, f, indent=2)

print("✅ WRITE COMPLETE")
print("📦 FILE SIZE CHECK:")
print(os.path.getsize(output_file))
