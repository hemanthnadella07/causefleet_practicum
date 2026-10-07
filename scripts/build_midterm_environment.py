import os
import json
import random
from datetime import datetime
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

pd.DataFrame([{
    "org_id": cfg["org_id"],
    "name": cfg["org_name"],
    "sector": cfg["sector"],
    "annual_budget": cfg["annual_target"],
    "fiscal_year_start": "2023-01-01",
    "is_synthetic_label": True
}]).to_csv(f"{DATA_DIR}/org_profile.csv", index=False)

pd.DataFrame([
    {"staff_id": "STF-01", "org_id": cfg["org_id"], "full_name": "Sarah Jenkins", "title": "Director of Development", "email": "synthetic.sjenkins@demo-causefleet.org", "role": "Executive"},
    {"staff_id": "STF-02", "org_id": cfg["org_id"], "full_name": "Marcus Vance", "title": "Major Gifts Officer", "email": "synthetic.mvance@demo-causefleet.org", "role": "Fundraiser"},
    {"staff_id": "STF-03", "org_id": cfg["org_id"], "full_name": "Elena Rostova", "title": "Annual Giving Specialist", "email": "synthetic.erostova@demo-causefleet.org", "role": "Coordinator"}
]).to_csv(f"{DATA_DIR}/staff.csv", index=False)

pd.DataFrame([
    {"campaign_id": "CMP-2023-ANN", "org_id": cfg["org_id"], "name": "2023 Annual Campaign", "goal_amount": 25000000.0, "start_date": "2023-01-01", "end_date": "2023-12-31", "channel": "Omnichannel"},
    {"campaign_id": "CMP-2024-ANN", "org_id": cfg["org_id"], "name": "2024 Annual Campaign", "goal_amount": 27000000.0, "start_date": "2024-01-01", "end_date": "2024-12-31", "channel": "Omnichannel"},
    {"campaign_id": "CMP-2025-ANN", "org_id": cfg["org_id"], "name": "2025 Annual Campaign", "goal_amount": 29000000.0, "start_date": "2025-01-01", "end_date": "2025-12-31", "channel": "Omnichannel"},
    {"campaign_id": cfg["storylines"]["gala_campaign_id"], "org_id": cfg["org_id"], "name": "2025 Fall Hope Gala", "goal_amount": 2000000.0, "start_date": "2025-09-01", "end_date": "2025-10-31", "channel": "Special Event"},
    {"campaign_id": "CMP-2026-ANN", "org_id": cfg["org_id"], "name": "2026 Building Tomorrow", "goal_amount": 30000000.0, "start_date": "2026-01-01", "end_date": "2026-12-31", "channel": "Omnichannel"}
]).to_csv(f"{DATA_DIR}/campaigns.csv", index=False)

pd.DataFrame([
    {"goal_id": "GL-01", "campaign_id": "CMP-2025-ANN", "target_metric": "Total Revenue", "target_value": 29000000.0, "deadline": "2025-12-31"},
    {"goal_id": "GL-02", "campaign_id": cfg["storylines"]["gala_campaign_id"], "target_metric": "Event Revenue", "target_value": 2000000.0, "deadline": "2025-10-31"},
    {"goal_id": "GL-03", "campaign_id": "CMP-2026-ANN", "target_metric": "Total Revenue", "target_value": 30000000.0, "deadline": "2026-12-31"}
]).to_csv(f"{DATA_DIR}/goals.csv", index=False)

pd.DataFrame([{
    "event_id": "EVT-2025-01",
    "campaign_id": cfg["storylines"]["gala_campaign_id"],
    "event_name": "Annual Hope Gala Dinner",
    "event_date": "2025-10-15",
    "ticket_price": 250.00
}]).to_csv(f"{DATA_DIR}/events.csv", index=False)

n_donors = cfg["donor_population"]
p = cfg["pareto_distribution"]
tiers = np.random.choice(["Small", "Mid", "Major"], size=n_donors, p=[p["small_tier_pct"], p["mid_tier_pct"], p["major_tier_pct"]])

