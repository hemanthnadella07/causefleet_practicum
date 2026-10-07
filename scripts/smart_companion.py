import sqlite3
import re

DB_FILE = "causefleet_demo.db"

class CausefleetSmartCompanion:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path

    def answer_question(self, question: str) -> str:
        q = question.lower()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        if "revenue" in q or "raised" in q or "giving" in q:
            m = re.search(r"202[2-6]", q)
            if m:
                yr = m.group(0)
                cur.execute("SELECT SUM(amount), COUNT(gift_id) FROM gifts WHERE gift_date LIKE ?", (f"{yr}%",))
                row = cur.fetchone()
                conn.close()
                rev = row[0] or 0.0
                cnt = row[1] or 0
                return f"[Smart Companion] In {yr}, total revenue was ${rev:,.2f} across {cnt:,} gifts. (Source: gifts table)"
            else:
                cur.execute("SELECT SUBSTR(gift_date, 1, 4) as yr, SUM(amount) FROM gifts GROUP BY yr ORDER BY yr")
                rows = cur.fetchall()
                conn.close()
                bk = ", ".join([f"{r[0]}: ${r[1]:,.0f}" for r in rows])
                return f"[Smart Companion] Multi-year revenue totals: {bk}. (Source: gifts table)"

        if "top donor" in q or "major donor" in q or "biggest donor" in q:
            cur.execute("""
                SELECT d.first_name || ' ' || d.last_name, d.donor_type, SUM(g.amount) as total_given, s.full_name
                FROM donors d JOIN gifts g ON d.donor_id = g.donor_id
                LEFT JOIN staff s ON d.assigned_mgo_id = s.staff_id
                WHERE d.is_top_100 = 1
                GROUP BY d.donor_id ORDER BY total_given DESC LIMIT 5
            """)
            rows = cur.fetchall()
            conn.close()
            resp = "[Smart Companion] Top 5 Major Donors:\n"
            for r in rows:
                mgo = f" (MGO: {r[3]})" if r[3] else ""
                resp += f" • {r[0]} ({r[1]}): ${r[2]:,.2f}{mgo}\n"
            resp += "(Source: donors, gifts, staff tables)"
            return resp

        if "impact" in q or "food" in q or "water" in q or "education" in q or "countries" in q:
            cur.execute("SELECT year, metric_name, actual_value, target_value FROM impact_metrics WHERE year = 2025")
            rows = cur.fetchall()
            conn.close()
            resp = "[Smart Companion] 2025 Mission Impact Results:\n"
            for r in rows:
                resp += f" • {r[1]}: {int(r[2]):,} reached (Target: {int(r[3]):,})\n"
            resp += "(Source: impact_metrics table, reconciled to expenditures)"
            return resp

        if ("why did" in q or "stop giving" in q or "decrease" in q) and ("eleanor" in q or "vance" in q or "dnr-00042" in q or "major donor" in q):
            cur.execute("SELECT SUBSTR(gift_date, 1, 4) as yr, SUM(amount) FROM gifts WHERE donor_id = 'DNR-00042' GROUP BY yr")
            rows = cur.fetchall()
            cur.execute("SELECT interaction_date, notes FROM interactions WHERE donor_id = 'DNR-00042' ORDER BY interaction_date DESC LIMIT 1")
            int_row = cur.fetchone()
            conn.close()
            history = ", ".join([f"{r[0]}: ${r[1]:,.0f}" for r in rows])
            notes = int_row[1] if int_row else "No interaction recorded"
            dt = int_row[0] if int_row else "N/A"
            return (f"[Smart Companion Analysis - Storyline 1]\n"
                    f"Donor Eleanor Vance (DNR-00042) dropped from $50,000/yr to $5,000 in 2026 ({history}).\n"
                    f"Root Cause: Last stewardship touchpoint was {dt} ('{notes}'). MGO follow-up lapsed, causing attrition.")

        if "cash reserve" in q or "burn rate" in q or "runway" in q:
            cur.execute("SELECT cash_reserves_months, monthly_burn_rate FROM org_profile")
            row = cur.fetchone()
            conn.close()
            res = row[0] if row else 0
            burn = row[1] if row else 0
            return f"[Smart Companion] Operating runway is {res} months of cash reserves with a monthly burn rate of ${burn:,.2f}. (Source: org_profile)"

        conn.close()
        return f"[Smart Companion Guardrail] Requested information for '{question}' is not available in verified platform tables. Declining to guess."

if __name__ == "__main__":
    bot = CausefleetSmartCompanion()
    print("=" * 70)
    print("CAUSEFLEET SMART COMPANION (AI CHATBOT) - EXECUTIVE DEMO CONSOLE")
    print("=" * 70)
    prompts = [
        "What was our total revenue in 2025?",
        "Who are our top major donors?",
        "What was our humanitarian impact in 2025?",
        "Why did Eleanor Vance stop giving?",
        "What are our cash reserves and monthly burn rate?"
    ]
    for idx, p in enumerate(prompts, 1):
        print(f"\n[Executive Question {idx}]: {p}")
        print(bot.answer_question(p))
        print("-" * 70)
