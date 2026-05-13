import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from datetime import datetime
from pathlib import Path
import re


def extract_number_from_filename(filename):
    """Extract the number from parentheses in the filename for proper sorting"""
    match = re.search(r"\((\d+)\)", filename)
    return int(match.group(1)) if match else 0


def crop_rotate_save(image_path, crop_areas):
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    cropped_images = {}

    with Image.open(image_path) as img:
        for name, (x, y, w, h, rotation) in crop_areas.items():
            cropped = img.crop((x, y, x + w, y + h))
            if rotation:
                cropped = cropped.rotate(rotation, expand=True)
            cropped_images[name] = cropped

    return cropped_images, base_name


def split_vertical_hand_crop(x, y, w, h, rotation):
    """
    Split a vertical hand crop (East/West column) into two parts along height:
    top ~55% (about 7 cards), bottom ~45% (about 6 cards).
    This is used for E and W, which are vertical strips rotated by 90/270 degrees.
    """
    h1 = int(h * 0.55)
    overlap = int(h * 0.02)

    y1 = y
    y2 = y + h1 - overlap
    h2 = (y + h) - y2

    part1 = (x, y1, w, h1, rotation)
    part2 = (x, y2, w, h2, rotation)
    return part1, part2


def split_hand_crop(x, y, w, h, rotation):
    w1 = int(w * 0.50)
    overlap = int(w * 0.01)
    x1 = x
    x2 = x + w1 - overlap
    w2 = (x + w) - x2
    return (x1, y, w1, h, rotation), (x2, y, w2, h, rotation)


def build_split_crop_areas(base_crop_areas):
    """
    Given base crop_areas {'N': (...), 'S': (...), 'E': (...), 'W': (...)},
    return a dict with eight areas:
        'N1','N2','S1','S2','E1','E2','W1','W2'

    N and S are horizontal bands, so we split them along width.
    E and W are vertical strips (rotated 90/270 deg), so we split them along height.
    """
    split_areas = {}

    for key in ["N", "S", "E", "W"]:
        x, y, w, h, rot = base_crop_areas[key]

        if key in ("N", "S"):
            # Horizontal hands: split along width (left/right)
            (x1, y1, w1, h1, r1), (x2, y2, w2, h2, r2) = split_hand_crop(
                x, y, w, h, rot
            )
        else:
            # Vertical hands (E/W): split along height (top/bottom)
            (x1, y1, w1, h1, r1), (x2, y2, w2, h2, r2) = split_vertical_hand_crop(
                x, y, w, h, rot
            )

        split_areas[f"{key}1"] = (x1, y1, w1, h1, r1)
        split_areas[f"{key}2"] = (x2, y2, w2, h2, r2)

    return split_areas


def get_hand_range(group_num):
    """Return hand IDs range for group number."""
    return (1, 32) if group_num % 2 == 1 else (33, 64)


def find_highest_deal_number(directory, group_number):
    """Find the highest deal number in existing m-{group}-{deal}.png files."""
    highest = 0
    pattern = f"m-{group_number}-"

    if not os.path.exists(directory):
        return highest

    for filename in os.listdir(directory):
        if filename.startswith(pattern) and filename.lower().endswith(".png"):
            # Extract deal number from m-{group}-{deal}.png
            try:
                deal_part = filename[len(pattern) :].split(".")[0]
                deal_num = int(deal_part)
                highest = max(highest, deal_num)
            except (ValueError, IndexError):
                continue

    print(f"DEBUG: Highest existing deal number found: {highest}")
    return highest


