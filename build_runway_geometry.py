import re

valid_count = 0
skipped_count = 0

def extract_coords(raw_line):
    """
    Extract FAA runway endpoint coordinates from malformed NASR rows.
    Returns:
        [lat1, lon1, lat2, lon2]
    or []
    """

    # FAA coords look like:
    # 61-12-56.4587N
    # 149-51-09.0466W

    pattern = r'\d{2,3}-\d{2}-\d{2}\.\d+[NS]|\d{3}-\d{2}-\d{2}\.\d+[EW]'

    matches = re.findall(pattern, raw_line)

    if len(matches) >= 4:
        return matches[:4]

    return []


with open("APT_RWY.txt", "r", encoding="latin-1") as f:
    for line in f:

        if not line.startswith("RWY"):
            continue

        coords = extract_coords(line)

        print("\n===================")
        print("RAW:", line.strip())
        print("COORDS:", coords)

        if len(coords) < 4:
            skipped_count += 1
            continue

        lat1, lon1, lat2, lon2 = coords

        # ---------------------------------
        # YOUR EXISTING GEOMETRY CODE HERE
        # ---------------------------------

        valid_count += 1


print("\n===================")
print(f"Valid runway geometries: {valid_count}")
print(f"Skipped malformed rows: {skipped_count}")
