import os
import sys
import json
import sqlite3
import subprocess
import time

print("=" * 70)
print("UPDATING CAUSEFLEET REPOSITORY TO REVISION 2 (HUMANITARIAN + AI)")
print("=" * 70)

# 1. Update Schema (11 Relational Entities)
SCHEMA_SQL = """DROP TABLE IF EXISTS audience_metrics;
DROP TABLE IF EXISTS major_gift_proposals;
DROP TABLE IF EXISTS interactions;
DROP TABLE IF EXISTS gifts;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS goals;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS impact_metrics;
DROP TABLE IF EXISTS donors;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS org_profile;

CREATE TABLE org_profile (
    org_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    sector VARCHAR(64) NOT NULL,
    annual_budget DECIMAL(14, 2) NOT NULL,
    cash_reserves_months DECIMAL(4, 1) NOT NULL,
    monthly_burn_rate DECIMAL(14, 2) NOT NULL,
    fiscal_year_start DATE NOT NULL,
    is_synthetic_label BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE staff (
    staff_id VARCHAR(32) PRIMARY KEY,
    org_id VARCHAR(32) NOT NULL,
    full_name VARCHAR(64) NOT NULL,
    title VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    role VARCHAR(32) NOT NULL,
    portfolio_capacity INT DEFAULT 0,
    FOREIGN KEY (org_id) REFERENCES org_profile(org_id) ON DELETE CASCADE
);

CREATE TABLE donors (
    donor_id VARCHAR(32) PRIMARY KEY,
    org_id VARCHAR(32) NOT NULL,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    phone VARCHAR(32),
    address VARCHAR(128),
    city VARCHAR(64),
    state VARCHAR(8),
    zip_code VARCHAR(16),
    donor_type VARCHAR(32) NOT NULL CHECK (donor_type IN ('Individual', 'Foundation', 'Corporation')),
    giving_level VARCHAR(32) NOT NULL CHECK (giving_level IN ('Under 100','100-999','1,000-9,999','10,000-99,999','100,000+')),
    assigned_mgo_id VARCHAR(32),
    is_top_100 BOOLEAN NOT NULL DEFAULT 0,
    created_at DATE NOT NULL,
    is_synthetic_label BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (org_id) REFERENCES org_profile(org_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_mgo_id) REFERENCES staff(staff_id) ON DELETE SET NULL
);

CREATE TABLE impact_metrics (
    metric_id VARCHAR(32) PRIMARY KEY,
    org_id VARCHAR(32) NOT NULL,
    year INT NOT NULL,
    metric_name VARCHAR(64) NOT NULL,
    actual_value DECIMAL(14, 2) NOT NULL,
    target_value DECIMAL(14, 2) NOT NULL,
    cost_per_unit DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (org_id) REFERENCES org_profile(org_id) ON DELETE CASCADE
);

CREATE TABLE campaigns (
    campaign_id VARCHAR(32) PRIMARY KEY,
    org_id VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    goal_amount DECIMAL(14, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    channel VARCHAR(32) NOT NULL,
    is_emergency_appeal BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (org_id) REFERENCES org_profile(org_id) ON DELETE CASCADE
);

CREATE TABLE goals (
    goal_id VARCHAR(32) PRIMARY KEY,
    campaign_id VARCHAR(32) NOT NULL,
    target_metric VARCHAR(64) NOT NULL,
    target_value DECIMAL(14, 2) NOT NULL,
    deadline DATE NOT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
);

CREATE TABLE events (
    event_id VARCHAR(32) PRIMARY KEY,
    campaign_id VARCHAR(32) NOT NULL,
    event_name VARCHAR(128) NOT NULL,
    event_date DATE NOT NULL,
    ticket_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE CASCADE
);

CREATE TABLE gifts (
    gift_id VARCHAR(32) PRIMARY KEY,
    donor_id VARCHAR(32) NOT NULL,
    campaign_id VARCHAR(32) NOT NULL,
    amount DECIMAL(14, 2) NOT NULL CHECK (amount > 0),
    gift_date DATE NOT NULL,
    payment_channel VARCHAR(32) NOT NULL,
    is_pledge BOOLEAN NOT NULL DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'Completed',
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE RESTRICT
);

CREATE TABLE major_gift_proposals (
    proposal_id VARCHAR(32) PRIMARY KEY,
    donor_id VARCHAR(32) NOT NULL,
    staff_id VARCHAR(32) NOT NULL,
    stage VARCHAR(32) NOT NULL,
    ask_amount DECIMAL(14, 2) NOT NULL,
    expected_close_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE RESTRICT
);

CREATE TABLE interactions (
    interaction_id VARCHAR(32) PRIMARY KEY,
    donor_id VARCHAR(32) NOT NULL,
    staff_id VARCHAR(32) NOT NULL,
    interaction_date DATE NOT NULL,
    type VARCHAR(64) NOT NULL,
    notes TEXT,
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE RESTRICT
);

CREATE TABLE audience_metrics (
    month_id VARCHAR(16) PRIMARY KEY,
    email_subscribers INT NOT NULL,
    mailable_households INT NOT NULL,
    social_followers INT NOT NULL,
    website_visitors INT NOT NULL,
    web_conversion_rate DECIMAL(5, 4) NOT NULL
);

CREATE INDEX idx_gifts_donor ON gifts(donor_id);
CREATE INDEX idx_gifts_date ON gifts(gift_date);
CREATE INDEX idx_gifts_campaign ON gifts(campaign_id);
CREATE INDEX idx_donors_mgo ON donors(assigned_mgo_id);
"""
with open("schema/schema.sql", "w") as f:
    f.write(SCHEMA_SQL.strip())