def preprocess_scan_files(input_dir, group_number):
    """Rename Scan_ files to m-{group}-{deal}.png format before processing."""
    print(f"\n=== PREPROCESSING: Renaming Scan_ files ===")

    if not os.path.exists(input_dir):
        print(f"WARNING: Input directory does not exist: {input_dir}")
        return 0

    # Find all Scan_ files
    scan_files = [
        f
        for f in os.listdir(input_dir)
        if f.startswith("Scan_") and f.lower().endswith(".png")
    ]

    if not scan_files:
        print("No Scan_ files found to rename")
        return 0

    # Sort files by parentheses number for proper ordering
    scan_files.sort(key=extract_number_from_filename)
    print(f"Found {len(scan_files)} Scan_ files to rename")

    # Get expected deal range for this group
    start_deal, end_deal = get_hand_range(group_number)
    expected_count = end_deal - start_deal + 1

    # Find highest existing deal number
    highest_existing = find_highest_deal_number(input_dir, group_number)

    # Determine starting deal number
    if highest_existing >= start_deal:
        # Start from next available number after highest existing
        next_deal = highest_existing + 1
        print(
            f"Found existing files up to deal {highest_existing}, starting from deal {next_deal}"
        )
    else:
        # Start from the beginning of the range
        next_deal = start_deal
        print(f"No existing files found, starting from deal {next_deal}")

    # Check count vs expected
    if len(scan_files) != expected_count:
        print(
            f"WARNING: Found {len(scan_files)} Scan_ files, but expected {expected_count} deals ({start_deal}-{end_deal}) for Group {group_number}"
        )
        print("Continuing with available files...")

    # Rename files
    renamed_count = 0
    for i, old_filename in enumerate(scan_files):
        deal_number = next_deal + i

        # Check if we're going beyond expected range
        if deal_number > end_deal:
            print(
                f"WARNING: Deal number {deal_number} exceeds expected range ({start_deal}-{end_deal}) for Group {group_number}"
            )
            print("Continuing anyway...")

        old_path = os.path.join(input_dir, old_filename)
        new_filename = f"m-{group_number}-{deal_number}.png"
        new_path = os.path.join(input_dir, new_filename)

        try:
            # Check if target file already exists
            if os.path.exists(new_path):
                print(
                    f"WARNING: Target file {new_filename} already exists, skipping {old_filename}"
                )
                continue

            os.rename(old_path, new_path)
            print(f"Renamed: {old_filename} → {new_filename}")
            renamed_count += 1

        except Exception as e:
            print(f"ERROR renaming {old_filename}: {str(e)}")
            continue

    print(f"Preprocessing complete: {renamed_count} files renamed")
    return renamed_count


def extract_deal_number(filename):
    """Extract deal number from filename with enhanced debugging."""
    print(f"DEBUG: Analyzing filename: '{filename}'")

    # First, try the original pattern: number right before .png
    match = re.search(r"-(\d+)\.png", filename, re.IGNORECASE)
    if match:
        deal_number = match.group(1)
        print(f"DEBUG: Original pattern matched - extracted: {deal_number}")
        return deal_number

    # Try alternative patterns based on common naming conventions
    patterns = [
        (r"(\d+)\.png", "number at end before .png"),
        (r"-(\d+)-", "number between dashes"),
        (r"s-(\d+)", "number after s-"),
        (r"deal[\s-_]*(\d+)", 'number after "deal"'),
        (r"(\d+)", "any number in filename"),
    ]

    for pattern, description in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            deal_number = match.group(1)
            print(
                f"DEBUG: Alternative pattern '{description}' matched - extracted: {deal_number}"
            )
            return deal_number

    print(f"WARNING: Could not extract deal number from '{filename}' using any pattern")
    return "Unknown"


