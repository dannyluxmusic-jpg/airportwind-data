name: Update Airport Frequencies

on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * *"   # daily at 06:00 UTC

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 40

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0   # IMPORTANT (fixes push issues)

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip

      - name: Download current NASR zip
        shell: bash
        run: |
          set -euo pipefail

          NASR_URL=$(curl -fsSL "https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription" \
            | grep -Eo 'https://nfdc\.faa\.gov/webContent/28DaySub/28DaySubscription_Effective_[0-9]{4}-[0-9]{2}-[0-9]{2}\.zip' \
            | head -n 1)

          echo "Resolved NASR URL:"
          echo "$NASR_URL"

          curl -L --fail --retry 20 --retry-all-errors --retry-delay 5 \
            -o NASR.zip "$NASR_URL"

          ls -lh NASR.zip

      - name: Build new frequencies
        run: python build_frequencies.py

      - name: Merge (preserve phones)
        run: |
          python - << 'EOF'
          import csv

          old_rows = []
          try:
              with open("airport_frequencies.csv") as f:
                  old_rows = list(csv.DictReader(f))
          except:
              pass

          with open("airport_frequencies.csv") as f:
              new_rows = list(csv.DictReader(f))

          merged = {(r["icao"], r["type"], r["value"]): r for r in new_rows}

          for r in old_rows:
              if r["type"] == "phone":
                  key = (r["icao"], r["type"], r["value"])
                  merged[key] = r

          with open("airport_frequencies.csv", "w", newline="") as f:
              w = csv.DictWriter(f, fieldnames=["icao","type","value"])
              w.writeheader()
              for r in merged.values():
                  w.writerow(r)
          EOF

      - name: Commit changes (FINAL FIX)
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"

          git fetch origin main
          git reset --hard origin/main

          git add airport_frequencies.csv
          git diff --cached --quiet && echo "No changes to commit" && exit 0

          git commit -m "Auto update airport frequencies"
          git push origin HEAD:main
