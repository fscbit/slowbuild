#!/usr/bin/env python3
"""CSV ⇄ JSON Converter. Drag a .csv → .json, or .json → .csv."""
import sys, os, json, csv

def csv_to_json(csv_path):
    output = csv_path.replace('.csv', '.json')
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(rows)} rows → {output}")

def json_to_csv(json_path):
    output = json_path.replace('.json', '.csv')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    if not data:
        print("❌ Empty data.")
        return
    keys = list(data[0].keys())
    with open(output, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ {len(data)} rows → {output}")

if __name__ == "__main__":
    files = sys.argv[1:]
    if not files:
        print("CSV ⇄ JSON Converter")
        print("  Drag .csv → gives .json")
        print("  Drag .json → gives .csv")
        sys.exit(1)
    for f in files:
        if not os.path.exists(f):
            print(f"⚠️  Not found: {f}")
            continue
        if f.endswith('.csv'):
            csv_to_json(f)
        elif f.endswith('.json'):
            json_to_csv(f)
        else:
            print(f"⚠️  Unsupported: {f}")
