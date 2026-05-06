import json
import os
from datetime import datetime

print("🔥🔥🔥 V2 SCRIPT IS RUNNING 🔥🔥🔥")
print("FILE LOCATION:", __file__)
print("WORKING DIR:", os.getcwd())

airports = {
    "V2-KJFK": {"cat": "VFR"},
    "V2-KLAX": {"cat": "MVFR"},
    "V2-KJWN": {"cat": "IFR"}
}

output = {
    "meta": {
        "version": 2,
        "generated": datetime.utcnow().isoformat(),
        "source": "FORCED_V2_TRACE"
    },
    "airports": airports
}

with open("airport_weather.json", "w") as f:
    json.dump(output, f, indent=2)

print("✅ V2 WRITE COMPLETE")
print("AIRPORT COUNT:", len(airports))
