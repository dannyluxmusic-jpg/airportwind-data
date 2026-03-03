def parse_twr_txt(zf: zipfile.ZipFile, ident3_to_icao: Dict[str, str]) -> List[Tuple[str, str, str]]:
    name = "TWR.txt"
    if name not in zf.namelist():
        print("NOTE: TWR.txt not found in NASR.zip; skipping tower/approach/departure/etc")
        return []

    rows: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str, str]] = set()

    print("Reading:", name)
    with zf.open(name) as f:
        for raw in f:
            try:
                line = raw.decode("latin-1")
            except Exception:
                continue

            if not line.startswith("TWR"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            freq = norm_freq(parts[1])
            if not freq:
                continue

            # --- FIXED IDENT LOGIC ---
            # Prefer a known 3-letter airport ident from APT.txt mapping
            ident: Optional[str] = None

            for tok in parts:
                t = tok.strip().upper().replace("*", "")
                if len(t) == 3 and t in ident3_to_icao:
                    ident = t
                    break

            # Fallback: direct 4-letter ICAO token like KLAX
            if not ident:
                for tok in parts:
                    t = tok.strip().upper().replace("*", "")
                    if len(t) == 4 and t.isalnum():
                        ident = t
                        break

            if not ident:
                continue

            # Convert to ICAO
            ident = norm_station(ident)
            if len(ident) == 3 and ident in ident3_to_icao:
                icao = ident3_to_icao[ident]
            else:
                icao = ident

            if not icao:
                continue

            typ = classify_twr_line(line)
            add_row(rows, seen, icao, typ, freq)

    return rows