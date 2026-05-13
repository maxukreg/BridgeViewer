import csv
import os
import sys
import argparse
from pathlib import Path


def getdefaultbasedir() -> str:
    """Return default Sheets directory dynamically one level up from script."""
    pathfile = Path(__file__)
    return str(pathfile.parent.parent)


def parsedealheaderrow(row):
    """Parse a deal header row and return group, deal or None if not a header.
    Supports both:
    - Group, 28, Deal, 33, ...
    - Group,28,Deal,33,... packed into a single cell
    """
    if not row:
        return None

    # Single-cell style: Group,28,Deal,33,...
    if len(row) == 1 and isinstance(row[0], str) and "," in row[0]:
        row0 = row[0].strip()
        parts = [p.strip() for p in row0.split(",")]
        if len(parts) >= 4 and parts[0] == "Group" and parts[2] == "Deal":
            try:
                group = parts[1]
                deal = parts[3]
                return group, deal
            except (ValueError, IndexError):
                return None

    # Multi-cell style: Group, 28, Deal, 33, ...
    if len(row) >= 4 and row[0].strip() == "Group" and row[2].strip() == "Deal":
        try:
            group = row[1].strip()
            deal = row[3].strip()
            return group, deal
        except (ValueError, IndexError):
            return None

    return None


def readnextdatalines(reader, numlines):
    """Read the next numlines rows from the CSV reader."""
    datalines = []
    for _ in range(numlines):
        try:
            datalines.append(next(reader))
        except StopIteration:
            break
    return datalines


