import json

def main():

    print("🔥 SCRIPT STARTED")

    airports = {
        "TEST1": {"cat": "VFR"},
        "TEST2": {"cat": "IFR"}
    }

    print("AIRPORTS:", len(airports))

    output = {
        "meta": {"test": True},
        "airports": airports
    }

    with open("airport_weather.json", "w") as f:
        json.dump(output, f, indent=2)

    print("✅ FILE WRITTEN")

if __name__ == "__main__":
    main()