def add_text_to_image(image, text):
    text_height = 40
    new_img = Image.new("RGB", (image.width, image.height + text_height), color="white")
    new_img.paste(image, (0, text_height))

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    text_width = draw.textlength(text, font=font)
    text_position = ((new_img.width - text_width) // 2, 5)
    draw.text(text_position, text, fill="black", font=font)

    return new_img


def add_header_to_image(image, group_number, deal_number):
    """Add header text with Group and Deal Number."""
    print(f"DEBUG: Creating header with Group={group_number}, Deal={deal_number}")

    header_height = 20
    new_img = Image.new(
        "RGB", (image.width, image.height + header_height), color="white"
    )
    new_img.paste(image, (0, header_height))

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    header_text = f"Group {group_number} - Deal {deal_number}"
    print(f"DEBUG: Header text will be: '{header_text}'")

    text_width = draw.textlength(header_text, font=font)
    text_position = ((new_img.width - text_width) // 2, 5)
    draw.text(text_position, header_text, fill="black", font=font)

    return new_img


def merge_ns_ew_images(
    cropped_images, output_dir, base_output_name, group_number, deal_number
):
    """
    Build two pages:
      - North/South page: N1, N2, S1, S2 -> m-{group}-{deal}-NS.png
      - East/West page: E1, E2, W1, W2 -> m-{group}-{deal}-EW.png
    """

    def stack_hand_parts(part1, part2, label_text):
        combined_height = part1.height + part2.height
        max_width = max(part1.width, part2.width)

        tmp = Image.new("RGB", (max_width, combined_height), color="white")
        y_off = 0
        tmp.paste(part1, (0, y_off))
        y_off += part1.height
        tmp.paste(part2, (0, y_off))

        return add_text_to_image(tmp, label_text)

    # --- FIX: CLEAN ARTEFACTS FROM SOUTH HAND (S1) ---
    # The artifact is on the far right of the top half of the South hand (S1).
    # We mask the last 45 pixels of that specific crop before merging.
    if "S1" in cropped_images:
        s1_img = cropped_images["S1"]
        draw_s1 = ImageDraw.Draw(s1_img)
        # 45 pixels is approx 25px on original * 1.8 stretch factor approx 45-50px visual
        mask_width = 45
        draw_s1.rectangle(
            [(s1_img.width - mask_width, 0), (s1_img.width, s1_img.height)],
            fill="white",
        )
    # -------------------------------------------------

    # ---------- Build NS page ----------

    ns_order = [("N1", "N2", "North hand"), ("S1", "S2", "South hand")]
    ns_blocks = []

    for p1, p2, label in ns_order:
        img1 = cropped_images[p1]
        img2 = cropped_images[p2]
        ns_blocks.append(stack_hand_parts(img1, img2, label))

    max_width_ns = max(img.width for img in ns_blocks)
    total_height_ns = sum(img.height for img in ns_blocks) + 70 * (len(ns_blocks) - 1)

    ns_merged = Image.new("RGB", (max_width_ns, total_height_ns), color="white")
    y_offset = 0
    for img in ns_blocks:
        ns_merged.paste(img, (0, y_offset))
        y_offset += img.height + 70

    ns_with_header = add_header_to_image(ns_merged, group_number, deal_number)
    os.makedirs(output_dir, exist_ok=True)
    ns_filename = f"{base_output_name}-NS.png"
    ns_path = os.path.join(output_dir, ns_filename)
    ns_with_header.save(ns_path)
    enhance_and_overwrite_image(ns_path)
    print(f"NS merged and enhanced image saved to {ns_path}")

    # ---------- Build EW page ----------

    ew_order = [("E1", "E2", "East hand"), ("W2", "W1", "West hand")]
    ew_blocks = []

    for p1, p2, label in ew_order:
        img1 = cropped_images[p1]
        img2 = cropped_images[p2]
        ew_blocks.append(stack_hand_parts(img1, img2, label))

    max_width_ew = max(img.width for img in ew_blocks)
    total_height_ew = sum(img.height for img in ew_blocks) + 70 * (len(ew_blocks) - 1)

    ew_merged = Image.new("RGB", (max_width_ew, total_height_ew), color="white")
    y_offset = 0
    for img in ew_blocks:
        ew_merged.paste(img, (0, y_offset))
        y_offset += img.height + 70

    ew_with_header = add_header_to_image(ew_merged, group_number, deal_number)
    ew_filename = f"{base_output_name}-EW.png"
    ew_path = os.path.join(output_dir, ew_filename)
    ew_with_header.save(ew_path)
    enhance_and_overwrite_image(ew_path)
    print(f"EW merged and enhanced image saved to {ew_path}")


def enhance_image(image_path):
    with Image.open(image_path) as img:
        # Stretch the image horizontally
        stretched_image = img.resize((int(img.width * 1.8), img.height))

        # Sharpen the image
        sharpened_image = stretched_image.filter(ImageFilter.SHARPEN)

        # Increase contrast
        contrast_enhancer = ImageEnhance.Contrast(sharpened_image)
        contrast_image = contrast_enhancer.enhance(1.8)

        # Increase color saturation
        color_enhancer = ImageEnhance.Color(contrast_image)
        saturated_image = color_enhancer.enhance(1.5)

        return saturated_image


def enhance_and_overwrite_image(image_path):
    enhanced_image = enhance_image(image_path)
    enhanced_image.save(image_path)
    print(f"Enhanced and overwritten: {image_path}")


def process_directory(input_dir, output_dir, crop_areas, group_number):
    files_processed = 0
    files_created = 0

    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory does not exist: {input_dir}")
        return files_processed, files_created

    # PREPROCESSING: Rename Scan_ files first
    renamed_count = preprocess_scan_files(input_dir, group_number)
    if renamed_count > 0:
        print(f"Preprocessed {renamed_count} files")

    # Now find all PNG files (including newly renamed ones)
    png_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".png")]
    if not png_files:
        print(f"WARNING: No PNG files found in {input_dir}")
        return files_processed, files_created

    png_files.sort()

    for filename in png_files:
        full_path = os.path.join(input_dir, filename)
        print(f"\n--- Processing: {filename} ---")
        files_processed += 1

        try:
            # 1) Crop and rotate all four hands: N, S, E, W
            cropped_images, base_name = crop_rotate_save(full_path, crop_areas)

            # 2) (No per-hand clean-up here anymore; all special patches are
            #    applied later inside merge_ns_ew_images on the final NS image.)

            # 3) Extract deal number and build base output name
            deal_number = extract_deal_number(filename)
            print(
                f"DEBUG: Final deal number being used: '{deal_number}' for file: '{filename}'"
            )

            base_output_name = f"m-{group_number}-{deal_number}"
            print(f"DEBUG: Base output name will be: '{base_output_name}'")

            # 4) Merge into NS / EW pages (uses split_hand_crop etc.)
            merge_ns_ew_images(
                cropped_images, output_dir, base_output_name, group_number, deal_number
            )

            files_created += 2  # NS and EW pages

        except Exception as e:
            print(f"ERROR processing {filename}: {str(e)}")
            continue

    print(
        f"\nSummary: {files_processed} files processed, {files_created} files created in {output_dir}"
    )
    return files_processed, files_created