def updatedealinhandsfromai(handsfromaipath, targetgroup, targetdeal, newdatalines):
    """Update a specific deal in HandsFromAI.csv.
    If placeholder lines don't exist, they are inserted.
    """
    with open(handsfromaipath, "r", newline="") as file:
        lines = list(csv.reader(file))

    dealstartline = None
    for i, row in enumerate(lines):
        dealkey = parsedealheaderrow(row)
        if dealkey and dealkey == (targetgroup, targetdeal):
            dealstartline = i
            break

    if dealstartline is None:
        return False  # Deal header not found

    # Determine if we have enough lines to overwrite
    # We need 8 lines after the header for cards/sequences
    # and 4 lines after that for bidding/players.

    # We remove any existing data lines that might be there (up to 8)
    # to ensure we don't just shift old data down.
    # However, to be safe and simple:
    # Delete the next 8 lines if they are NOT headers, then insert.

    current_idx = dealstartline + 1
    # Optimization: Check if the lines following the header are empty or
    # belong to the same deal block before deleting.
    for _ in range(8):
        if current_idx < len(lines):
            # If we hit another header, stop deleting
            if parsedealheaderrow(lines[current_idx]):
                break
            lines.pop(current_idx)
        else:
            break

    # Now insert the 8 new lines from batchOutput.csv
    for i, newline in enumerate(reversed(newdatalines[:8])):
        lines.insert(dealstartline + 1, newline)

    with open(handsfromaipath, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(lines)

    return True


# True only if no new errors added for this deal


def validate_deal_data(group, deal, datalines, validation_errors):
    """
    Validate one deal's 8 data rows from batchOutput.csv (already parsed by csv.reader).

    Layout per deal (after the header):
      index 0: North cards
      index 1: North sequence
      index 2: East cards
      index 3: East sequence
      index 4: South cards
      index 5: South sequence
      index 6: West cards
      index 7: West sequence
    """

    if len(datalines) != 8:
        validation_errors.append(
            f"Deal {deal}: Expected 8 data lines, got {len(datalines)}"
        )
        return False

    # ----- CARD VALIDATION -----
    card_indices = [0, 2, 4, 6]  # N, E, S, W
    directions = ["N", "E", "S", "W"]
    card_owner = {}  # card -> first direction seen
    duplicate_details = []

    for i, idx in enumerate(card_indices):
        row = datalines[idx]

        # Handle the “one big cell with commas” case:
        # ['KH,7H,6H,...'] -> ['KH','7H','6H',...]
        if len(row) == 1:
            row = [c.strip() for c in row[0].split(",")]

        for raw_card in row:
            card = raw_card.strip()
            if not card:
                continue
            if card in card_owner:
                first = card_owner[card]
                descr = f"{card} ({first} & {directions[i]})"
                if descr not in duplicate_details:
                    duplicate_details.append(descr)
            else:
                card_owner[card] = directions[i]

    if len(card_owner) != 52:
        if duplicate_details:
            dup_text = ", ".join(duplicate_details[:5])
            if len(duplicate_details) > 5:
                dup_text += f" +{len(duplicate_details) - 5} more"
            validation_errors.append(f"Deal {deal}: Dupl — {dup_text}")
        else:
            validation_errors.append(
                f"Deal {deal}: {len(card_owner)} unique cards (missing {52 - len(card_owner)})"
            )

    # ----- SEQUENCE VALIDATION -----
    seq_indices = [1, 3, 5, 7]  # N, E, S, W sequences
    seq_directions = ["N", "S", "E", "W"]

    for i, idx in enumerate(seq_indices):
        row = datalines[idx]

        # Handle the “one big cell with commas” case for sequences as well
        if len(row) == 1:
            row = [x.strip() for x in row[0].split(",")]

        try:
            nums = [int(x.strip()) for x in row if x.strip()]
        except ValueError:
            validation_errors.append(
                f"Deal {deal}: Invalid numbers in {seq_directions[i]} seq"
            )
            continue

        expected = set(range(1, 14))
        actual = set(nums)
        if actual != expected:
            missing = expected - actual
            extra = actual - expected
            parts = []
            if missing:
                parts.append(f"missing {sorted(missing)}")
            if extra:
                parts.append(f"extra {sorted(extra)}")
            validation_errors.append(
                f"Deal {deal}: {seq_directions[i]} seq — {', '.join(parts)}"
            )

    return True


def show_validation_summary(validation_errors):
    """Print validation errors to stdout with a parseable prefix.
    The dashboard reads these from the script output and displays them
    as an inline error panel. The tkinter popup is not used when errors
    are present — stdout is the single source of truth for all callers.
    """
    if not validation_errors:
        print("VALIDATION_OK: All deals passed validation!")
        return

    print(f"VALIDATION_ERROR_COUNT: {len(validation_errors)}")
    for err in validation_errors:
        print(f"VALIDATION_ERROR: {err}")


def processhandstemprecordbyrecord(handstemppath, handsfromaipath):
    """Process batchOutput.csv record by record, updating HandsFromAI.csv."""
    processedcount = 0
    skippedcount = 0
    errorcount = 0
    totalrows = 0
    validation_errors = []

    print("Processing batchOutput.csv record by record...")

    with open(handstemppath, "r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            totalrows += 1

            if not row or not any(cell.strip() for cell in row):
                continue  # Skip blank rows

            dealkey = parsedealheaderrow(row)
            if dealkey:
                group, deal = dealkey  # Deal header found

                datalines = readnextdatalines(reader, 8)
                if len(datalines) != 8:
                    print(
                        f"WARNING: Expected 8 data lines for Group {group}, Deal {deal}, got {len(datalines)}"
                    )
                    errorcount += 1
                    continue

                # Validate deal data BEFORE processing
                validate_deal_data(group, deal, datalines, validation_errors)

                # Continue processing regardless of validation
                success = updatedealinhandsfromai(
                    handsfromaipath, group, deal, datalines
                )
                if success:
                    processedcount += 1
                    print(f"Updated Group {group}, Deal {deal}")
                else:
                    skippedcount += 1
                    print(
                        f"SKIPPED: Group {group}, Deal {deal} not found in HandsFromAI.csv"
                    )

    print(f"Total rows read from batchOutput.csv: {totalrows}")

    # Show validation summary popup
    print("=" * 60)
    if validation_errors:
        print(f"Validation issues found: {len(validation_errors)}")
        show_validation_summary(validation_errors)
    else:
        print("All deals passed validation!")

    return processedcount, skippedcount, errorcount


def validatefiles(handstemppath, handsfromaipath):
    """Ensure both CSV files exist and are readable."""
    errors = []
    if not os.path.exists(handstemppath):
        errors.append(f"batchOutput.csv not found: {handstemppath}")
    if not os.path.exists(handsfromaipath):
        errors.append(f"HandsFromAI.csv not found: {handsfromaipath}")

    # Basic readability checks
    for pth, label in [
        (handstemppath, "batchOutput.csv"),
        (handsfromaipath, "HandsFromAI.csv"),
    ]:
        try:
            with open(pth, "r") as f:
                pass
        except Exception as e:
            errors.append(f"Cannot read {label}: {e}")

    return errors


def main():
    """Non-interactive entry point - Requires --group
    Optional --base-dir - Resolves ...Group{group}/CSV/batchOutput.csv, HandsFromAI.csv
    """
    print("CSV Deal Update Script - Record-by-Record, non-interactive")
    print("=" * 60)

    parser = argparse.ArgumentParser(
        description="Update HandsFromAI.csv with data from batchOutput.csv for a given group."
    )
    parser.add_argument(
        "--group",
        "-g",
        type=int,
        required=True,
        help="Group number (already established by the caller)",
    )
    parser.add_argument(
        "--base-dir",
        "-d",
        type=str,
        help="Base Sheets directory (defaults to parent of this script)",
    )
    args = parser.parse_args()

    # Validate group number
    if not (11 <= args.group <= 38):
        print(
            f"ERROR: Group number must be between 11 and 38, got {args.group}",
            file=sys.stderr,
        )
        sys.exit(1)

    basedir = args.base_dir if args.base_dir else getdefaultbasedir()
    groupdir = os.path.join(basedir, f"Group{args.group}")
    csvdir = os.path.join(groupdir, "CSV")  # Casing fixed as requested

    if not os.path.isdir(groupdir):
        print(
            f"ERROR: Group{args.group} directory does not exist: {groupdir}",
            file=sys.stderr,
        )
        sys.exit(1)
    if not os.path.isdir(csvdir):
        print(f"ERROR: Expected CSV folder not found: {csvdir}", file=sys.stderr)
        sys.exit(1)

    handstemppath = os.path.join(csvdir, "batchOutput.csv")
    handsfromaipath = os.path.join(csvdir, "HandsFromAI.csv")

    print(f"Group directory: {groupdir}")
    print(f"CSV directory: {csvdir}")
    print(f"batchOutput.csv: {handstemppath}")
    print(f"HandsFromAI.csv: {handsfromaipath}")
    print()

    # Match validation range used elsewhere (adjust if needed)
    print("Validating files...")
    validationerrors = validatefiles(handstemppath, handsfromaipath)
    if validationerrors:
        print("File validation failed:")
        for err in validationerrors:
            print(f" - {err}")
        sys.exit(1)

    try:
        processed, skipped, errors = processhandstemprecordbyrecord(
            handstemppath, handsfromaipath
        )
        print("=" * 60)
        print("PROCESSING COMPLETE")
        print(f"Updated deals: {processed}")
        print(f"Skipped deals (not found): {skipped}")
        print(f"Errors (structure issues): {errors}")

        sys.exit(0 if processed > 0 and errors == 0 else 1)
    except Exception as e:
        print(f"Processing failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
