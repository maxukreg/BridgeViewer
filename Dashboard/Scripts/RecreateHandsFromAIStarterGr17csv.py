import csv
import shutil
from pathlib import Path


def get_base_dir():
    # Resolves to the 'Sheets' directory from 'Scripts'
    return Path(__file__).resolve().parent.parent


def create_one_off_group_17():
    base_dir = get_base_dir()
    group_num = 17
    group_dir = base_dir / f"Group{group_num}"

    # Define hand range for odd group (1-32)
    start_id, end_id = 1, 32

    # 1. Create Folder Structure
    (group_dir / "CSV").mkdir(parents=True, exist_ok=True)
    (group_dir / "Booklet" / "Deals").mkdir(parents=True, exist_ok=True)
    (group_dir / "Booklet" / "Intro").mkdir(parents=True, exist_ok=True)
    (group_dir / "Lin").mkdir(parents=True, exist_ok=True)
    (group_dir / "images" / "ModScans").mkdir(parents=True, exist_ok=True)
    (group_dir / "images" / "OriginalScans").mkdir(parents=True, exist_ok=True)

    # 2. Create HandsFromAI.csv (Matches original script's naming)
    csv_dir = group_dir / "CSV"
    with open(csv_dir / "HandsFromAI.csv", "w", newline="") as f:
        writer = csv.writer(f)
        for deal_id in range(start_id, end_id + 1):
            writer.writerow(
                [
                    "Group",
                    group_num,
                    "Deal",
                    deal_id,
                    "Dealer",
                    "",
                    "Vul",
                    "",
                    "Contract",
                    "",
                ]
            )
            for _ in range(12):  # 8 for cards, 4 for players
                writer.writerow([])

    # 3. Create blank helper files
    (csv_dir / "HandsTemp.csv").touch()
    (csv_dir / "bidding.csv").touch()

    # 4. Copy and Replace in Deals JS Template
    templates_dir = base_dir / "Templates"
    src = templates_dir / "textTemplate1.js"  # Template for odd groups
    dst = group_dir / "Booklet" / f"deals{group_num}.js"

    if src.exists():
        shutil.copy2(src, dst)
        with open(dst, "r", encoding="utf-8") as f:
            content = (
                f.read()
                .replace("Group37", f"Group{group_num}")
                .replace("group37", f"group{group_num}")
            )
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"SUCCESS: Group 17 created at {group_dir}")


if __name__ == "__main__":
    create_one_off_group_17()