donors = []
for i in range(1, n_donors + 1):
    did = f"DNR-{i:05d}"
    tier = tiers[i - 1]
    created = fake.date_between(start_date=datetime(2022, 1, 1), end_date=datetime(2025, 10, 1))
    donors.append({
        "donor_id": did,
        "org_id": cfg["org_id"],
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": f"synthetic.{did.lower()}@demo-causefleet.org",
        "phone": f"555-01{random.randint(10, 99)}",
        "address": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip_code": fake.zipcode(),
        "donor_tier": tier,
        "created_at": created.strftime("%Y-%m-%d"),
        "is_synthetic_label": True
    })

df_donors = pd.DataFrame(donors)

target_major_id = cfg["storylines"]["target_major_donor_id"]
df_donors.loc[df_donors["donor_id"] == target_major_id, "donor_tier"] = "Major"
df_donors.loc[df_donors["donor_id"] == target_major_id, "created_at"] = "2022-05-10"

gala_cohort = [f"DNR-{i:05d}" for i in range(150, 350)]
for did in gala_cohort:
    df_donors.loc[df_donors["donor_id"] == did, "donor_tier"] = "Small"
    df_donors.loc[df_donors["donor_id"] == did, "created_at"] = "2025-09-15"

df_donors.to_csv(f"{DATA_DIR}/donors.csv", index=False)

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
    tier = d["donor_tier"]
    created_dt = datetime.strptime(d["created_at"], "%Y-%m-%d")

    if did == target_major_id:
        gifts.append(add_gift(did, 50000.0, "2023-11-15", "CMP-2023-ANN", ch="Wire Transfer", is_pl=True))
        gifts.append(add_gift(did, 50000.0, "2024-11-10", "CMP-2024-ANN", ch="Wire Transfer", is_pl=True))
        gifts.append(add_gift(did, 50000.0, "2025-11-20", "CMP-2025-ANN", ch="Wire Transfer", is_pl=True))
        gifts.append(add_gift(did, 5000.0, "2026-06-12", "CMP-2026-ANN", ch="Online"))
        interactions.append({
            "interaction_id": f"INT-{int_id_ctr:06d}", "donor_id": did, "staff_id": "STF-02",
            "interaction_date": "2025-11-22", "type": "Major Donor Dinner",
            "notes": "Donor expressed interest in endowed scholarships."
        })
        int_id_ctr += 1
        continue

    if did in gala_cohort:
        gifts.append(add_gift(did, random.uniform(100, 250), "2025-10-15", cfg["storylines"]["gala_campaign_id"], ch="Event"))
        if random.random() < 0.10:
            gifts.append(add_gift(did, random.uniform(50, 150), "2026-04-12", "CMP-2026-ANN", ch="Online"))
        continue

    for yr in [2023, 2024, 2025, 2026]:
        yr_start = datetime(yr, 1, 1)
        if created_dt > datetime(yr, 12, 31):
            continue
        if tier == "Major":
            for _ in range(random.randint(1, 3)):
                amt = min(np.random.pareto(a=2.0) * 15000 + 10000, 150000)
                s_dt = max(created_dt, yr_start)
                e_dt = min(datetime(yr, 12, 28), datetime(2026, 9, 30))
                if s_dt > e_dt:
                    continue
                dt = fake.date_between(start_date=s_dt, end_date=e_dt)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Check", is_pl=True))
        elif tier == "Mid":
            for _ in range(random.randint(1, 3)):
                amt = random.uniform(500, 3000)
                s_dt = max(created_dt, yr_start)
                e_dt = min(datetime(yr, 12, 28), datetime(2026, 9, 30))
                if s_dt > e_dt:
                    continue
                dt = fake.date_between(start_date=s_dt, end_date=e_dt)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Credit Card"))
        else:
            if random.random() < 0.60:
                amt = random.uniform(25, 250)
                s_dt = max(created_dt, yr_start)
                e_dt = min(datetime(yr, 12, 28), datetime(2026, 9, 30))
                if s_dt > e_dt:
                    continue
                dt = fake.date_between(start_date=s_dt, end_date=e_dt)
                gifts.append(add_gift(did, amt, dt.strftime("%Y-%m-%d"), f"CMP-{yr}-ANN", ch="Online"))

pd.DataFrame(gifts).to_csv(f"{DATA_DIR}/gifts.csv", index=False)
pd.DataFrame(interactions).to_csv(f"{DATA_DIR}/interactions.csv", index=False)