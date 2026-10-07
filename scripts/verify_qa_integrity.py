import sys
import pandas as pd

DATA_DIR = "data"
donors = pd.read_csv(f"{DATA_DIR}/donors.csv")
gifts = pd.read_csv(f"{DATA_DIR}/gifts.csv")
campaigns = pd.read_csv(f"{DATA_DIR}/campaigns.csv")

assert len(gifts[~gifts['donor_id'].isin(donors['donor_id'])]) == 0, "Foreign key failure: gifts -> donors"
assert len(gifts[~gifts['campaign_id'].isin(campaigns['campaign_id'])]) == 0, "Foreign key failure: gifts -> campaigns"

merged = gifts.merge(donors, on="donor_id")
assert len(merged[merged['gift_date'] < merged['created_at']]) == 0, "Date paradox: gift before donor creation"

assert gifts['amount'].isnull().sum() == 0 and (gifts['amount'] <= 0).sum() == 0, "Financial reconciliation failure"
assert len(donors[donors['is_synthetic_label'] != True]) == 0, "Privacy failure: unflagged records"

s1 = gifts[gifts['donor_id'] == 'DNR-00042']
assert s1[s1['gift_date'].str.startswith('2025')]['amount'].sum() == 50000.0, "Storyline 1 baseline mismatch"
assert s1[s1['gift_date'].str.startswith('2026')]['amount'].sum() == 5000.0, "Storyline 1 drop mismatch"

print("[PASS] QA Audit Suite: 100% assertions satisfied.")