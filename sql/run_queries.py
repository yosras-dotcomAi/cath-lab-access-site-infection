"""
Runs every query in sql/queries.sql on the simulated data and prints the results.
Usage (from the repository root):  python sql/run_queries.py
"""

import re
import sqlite3
import pandas as pd

conn = sqlite3.connect(":memory:")
for table in ["procedures", "operators", "infection_events"]:
    pd.read_csv(f"data/{table}.csv").to_sql(table, conn, index=False)

with open("sql/queries.sql", encoding="utf-8") as f:
    text = f.read()

# Each query starts with a line like "-- Q3: description"
parts = re.split(r"^-- (Q\d+: .*)$", text, flags=re.MULTILINE)
for title, body in zip(parts[1::2], parts[2::2]):
    print(f"\n=== {title} ===")
    print(pd.read_sql_query(body.strip().rstrip(";"), conn).to_string(index=False))
