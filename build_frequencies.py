name: Update Airport Frequencies

on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * *"

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo (FULL + CLEAN)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: main

      - name: Force sync to latest main
        run: |
          git fetch origin
          git checkout main
          git reset --hard origin/main

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip

      - name: Download NASR zip
        run: |
          NASR_URL=$(curl -fsSL "https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription" \
            | grep -Eo 'https://nfdc\.faa\.gov/webContent/28DaySub/28DaySubscription_Effective_[0-9\-]+\.zip' \
            | head -n 1)

          echo "Downloading: $NASR_URL"
          curl -L --fail -o NASR.zip "$NASR_URL"

      - name: Build airport_frequencies.csv
        run: |
          python build_frequencies.py

      - name: Commit changes (SAFE)
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"

          git add airport_frequencies.csv

          if git diff --cached --quiet; then
            echo "No changes to commit"
            exit 0
          fi

          git commit -m "Auto update airport frequencies"

          git pull --rebase origin main
          git push origin main
