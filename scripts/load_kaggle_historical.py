#!/usr/bin/env python3
"""
STUB — bootstrap historical UK/Ireland results from the Kaggle community
dataset. UNTESTED — blocked on your Kaggle account/API token.

See docs/FREE_DATA_SOURCES.md #2 for the exact steps:
1. Create a free Kaggle account
2. kaggle.com/settings -> Create New API Token -> downloads kaggle.json
3. mv kaggle.json ~/.kaggle/kaggle.json && chmod 600 ~/.kaggle/kaggle.json
4. pip install --user kaggle
5. Re-run this script

Once loaded, this data is for BACKTESTING / research bootstrap only — its
licence hasn't been verified (see FREE_DATA_SOURCES.md), so it must not be
redistributed or relied on as a source of truth until that's checked.
"""
import subprocess
import sys
from pathlib import Path

DATASET = "deltaromeo/horse-racing-results-ukireland-2015-2025"
DOWNLOAD_DIR = Path(__file__).parent.parent / "data" / "kaggle_historical"


def main():
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print(
            "BLOCKED: no ~/.kaggle/kaggle.json found.\n"
            "Create a free Kaggle account, generate an API token at "
            "kaggle.com/settings, and place it there. See "
            "docs/FREE_DATA_SOURCES.md #2 for exact steps."
        )
        sys.exit(1)

    try:
        import kaggle  # noqa: F401
    except ImportError:
        print("BLOCKED: the 'kaggle' package isn't installed. Run: pip3 install --user kaggle")
        sys.exit(1)

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(DOWNLOAD_DIR), "--unzip"],
        capture_output=True, text=True,
    )
    print(r.stdout)
    if r.returncode != 0:
        print("Download failed:", r.stderr, file=sys.stderr)
        sys.exit(1)

    csvs = list(DOWNLOAD_DIR.glob("*.csv"))
    print(f"Downloaded {len(csvs)} CSV file(s) to {DOWNLOAD_DIR}")
    for c in csvs:
        print(f"  {c.name}")
    print(
        "\nNext step (not yet built): write the loader that maps these CSV "
        "columns into runner_result / race rows, respecting observed_at / "
        "available_at as the CSV's own result-publication date, not today's "
        "date — otherwise this bootstrap data would itself violate the "
        "leakage rule. This mapping step needs the actual CSV headers to "
        "write correctly, which requires seeing a real download first."
    )


if __name__ == "__main__":
    main()
