import geopandas as gpd
import json
import os

🔍 Find shapefile dynamically

shp_path = None
for root, dirs, files in os.walk(“nasr”):
for file in files:
if file == “Class_Airspace.shp”:
shp_path = os.path.join(root, file)
break

if not shp_path:
raise Exception(“❌ Class_Airspace.shp not found”)

print(“✅ Using shapefile:”, shp_path)

gdf = gpd.read_file(shp_path)

def convert_alt(val, uom):
if val is None:
return 0
if uom == “FL”:
return val * 100
return val

features = []

for _, row in gdf.iterrows():
geom = row.geometry.geo_interface

lower = convert_alt(row.get("LOWER_VAL"), row.get("LOWER_UOM"))
upper = convert_alt(row.get("UPPER_VAL"), row.get("UPPER_UOM"))

features.append({
    "type": "Feature",
    "geometry": geom,
    "properties": {
        "class": row.get("CLASS", ""),
        "lower": lower,
        "upper": upper
    }
})