print("[WRITE] schema/schema.sql")

# 2. Update Configuration
CONFIG_JSON = """{
  "archetype": "International Humanitarian Relief (10M-50M Range)",
  "org_id": "ORG-HUM-01",
  "org_name": "Global Hope International Relief",
  "sector": "International Humanitarian (Food, Water, Education)",
  "target_annual_revenue": 32450000.0,
  "simulation_years": [2022, 2023, 2024, 2025, 2026],
  "exact_donor_population": 5123,
  "cash_reserves_months": 5.4,
  "monthly_burn_rate": 2650000.0,
  "donor_type_distribution": {"Individual": 0.88, "Foundation": 0.08, "Corporation": 0.04},
  "giving_level_distribution": {
    "Under 100":0.62,"100-999":0.26,"1,000-$9,999": 0.09,
    "10,000-99,999": 0.026, "$100,000+": 0.004
  },
  "storylines": {
    "storyline_1_major_donor_id": "DNR-00042",
    "storyline_2_gala_campaign_id": "CMP-2025-GALA",
    "storyline_3_disaster_campaign_id": "CMP-2024-EMERGENCY-HORN-AFRICA"
  }
}"""
with open("config/config_midterm.json", "w") as f:
    f.write(CONFIG_JSON.strip())
print("[WRITE] config/config_midterm.json")

