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
      - name: Checkout repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: python -m pip install --upgrade pip

      - name: Download NASR
        run: |
          NASR_URL=$(curl -fsSL "https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription" \
            | grep -Eo 'https://nfdc\.faa\.gov/webContent/28DaySub/28DaySubscription_Effective_[0-9\-]+\.zip' \
            | head -n 1)

          echo "Downloading: $NASR_URL"
          curl -L -o NASR.zip "$NASR_URL"

      - name: Build frequencies
        run: python build_frequencies.py

      - name: Commit and FORCE push (FINAL FIX)
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"

          git add airport_frequencies.csv

          if git diff --cached --quiet; then
            echo "No changes"
            exit 0
          fi

          git commit -m "Auto update airport frequencies"

          # 🔥 THIS FIXES EVERYTHING
          git push --force origin HEAD:main
