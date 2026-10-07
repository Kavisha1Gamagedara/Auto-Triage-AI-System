import csv
import os
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "data")
PARTS_CSV = os.path.join(DATA_DIR, "parts.csv")

def main():
    if not os.path.exists(PARTS_CSV):
        print("parts.csv not found")
        return

    with open(PARTS_CSV, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if "price_updated" not in fieldnames:
            fieldnames = fieldnames + ["price_updated", "currency", "supplier"]
        
        rows = list(reader)

    suppliers = ["Global Auto Parts", "Lanka Motors", "OEM Direct", "City Spares", "National Auto"]
    base_date = datetime(2024, 1, 1)

    for row in rows:
        if "price_updated" not in row or not row["price_updated"]:
            random_days = random.randint(0, 180)
            row["price_updated"] = (base_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
        if "currency" not in row or not row["currency"]:
            row["currency"] = "LKR"
        if "supplier" not in row or not row["supplier"]:
            row["supplier"] = random.choice(suppliers)

    with open(PARTS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated {len(rows)} rows in parts.csv")

if __name__ == "__main__":
    main()
