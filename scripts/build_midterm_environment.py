import os
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
for m_idx, dt in enumerate(pd.date_range("2022-01-01", periods=58, freq="MS")):
    aud_months.append({
        "month_id": dt.strftime("%Y-%m"),
        "email_subscribers": int(85000 + m_idx * 750),
        "mailable_households": int(42000 + m_idx * 300),
        "social_followers": int(110000 + m_idx * 1200),
        "website_visitors": int(35000 + random.randint(1000, 8000)),
        "web_conversion_rate": round(random.uniform(0.018, 0.026), 4)
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