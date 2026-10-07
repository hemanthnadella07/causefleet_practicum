import os
import sqlite3
import subprocess
import time
import pandas as pd

start = time.time()
print(">>> STEP 1: Executing 5-Year Humanitarian Simulation...")
subprocess.run(["python", "scripts/build_midterm_environment.py"], check=True)

print("\n>>> STEP 2: Staging Relational SQLite Database (`causefleet_demo.db`)...")
if os.path.exists("causefleet_demo.db"):
    os.remove("causefleet_demo.db")

conn = sqlite3.connect("causefleet_demo.db")
with open("schema/schema.sql") as f:
    conn.cursor().executescript(f.read())

tables = ["org_profile", "staff", "donors", "impact_metrics", "campaigns", "goals", "events", "gifts", "major_gift_proposals", "interactions", "audience_metrics"]
for tbl in tables:
    df = pd.read_csv(f"data/{tbl}.csv")
    df.to_sql(tbl, conn, if_exists="append", index=False)
    print(f" - Staged `{tbl}` ({len(df)} rows)")

conn.commit()
conn.close()

print(f"\n[SUCCESS] Pipeline Built and Staged in {round(time.time() - start, 2)}s.")