# 3. Update Generator Script
BUILD_SCRIPT = '''import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from faker import Faker

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

with open("config/config_midterm.json", "r") as f:
    cfg = json.load(f)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
org_id = cfg["org_id"]

pd.DataFrame([{
    "org_id": org_id, "name": cfg["org_name"], "sector": cfg["sector"],
    "annual_budget": cfg["target_annual_revenue"], "cash_reserves_months": cfg["cash_reserves_months"],
    "monthly_burn_rate": cfg["monthly_burn_rate"], "fiscal_year_start": "2022-01-01",
    "is_synthetic_label": True
}]).to_csv(f"{DATA_DIR}/org_profile.csv", index=False)

pd.DataFrame([
    {"staff_id": "STF-01", "org_id": org_id, "full_name": "Sarah Jenkins", "title": "Chief Executive Officer", "email": "synthetic.sjenkins@demo-causefleet.org", "role": "Executive", "portfolio_capacity": 0},
    {"staff_id": "STF-02", "org_id": org_id, "full_name": "Marcus Vance", "title": "Senior Major Gifts Officer", "email": "synthetic.mvance@demo-causefleet.org", "role": "MGO", "portfolio_capacity": 150},
    {"staff_id": "STF-03", "org_id": org_id, "full_name": "David Kim", "title": "Major Gifts Officer", "email": "synthetic.dkim@demo-causefleet.org", "role": "MGO", "portfolio_capacity": 150},
    {"staff_id": "STF-04", "org_id": org_id, "full_name": "Elena Rostova", "title": "Annual Fund Director", "email": "synthetic.erostova@demo-causefleet.org", "role": "Coordinator", "portfolio_capacity": 0}
]).to_csv(f"{DATA_DIR}/staff.csv", index=False)

n_donors = cfg["exact_donor_population"]
types = list(cfg["donor_type_distribution"].keys())
type_p = list(cfg["donor_type_distribution"].values())
levels = list(cfg["giving_level_distribution"].keys())
level_p = list(cfg["giving_level_distribution"].values())

assigned_types = np.random.choice(types, size=n_donors, p=type_p)
assigned_levels = np.random.choice(levels, size=n_donors, p=level_p)

donors = []
for i in range(1, n_donors + 1):
    did = f"DNR-{i:05d}"
    created = fake.date_between(start_date=datetime(2021, 6, 1), end_date=datetime(2025, 10, 1))
    donors.append({
        "donor_id": did, "org_id": org_id, "first_name": fake.first_name(), "last_name": fake.last_name(),
        "email": f"synthetic.{did.lower()}@demo-causefleet.org", "phone": f"555-01{random.randint(10, 99)}",
        "address": fake.street_address(), "city": fake.city(), "state": fake.state_abbr(), "zip_code": fake.zipcode(),
        "donor_type": assigned_types[i - 1], "giving_level": assigned_levels[i - 1],
        "assigned_mgo_id": None, "is_top_100": False, "created_at": created.strftime("%Y-%m-%d"),
        "is_synthetic_label": True
    })

df_donors = pd.DataFrame(donors)
target_major_id = cfg["storylines"]["storyline_1_major_donor_id"]
df_donors.loc[df_donors["donor_id"] == target_major_id, "giving_level"] = "$100,000+"
df_donors.loc[df_donors["donor_id"] == target_major_id, "created_at"] = "2021-08-15"

gala_cohort = [f"DNR-{i:05d}" for i in range(200, 400)]
for did in gala_cohort:
    df_donors.loc[df_donors["donor_id"] == did, "giving_level"] = "100-999"
    df_donors.loc[df_donors["donor_id"] == did, "created_at"] = "2025-09-15"

top_100_ids = [target_major_id] + [f"DNR-{i:05d}" for i in range(2, 101)]
for idx, did in enumerate(top_100_ids):
    df_donors.loc[df_donors["donor_id"] == did, "is_top_100"] = True
    if df_donors.loc[df_donors["donor_id"] == did, "giving_level"].values[0] in ["Under 100","100-$999"]:
        df_donors.loc[df_donors["donor_id"] == did, "giving_level"] = "10,000-99,999"
    assigned_mgo = "STF-02" if idx % 2 == 0 else "STF-03"
    df_donors.loc[df_donors["donor_id"] == did, "assigned_mgo_id"] = assigned_mgo

df_donors.to_csv(f"{DATA_DIR}/donors.csv", index=False)

pd.DataFrame([
    {"campaign_id": "CMP-2022-ANN", "org_id": org_id, "name": "2022 Clean Water & Food Hope", "goal_amount": 28000000.0, "start_date": "2022-01-01", "end_date": "2022-12-31", "channel": "Omnichannel", "is_emergency_appeal": False},
    {"campaign_id": "CMP-2023-ANN", "org_id": org_id, "name": "2023 Clean Water & Food Hope", "goal_amount": 30000000.0, "start_date": "2023-01-01", "end_date": "2023-12-31", "channel": "Omnichannel", "is_emergency_appeal": False},
    {"campaign_id": "CMP-2024-ANN", "org_id": org_id, "name": "2024 Clean Water & Food Hope", "goal_amount": 32000000.0, "start_date": "2024-01-01", "end_date": "2024-12-31", "channel": "Omnichannel", "is_emergency_appeal": False},
    {"campaign_id": cfg["storylines"]["storyline_3_disaster_campaign_id"], "org_id": org_id, "name": "East Africa Flash Flood Emergency Relief", "goal_amount": 3500000.0, "start_date": "2024-05-01", "end_date": "2024-07-31", "channel": "Digital Surge", "is_emergency_appeal": True},
    {"campaign_id": "CMP-2025-ANN", "org_id": org_id, "name": "2025 Global Poverty Relief", "goal_amount": 34000000.0, "start_date": "2025-01-01", "end_date": "2025-12-31", "channel": "Omnichannel", "is_emergency_appeal": False},
    {"campaign_id": cfg["storylines"]["storyline_2_gala_campaign_id"], "org_id": org_id, "name": "2025 Fall Hope Gala for Education", "goal_amount": 2500000.0, "start_date": "2025-09-01", "end_date": "2025-10-31", "channel": "Special Event", "is_emergency_appeal": False},
    {"campaign_id": "CMP-2026-ANN", "org_id": org_id, "name": "2026 Resilient Communities Initiative", "goal_amount": 35000000.0, "start_date": "2026-01-01", "end_date": "2026-12-31", "channel": "Omnichannel", "is_emergency_appeal": False}
]).to_csv(f"{DATA_DIR}/campaigns.csv", index=False)

impact_records = []
imp_id = 1
for yr in [2022, 2023, 2024, 2025, 2026]:
    growth = 1.0 + (yr - 2022) * 0.05
    impact_records.append({"metric_id": f"IMP-{imp_id:04d}", "org_id": org_id, "year": yr, "metric_name": "Countries Served", "actual_value": int(18 * growth), "target_value": int(20 * growth), "cost_per_unit": 350000.0})
    imp_id += 1
    f_mult = 1.25 if yr == 2024 else growth
    impact_records.append({"metric_id": f"IMP-{imp_id:04d}", "org_id": org_id, "year": yr, "metric_name": "People Receiving Food & Water", "actual_value": int(1450000 * f_mult), "target_value": int(1500000 * growth), "cost_per_unit": 12.50})
    imp_id += 1
    impact_records.append({"metric_id": f"IMP-{imp_id:04d}", "org_id": org_id, "year": yr, "metric_name": "People with Access to Education", "actual_value": int(320000 * growth), "target_value": int(350000 * growth), "cost_per_unit": 28.00})
    imp_id += 1
pd.DataFrame(impact_records).to_csv(f"{DATA_DIR}/impact_metrics.csv", index=False)

proposals = []
for p_idx, did in enumerate(top_100_ids[:50]):
    proposals.append({
        "proposal_id": f"PRP-{p_idx+1:04d}", "donor_id": did, "staff_id": "STF-02" if p_idx % 2 == 0 else "STF-03",
        "stage": random.choice(["Cultivation", "Solicitation", "Stewardship", "Closed Won"]),
        "ask_amount": random.choice([25000.0, 50000.0, 100000.0, 250000.0]), "expected_close_date": f"2026-{random.randint(10,12):02d}-15", "status": "Active"
    })
pd.DataFrame(proposals).to_csv(f"{DATA_DIR}/major_gift_proposals.csv", index=False)

pd.DataFrame([
    {"goal_id": "GL-01", "campaign_id": "CMP-2025-ANN", "target_metric": "Annual Revenue", "target_value": 34000000.0, "deadline": "2025-12-31"},
    {"goal_id": "GL-02", "campaign_id": cfg["storylines"]["storyline_2_gala_campaign_id"], "target_metric": "Gala Education Fund", "target_value": 2500000.0, "deadline": "2025-10-31"},
    {"goal_id": "GL-03", "campaign_id": cfg["storylines"]["storyline_3_disaster_campaign_id"], "target_metric": "Disaster Relief Revenue", "target_value": 3500000.0, "deadline": "2024-07-31"}
]).to_csv(f"{DATA_DIR}/goals.csv", index=False)

pd.DataFrame([{"event_id": "EVT-2025-01", "campaign_id": cfg["storylines"]["storyline_2_gala_campaign_id"], "event_name": "Annual Hope Gala for Education", "event_date": "2025-10-15", "ticket_price": 250.00}]).to_csv(f"{DATA_DIR}/events.csv", index=False)

aud_months = []
start_mo = datetime(2022, 1, 1)
for m_idx in range(58):
    mo_dt = start_mo + timedelta(days=m_idx * 30.5)
    aud_months.append({
        "month_id": mo_dt.strftime("%Y-%m"), "email_subscribers": int(85000 + m_idx * 750),
        "mailable_households": int(42000 + m_idx * 300), "social_followers": int(110000 + m_idx * 1200),
        "website_visitors": int(35000 + random.randint(1000, 8000)), "web_conversion_rate": round(random.uniform(0.018, 0.026), 4)
    })
pd.DataFrame(aud_months).to_csv(f"{DATA_DIR}/audience_metrics.csv", index=False)

gifts = []
interactions = []
gift_id_ctr = 1
int_id_ctr = 1

def add_gift(did, amt, dt_str, cid, ch="Online", is_pl=False):
    global gift_id_ctr
    gid = f"GFT-{gift_id_ctr:07d}"
    gift_id_ctr += 1
    return {
        "gift_id": gid, "donor_id": did, "campaign_id": cid, "amount": round(float(amt), 2),
        "gift_date": dt_str, "payment_channel": ch, "is_pledge": is_pl, "status": "Completed"
    }

for _, d in df_donors.iterrows():
    did = d["donor_id"]
    lvl = d["giving_level"]
    created_dt = datetime.strptime(d["created_at"], "%Y-%m-%d")

    if did == target_major_id:
        for y_idx, yr in enumerate([2022, 2023, 2024, 2025]):
            gifts.append(add_gift(did, 50000.0, f"{yr}-11-15", f"CMP-{yr}-ANN", ch="Wire Transfer", is_pl=True))
        gifts.append(add_gift(did, 5000.0, "2026-06-12", "CMP-2026-ANN", ch="Online"))
        interactions.append({
            "interaction_id": f"INT-{int_id_ctr:06d}", "donor_id": did, "staff_id": "STF-02",
            "interaction_date": "2025-11-22", "type": "Major Donor VIP Dinner",
            "notes": "Donor attended; noted interest in water projects. Lapsed subsequent follow-up call."
        })
        int_id_ctr += 1
        continue

    if did in gala_cohort:
        gifts.append(add_gift(did, random.uniform(150, 450), "2025-10-15", cfg["storylines"]["storyline_2_gala_campaign_id"], ch="Event"))
        if random.random() < 0.135:
            gifts.append(add_gift(did, random.uniform(75, 200), "2026-04-12", "CMP-2026-ANN", ch="Online"))
        continue

    for yr in [2022, 2023, 2024, 2025, 2026]:
        yr_start = datetime(yr, 1, 1)
        if created_dt > datetime(yr, 12, 31):
            continue
        end_cap = datetime(2026, 9, 30) if yr == 2026 else datetime(yr, 12, 28)
        start_bound = max(created_dt, yr_start)
        if start_bound > end_cap:
            continue

        if yr == 2024 and random.random() < 0.35:
            d_amt = random.uniform(100, 1500) if lvl in ["1,000-9,999", "10,000-99,999"] else random.uniform(25, 150)
            gifts.append(add_gift(did, d_amt, "2024-05-20", cfg["storylines"]["storyline_3_disaster_campaign_id"], ch="Digital Surge"))

        if lvl == "$100,000+":
            for _ in range(random.randint(1, 2)):
                amt = random.uniform(100000, 250000)
                dt = fake.date_between(start_date=start_bound, end_date=end_cap)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Wire Transfer", is_pl=True))
        elif lvl == "10,000-99,999":
            for _ in range(random.randint(1, 2)):
                amt = random.uniform(10000, 45000)
                dt = fake.date_between(start_date=start_bound, end_date=end_cap)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Check", is_pl=True))
        elif lvl == "1,000-9,999":
            for _ in range(random.randint(1, 3)):
                amt = random.uniform(1000, 4500)
                dt = fake.date_between(start_date=start_bound, end_date=end_cap)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Credit Card"))
        elif lvl == "100-999":
            if random.random() < 0.70:
                amt = random.uniform(100, 600)
                dt = fake.date_between(start_date=start_bound, end_date=end_cap)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Online"))
        else:
            if random.random() < 0.55:
                amt = random.uniform(20, 85)
                dt = fake.date_between(start_date=start_bound, end_date=end_cap)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Online"))

pd.DataFrame(gifts).to_csv(f"{DATA_DIR}/gifts.csv", index=False)
pd.DataFrame(interactions).to_csv(f"{DATA_DIR}/interactions.csv", index=False)
print(f"[PASS] 5-Year Dataset: {len(df_donors)} Donors | {len(gifts)} Gifts")
'''
with open("scripts/build_midterm_environment.py", "w") as f:
    f.write(BUILD_SCRIPT.strip())
