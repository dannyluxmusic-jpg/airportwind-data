import json
import os

print("🔥 V2 FILE IS DEFINITELY RUNNING")
print("FILE PATH:", __file__)
print("WORKING DIR:", os.getcwd())

data = {
    "meta": {
        "version": 2,
        "proof": "THIS FILE EXECUTED",
    },
    "airports": {
        "PROOF": {"cat": "VFR"}
    }
}

with open("airport_weather.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ FILE WRITTEN SUCCESSFULLY")
