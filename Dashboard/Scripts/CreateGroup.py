import csv
import shutil
import sys
import argparse
from pathlib import Path


def get_hand_range(group_num: int):
    """Return hand IDs range for group number."""
    return (1, 32) if group_num % 2 == 1 else (33, 64)


def get_default_base_dir():
    """Return Sheets directory where script is located."""
    # Script is in Sheets/Scripts/, so go up one level to Sheets/
    return Path(__file__).resolve().parent.parent


def create_hands_from_ai(csv_dir, group_num, start_id, end_id):
    """Create HandsFromAI.csv with header and 12 blank rows per deal."""
    file_path = csv_dir / "HandsFromAI.csv"
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        for deal_id in range(start_id, end_id + 1):
            # Header row
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
            # 8 blank rows
            for _ in range(8):
                writer.writerow([])
            # 4 blank rows (for players)
            for _ in range(4):
                writer.writerow([])


def create_booklet_subfolders_and_dealsjs(booklet_dir, group_num, templates_dir):
    """Create Booklet subfolders and fill dealsNN.js from template with replaced group numbers."""
    (booklet_dir / "Deals").mkdir(parents=True, exist_ok=True)
    (booklet_dir / "Intro").mkdir(parents=True, exist_ok=True)

    if group_num % 2 == 1:
        template_file = "textTemplate1.js"
        old_patterns = ["Group37", "group37", "_group37"]
    else:
        template_file = "textTemplate2.js"
        old_patterns = ["Group38", "group38", "_group38"]

    src = templates_dir / template_file
    dst = booklet_dir / "Deals" / f"deals{group_num}.js"

    if not src.exists():
        raise FileNotFoundError(f"Template file not found: {src}")

    shutil.copy2(src, dst)

    with open(dst, "r", encoding="utf-8") as infile:
        contents = infile.read()

    for old in old_patterns:
        new = old[:-2] + str(group_num)
        contents = contents.replace(old, new)

    with open(dst, "w", encoding="utf-8") as outfile:
        outfile.write(contents)


def create_group_structure(group_num: int, base_dir: Path = None):
    """Create folder structure and CSV skeletons for the group."""
    if not (11 <= group_num <= 38):
        raise ValueError("Group number must be between 11 and 38")

    # Use default base directory if none provided
    if base_dir is None:
        base_dir = get_default_base_dir()

    # DEBUG: Print diagnostic information
    print(f"DEBUG: __file__ = {__file__}")
    print(f"DEBUG: Path(__file__).resolve() = {Path(__file__).resolve()}")
    print(f"DEBUG: Path(__file__).resolve().parent = {Path(__file__).resolve().parent}")
    print(
        f"DEBUG: Path(__file__).resolve().parent.parent = {Path(__file__).resolve().parent.parent}"
    )
    print(f"DEBUG: base_dir = {base_dir}")
    print(f"DEBUG: base_dir type = {type(base_dir)}")

    group_dir = base_dir / f"Group{group_num}"
    print(f"DEBUG: group_dir = {group_dir}")
    print(
        f"DEBUG: Expected path should end with: ...\\Autobridge\\Sheets\\Group{group_num}"
    )

    if group_dir.exists():
        raise FileExistsError(
            f"Group{group_num} already exists at {group_dir}. Please choose a different group number."
        )

    # Create folders
    (group_dir / "Booklet").mkdir(parents=True, exist_ok=True)
    (group_dir / "CSV").mkdir(parents=True, exist_ok=True)
    (group_dir / "Lin").mkdir(parents=True, exist_ok=True)
    (group_dir / "images").mkdir(parents=True, exist_ok=True)
    (group_dir / "images" / "ModScans").mkdir(parents=True, exist_ok=True)
    (group_dir / "images" / "OriginalScans").mkdir(parents=True, exist_ok=True)

    start_id, end_id = get_hand_range(group_num)
    csv_dir = group_dir / "CSV"

    # Create requested HandsFromAI.csv (12 blank lines)
    create_hands_from_ai(csv_dir, group_num, start_id, end_id)

    # Populate dealsNN.js from template
    templates_dir = base_dir / "Templates"
    create_booklet_subfolders_and_dealsjs(
        group_dir / "Booklet", group_num, templates_dir
    )

    return group_dir


def main():
    """Main function to handle command line execution."""
    parser = argparse.ArgumentParser(
        description="Create new group structure and skeleton files"
    )
    parser.add_argument(
        "--group", "-g", type=int, required=True, help="Group number (11-38)"
    )
    parser.add_argument(
        "--base-dir",
        "-d",
        type=str,
        help="Base directory for Sheets (optional, uses default if not provided)",
    )
    args = parser.parse_args()

    # DEBUG: Print what arguments were received
    print(f"DEBUG MAIN: args.group = {args.group}")
    print(f"DEBUG MAIN: args.base_dir = {args.base_dir}")

    try:
        # Validate group number
        if not (11 <= args.group <= 38):
            print(
                f"ERROR: Group number must be between 11 and 38, got {args.group}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Determine base directory
        base_dir = Path(args.base_dir) if args.base_dir else get_default_base_dir()

        # DEBUG: Print the base_dir being used
        print(f"DEBUG MAIN: base_dir (calculated) = {base_dir}")
        print(f"DEBUG MAIN: base_dir.exists() = {base_dir.exists()}")

        # Check if group already exists
        group_dir = base_dir / f"Group{args.group}"
        print(f"DEBUG MAIN: group_dir (for existence check) = {group_dir}")
        print(f"DEBUG MAIN: group_dir.exists() = {group_dir.exists()}")

        if group_dir.exists():
            print(
                f"ERROR: Group{args.group} already exists at {group_dir}",
                file=sys.stderr,
            )
            print("Please choose a different group number.", file=sys.stderr)
            sys.exit(1)

        # Create the group structure
        created_dir = create_group_structure(args.group, base_dir)

        # Success message
        print(
            f"SUCCESS: Group {args.group} structure created successfully at {created_dir}"
        )

    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