def get_default_base_dir():
    """Return default Sheets directory dynamically (one level up from script)."""
    return str(Path(__file__).parent.parent)


def process_group_images(group_number, base_dir=None):
    """Main processing function for a specific group."""
    # Original single-hand crop areas
    base_crop_areas = {
        "N": (388, 24, 1195, 324, 0),
        "S": (400, 946, 1162, 246, 0),
        "E": (1783, 26, 259, 1180, 90),
        "W": (9, 36, 172, 1174, 270),
    }

    # Build split crop areas (N1/N2/S1/S2/E1/E2/W1/W2) from the originals
    crop_areas = build_split_crop_areas(base_crop_areas)
    if base_dir is None:
        base_dir = get_default_base_dir()

    input_dir = os.path.join(
        base_dir, f"Group{group_number}", "images", "OriginalScans"
    )
    output_dir = os.path.join(base_dir, f"Group{group_number}", "images", "ModScans")

    print(f"Processing Group {group_number}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    files_processed, files_created = process_directory(
        input_dir, output_dir, crop_areas, group_number
    )

    if files_processed == 0:
        print(
            "WARNING: No files were processed. Check if PNG files exist in the input directory."
        )
    elif files_created == 0:
        print(
            "WARNING: No output files were created. Check for processing errors above."
        )
    else:
        print(
            f"SUCCESS: Processed {files_processed} files, created {files_created} enhanced images"
        )

    return files_processed, files_created


def main():
    """Main function to handle command line execution."""
    parser = argparse.ArgumentParser(
        description="Split, merge and enhance hand images for a group"
    )
    parser.add_argument(
        "--group", "-g", type=int, required=True, help="Group number to process"
    )
    parser.add_argument(
        "--base-dir",
        "-d",
        type=str,
        help="Base directory for Sheets (optional, uses default if not provided)",
    )

    args = parser.parse_args()

    try:
        # Validate group number
        if not (11 <= args.group <= 38):
            print(
                f"ERROR: Group number must be between 11 and 38, got {args.group}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Determine base directory
        base_dir = args.base_dir if args.base_dir else get_default_base_dir()

        # Check if group directory exists
        group_dir = os.path.join(base_dir, f"Group{args.group}")
        if not os.path.exists(group_dir):
            print(
                f"ERROR: Group{args.group} directory does not exist at {group_dir}",
                file=sys.stderr,
            )
            print(
                "Please create the group structure first using P1SheetEntry.py",
                file=sys.stderr,
            )
            sys.exit(1)

        # Process the group images
        files_processed, files_created = process_group_images(args.group, base_dir)

        # Success message
        if files_created > 0:
            print(f"SUCCESS: Enhanced {files_created} images for Group {args.group}")
        else:
            print(f"WARNING: No images were enhanced for Group {args.group}")
            sys.exit(1)

    except ValueError as e:
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
