import argparse
import shutil
import sys
from pathlib import Path


def get_default_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def create_deals_js(group_num: int, base_dir: Path) -> Path:
    if not (11 <= group_num <= 38):
        raise ValueError("Group number must be between 11 and 38")

    templates_dir = base_dir / "Templates"
    group_dir = base_dir / f"Group{group_num}"
    deals_dir = group_dir / "Booklet" / "Deals"
    deals_dir.mkdir(parents=True, exist_ok=True)

    if group_num % 2 == 1:
        template_file = "textTemplate1.js"
        old_patterns = ["Group37", "group37", "_group37"]
    else:
        template_file = "textTemplate2.js"
        old_patterns = ["Group38", "group38", "_group38"]

    src = templates_dir / template_file
    dst = deals_dir / f"deals{group_num}.js"

    if not src.exists():
        raise FileNotFoundError(f"Template file not found: {src}")

    shutil.copy2(src, dst)

    contents = dst.read_text(encoding="utf-8")
    for old in old_patterns:
        new = old[:-2] + str(group_num)
        contents = contents.replace(old, new)
    dst.write_text(contents, encoding="utf-8")

    return dst


def main():
    parser = argparse.ArgumentParser(
        description="Create only dealsNN.js inside GroupNN/Booklet/Deals"
    )
    parser.add_argument(
        "--group", "-g", type=int, required=True, help="Group number (11-38)"
    )
    parser.add_argument(
        "--base-dir",
        "-d",
        type=str,
        default=None,
        help="Base directory containing Templates and GroupNN folders",
    )
    args = parser.parse_args()

    try:
        base_dir = Path(args.base_dir) if args.base_dir else get_default_base_dir()
        created_file = create_deals_js(args.group, base_dir)
        print(f"SUCCESS: Created {created_file}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
