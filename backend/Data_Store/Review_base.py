import os
import json

# Root output directory
OUTPUT_DIR = "output/Domain2"

# Final merged file
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Review_base.json")

merged_data = []

# Sort folders so Run1, Run2, Run3...
run_folders = sorted(
    [d for d in os.listdir(OUTPUT_DIR)
     if os.path.isdir(os.path.join(OUTPUT_DIR, d))]
)

for folder in run_folders:
    json_path = os.path.join(OUTPUT_DIR, folder, "base2.json")

    if not os.path.exists(json_path):
        print(f"Skipping {folder} (base2.json not found)")
        continue

    print(f"Reading {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

        if isinstance(data, list):
            merged_data.extend(data)
        else:
            merged_data.append(data)

# Save merged JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(merged_data, f, indent=4, ensure_ascii=False)

print(f"\nMerged {len(merged_data)} records.")
print(f"Saved to: {OUTPUT_FILE}")