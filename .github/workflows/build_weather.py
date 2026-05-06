import json
import os
from datetime import datetime

def main():

    print("🔥 PYTHON STARTED")

    print("CURRENT DIR:", os.getcwd())
    print("FILES:", os.listdir("."))

    airports = {
        "TEST1": {"cat": "VFR"},
        "TEST2": {"cat": "VFR"}
    }

    output = {
        "meta": {
            "generated": datetime.utcnow().isoformat(),
            "debug": True
        },
        "airports": airports
    }

    file_path = "airport_weather.json"

    with open(file_path, "w") as f:
        json.dump(output, f, indent=2)

    print("✅ FILE WRITTEN AT:", file_path)

    print("VERIFY CONTENT:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