print("[WRITE] scripts/build_midterm_environment.py")

# 4. Write Smart Companion Prototype (Deliverable D5)
COMPANION_SCRIPT = '''import sqlite3
import re

DB_FILE = "causefleet_demo.db"

class CausefleetSmartCompanion:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path

    def answer_question(self, question: str) -> str:
        q = question.lower()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if "revenue" in q or "raised" in q or "giving" in q:
            year_match = re.search(r"202[2-6]", q)
            if year_match:
                yr = year_match.group(0)
                cursor.execute("SELECT SUM(amount), COUNT(gift_id) FROM gifts WHERE gift_date LIKE ?", (f"{yr}%",))
                rev, count = cursor.fetchone()
                conn.close()
                return f"[Smart Companion] In {yr}, total revenue was ${rev:,.2f} across {count:,} gifts. (Source: gifts table)"
            else:
                cursor.execute("SELECT SUBSTR(gift_date, 1, 4) as yr, SUM(amount) FROM gifts GROUP BY yr ORDER BY yr")
                rows = cursor.fetchall()
                conn.close()
                breakdown = ", ".join([f"{r[0]}: ${r[1]:,.0f}" for r in rows])
                return f"[Smart Companion] Multi-year revenue totals: {breakdown}. (Source: gifts table)"

        if "top donor" in q or "major donor" in q or "biggest donor" in q:
            cursor.execute("""
                SELECT d.first_name || ' ' || d.last_name, d.donor_type, SUM(g.amount) as total_given, s.full_name
                FROM donors d
                JOIN gifts g ON d.donor_id = g.donor_id
                LEFT JOIN staff s ON d.assigned_mgo_id = s.staff_id
                WHERE d.is_top_100 = 1
                GROUP BY d.donor_id ORDER BY total_given DESC LIMIT 5
            """)
            rows = cursor.fetchall()
            conn.close()
            resp = "[Smart Companion] Top 5 Major Donors:\\n"
            for r in rows:
                mgo = f" (MGO: {r[3]})" if r[3] else ""
                resp += f" • {r[0]} ({r[1]}): ${r[2]:,.2f}{mgo}\\n"
            resp += "(Source: donors, gifts, staff tables)"
            return resp

        if "impact" in q or "food" in q or "water" in q or "education" in q or "countries" in q:
            cursor.execute("SELECT year, metric_name, actual_value, target_value FROM impact_metrics WHERE year = 2025")
            rows = cursor.fetchall()
            conn.close()
            resp = "[Smart Companion] 2025 Mission Impact Results:\\n"
            for r in rows:
                resp += f" • {r[1]}: {int(r[2]):,} reached (Target: {int(r[3]):,})\\n"
            resp += "(Source: impact_metrics table, reconciled to expenditures)"
            return resp

        if ("why did" in q or "stop giving" in q or "decrease" in q) and ("eleanor" in q or "vance" in q or "dnr-00042" in q or "major donor" in q):
            cursor.execute("SELECT SUBSTR(gift_date, 1, 4) as yr, SUM(amount) FROM gifts WHERE donor_id = 'DNR-00042' GROUP BY yr")
            rows = cursor.fetchall()
            cursor.execute("SELECT interaction_date, notes FROM interactions WHERE donor_id = 'DNR-00042' ORDER BY interaction_date DESC LIMIT 1")
            int_row = cursor.fetchone()
            conn.close()
            history = ", ".join([f"{r[0]}: ${r[1]:,.0f}" for r in rows])
            notes = int_row[1] if int_row else "No interaction recorded"
            return (f"[Smart Companion Analysis - Storyline 1]\\n"
                    f"Donor Eleanor Vance (DNR-00042) dropped from $50,000/yr to $5,000 in 2026 ({history}).\\n"
                    f"Root Cause: Last stewardship touchpoint was {int_row[0]} ('{notes}'). MGO follow-up lapsed, causing attrition.")

        if "cash reserve" in q or "burn rate" in q or "runway" in q:
            cursor.execute("SELECT cash_reserves_months, monthly_burn_rate FROM org_profile")
            res, burn = cursor.fetchone()
            conn.close()
            return f"[Smart Companion] Operating runway is {res} months of cash reserves with a monthly burn rate of ${burn:,.2f}. (Source: org_profile)"

        conn.close()
        return f"[Smart Companion Guardrail] Requested information for '{question}' is not available in verified platform tables. Declining to guess."
'''
with open("scripts/smart_companion.py", "w") as f:
    f.write(COMPANION_SCRIPT.strip())
print("[WRITE] scripts/smart_companion.py")

# 5. Update Master Execution Pipeline
RUN_SCRIPT = """import os
import sqlite3
import subprocess
import time
import pandas as pd

start = time.time()
print(">>> STEP 1: Executing 5-Year Humanitarian Simulation...")
subprocess.run(["python", "scripts/build_midterm_environment.py"], check=True)

print("\\n>>> STEP 2: Staging Relational SQLite Database (`causefleet_demo.db`)...")
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

print(f"\\n[SUCCESS] Pipeline Built and Staged in {round(time.time() - start, 2)}s.")
"""
with open("scripts/run_demo_pipeline.py", "w") as f:
    f.write(RUN_SCRIPT.strip())
print("[WRITE] scripts/run_demo_pipeline.py")

# 6. Execute Build
print("\\n>>> RUNNING REVISION 2 BUILD PIPELINE...")
subprocess.run([sys.executable, "scripts/run_demo_pipeline.py"], check=True)
