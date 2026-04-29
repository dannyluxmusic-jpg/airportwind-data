#!/usr/bin/env python3

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NASR_ZIP = HERE / "NASR.zip"
WORK = HERE / "airspace_work"
OUT = HERE / "usa_airspace.geojson"

KEEP_CLASSES = {"B", "C", "D"}

def main():
    if not NASR_ZIP.exists():
        raise FileNotFoundError("NASR.zip not found")

    if WORK.exists():
        shutil.rmtree(WORK)

    WORK.mkdir()

    with zipfile.ZipFile(NASR_ZIP) as z:
        z.extractall(WORK)

    shp = next(WORK.rglob("Class_Airspace.shp"), None)

    if not shp:
        print("Available SHP files:")
        for p in WORK.rglob("*.shp"):
            print(p)
        raise FileNotFoundError("Class_Airspace.shp not found")

    raw = WORK / "raw_airspace.geojson"

    subprocess.run([
        "ogr2ogr",
        "-f", "GeoJSON",
        str(raw),
        str(shp)
    ], check=True)

    with open(raw, "r", encoding="utf-8") as f:
        data = json.load(f)

    filtered = []
    for feature in data.get("features", []):
        props = feature.get("properties", {}) or {}

        cls = (
            props.get("CLASS")
            or props.get("AIRSPACE_CLASS")
            or props.get("TYPE_CODE")
            or ""
        )

        cls = str(cls).strip().upper().replace("CLASS ", "")

        if cls in KEEP_CLASSES:
            filtered.append(feature)

    data["features"] = filtered

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))

    print(f"Found shapefile: {shp}")
    print(f"Saved {len(filtered)} Class B/C/D features to {OUT}")

if __name__ == "__main__":
    main()
