"""
Generate a synthetic program-portfolio dataset for the Portfolio Health Dashboard.

Every record produced here is fabricated. No real organization, person, program,
or performance data is used, referenced, or reconstructed.

Usage:
    python generate_sample_data.py            # writes initiatives.csv
    python generate_sample_data.py --json     # also writes initiatives.json

The generator is seeded, so the output is byte-identical on every run. That keeps
the dashboard's committed data stable and reviewable in version control.
"""

import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

# Fixed snapshot date. Everything time-based is measured from here so the
# dashboard reads the same way a year from now as it does today.
AS_OF = date(2026, 6, 30)
SEED = 20260630
COUNT = 128

TEAMS = [
    "Analytics & Reporting",
    "Provider Engagement",
    "Member Experience",
    "Clinical Operations",
    "Data Governance",
    "Care Management",
    "Vendor & Delivery",
]

WORKSTREAMS = [
    "Gap Closure",
    "Data Integration",
    "Outreach Campaign",
    "Process Redesign",
    "Reporting & Insight",
    "Vendor Onboarding",
    "Compliance & Audit",
]

# Title fragments assembled combinatorially. Deliberately domain-flavored but
# generic — nothing here maps to a real program.
ACTIONS = [
    "Automate", "Consolidate", "Redesign", "Expand", "Standardize",
    "Migrate", "Pilot", "Retire", "Instrument", "Streamline",
]
OBJECTS = [
    "intake validation", "supplemental file submission", "outreach scheduling",
    "provider scorecard refresh", "chart retrieval workflow", "eligibility reconciliation",
    "measure specification library", "campaign attribution", "vendor SLA tracking",
    "care gap routing", "roster ingestion", "appeals turnaround reporting",
    "member contact preferences", "site-of-care analytics", "audit evidence collection",
    "quality dashboard distribution", "lab result normalization", "risk stratification inputs",
]
QUALIFIERS = [
    "", "", "", " (phase 2)", " for regional markets", " across delegated partners",
    " ahead of annual audit", " for the self-service layer",
]

# Fabricated owner names — common given names paired with common surnames.
FIRST = ["Dana", "Marcus", "Priya", "Elena", "Tobias", "Renee", "Omar", "Claire",
         "Devin", "Natalie", "Grant", "Simone", "Hugo", "Aisha", "Peter", "Lena",
         "Ravi", "Bea"]
LAST = ["Whitfield", "Okafor", "Ramnarine", "Castellanos", "Lindqvist", "Boateng",
        "Moreau", "Tanaka", "Delgado", "Novak", "Ferreira", "Halloran", "Sandoval",
        "Kowalski", "Adeyemi", "Vasquez"]


def classify(pct: int, days_since_update: int, due: date, complete: bool) -> str:
    """Derive status from the underlying facts rather than assigning it at random.

    The point of the dashboard is that status is *earned* by the data, not typed
    in by an owner who wants to look green.
    """
    if complete:
        return "Complete"
    if days_since_update >= 30:
        return "Stalled"
    days_to_due = (due - AS_OF).days
    if days_to_due < 0:
        return "At Risk"
    if days_to_due <= 21 and pct < 65:
        return "At Risk"
    if days_to_due <= 45 and pct < 35:
        return "At Risk"
    return "On Track"


def build() -> list[dict]:
    rng = random.Random(SEED)
    rows = []

    for i in range(1, COUNT + 1):
        team = rng.choice(TEAMS)
        workstream = rng.choice(WORKSTREAMS)
        title = (
            f"{rng.choice(ACTIONS)} {rng.choice(OBJECTS)}{rng.choice(QUALIFIERS)}"
        )
        owner = f"{rng.choice(FIRST)} {rng.choice(LAST)}"

        start = AS_OF - timedelta(days=rng.randint(10, 330))
        duration = rng.randint(90, 380)
        due = start + timedelta(days=duration)

        # Roughly 18% of the portfolio is finished.
        complete = rng.random() < 0.18
        if complete:
            pct = 100
            days_since_update = rng.randint(1, 45)
        else:
            # Progress loosely tracks elapsed time, with real-world slippage.
            elapsed = (AS_OF - start).days
            expected = min(95, max(3, int(100 * elapsed / duration)))
            pct = max(0, min(97, int(rng.gauss(expected * 0.85, 18))))
            # Most work is touched recently; a meaningful tail is not.
            days_since_update = int(
                rng.choice([
                    rng.randint(0, 7),
                    rng.randint(0, 14),
                    rng.randint(5, 25),
                    rng.randint(30, 120),
                ])
            )

        last_update = AS_OF - timedelta(days=days_since_update)
        status = classify(pct, days_since_update, due, complete)

        rows.append({
            "id": f"INI-{i:03d}",
            "title": title,
            "team": team,
            "workstream": workstream,
            "owner": owner,
            "status": status,
            "percent_complete": pct,
            "start_date": start.isoformat(),
            "due_date": due.isoformat(),
            "last_update": last_update.isoformat(),
            "days_since_update": days_since_update,
        })

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="also write initiatives.json")
    args = parser.parse_args()

    out_dir = Path(__file__).parent
    rows = build()
    fields = list(rows[0].keys())

    with open(out_dir / "initiatives.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    if args.json:
        with open(out_dir / "initiatives.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"Wrote {len(rows)} initiatives as of {AS_OF.isoformat()}")
    for status, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {status:<10} {n:>4}")


if __name__ == "__main__":
    main()
