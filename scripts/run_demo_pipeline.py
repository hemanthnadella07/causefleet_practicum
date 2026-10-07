import os
import sqlite3
import subprocess
import time
import pandas as pd

start = time.time()
subprocess.run(["python", "scripts/build_midterm_environment.py"], check=True)
subprocess.run(["python", "scripts/verify_qa_integrity.py"], check=True)

if os.path.exists("causefleet_demo.db"):
    os.remove("causefleet_demo.db")

conn = sqlite3.connect("causefleet_demo.db")
with open("schema/schema.sql") as f:
    conn.cursor().executescript(f.read())

for tbl in ["org_profile", "staff", "campaigns", "goals", "events", "donors", "gifts", "interactions"]:
    df = pd.read_csv(f"data/{tbl}.csv")
    df.to_sql(tbl, conn, if_exists="append", index=False)

conn.commit()
conn.close()
print(f"[SUCCESS] Environment Built & Verified in {round(time.time() - start, 2)}s.")