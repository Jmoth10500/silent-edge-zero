#!/usr/bin/env python3
"""Per-race market gap-fill / NULL-reason recorder. Run after the Smarkets collector.
See src/integrity/gapfill.py. Usage: python3 scripts/market_gap_fill.py [YYYY-MM-DD]"""
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from src.integrity.gapfill import gap_fill_day

if __name__ == "__main__":
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    conn = psycopg2.connect(dbname="silent_edge_zero")
    res = gap_fill_day(conn, d)
    print(f"{d}: {dict(Counter(r['action'] for r in res))}")
