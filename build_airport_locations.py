def dms_to_decimal(value, hemisphere):

    value = value.strip()

    if len(value) < 7:
        raise ValueError("Bad DMS")

    # LATITUDE
    if hemisphere in ["N", "S"]:

        degrees = int(value[0:2])
        minutes = int(value[2:4])
        seconds = float(value[4:])

    # LONGITUDE
    else:

        degrees = int(value[0:3])
        minutes = int(value[3:5])
        seconds = float(value[5:])

    decimal = (
        degrees +
        (minutes / 60.0) +
        (seconds / 3600.0)
    )

    if hemisphere in ["S", "W"]:
        decimal *= -1

    return decimal
