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
          fetch-depth: 0

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

      - name: Backup old CSV (if exists)
        run: |
          if [ -f airport_frequencies.csv ]; then
            cp airport_frequencies.csv airport_frequencies_backup.csv
          fi

      - name: Merge (preserve phones if you add later)
        run: |
          # Right now this just replaces.
          # Later we plug in phone merge here.
          cp airport_frequencies.csv airport_frequencies.csv

      - name: Commit changes (FIXED PUSH)
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"

          # Sync with remote FIRST (this is what was failing before)
          git fetch origin main
          git reset --hard origin/main

          git add airport_frequencies.csv

          if git diff --cached --quiet; then
            echo "No changes"
            exit 0
          fi

          git commit -m "Auto update airport frequencies"

          git push origin main
