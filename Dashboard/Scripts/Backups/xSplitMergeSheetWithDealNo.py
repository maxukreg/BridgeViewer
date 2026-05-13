import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from datetime import datetime
import re

def extract_number_from_filename(filename):
    """Extract the number from parentheses in the filename for proper sorting"""
    match = re.search(r'\((\d+)\)', filename)
    return int(match.group(1)) if match else 0

def crop_rotate_save(image_path, crop_areas):
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    cropped_images = {}

    with Image.open(image_path) as img:
        for name, (x, y, w, h, rotation) in crop_areas.items():
            cropped = img.crop((x, y, x+w, y+h))
            if rotation:
                cropped = cropped.rotate(rotation, expand=True)
            cropped_images[name] = cropped

    return cropped_images, base_name

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
        if filename.startswith(pattern) and filename.lower().endswith('.png'):
            # Extract deal number from m-{group}-{deal}.png
            try:
                deal_part = filename[len(pattern):].split('.')[0]
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
    scan_files = [f for f in os.listdir(input_dir) if f.startswith('Scan_') and f.lower().endswith('.png')]
    
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
        print(f"Found existing files up to deal {highest_existing}, starting from deal {next_deal}")
    else:
        # Start from the beginning of the range
        next_deal = start_deal
        print(f"No existing files found, starting from deal {next_deal}")
    
    # Check count vs expected
    if len(scan_files) != expected_count:
        print(f"WARNING: Found {len(scan_files)} Scan_ files, but expected {expected_count} deals ({start_deal}-{end_deal}) for Group {group_number}")
        print("Continuing with available files...")
    
    # Rename files
    renamed_count = 0
    for i, old_filename in enumerate(scan_files):
        deal_number = next_deal + i
        
        # Check if we're going beyond expected range
        if deal_number > end_deal:
            print(f"WARNING: Deal number {deal_number} exceeds expected range ({start_deal}-{end_deal}) for Group {group_number}")
            print("Continuing anyway...")
        
        old_path = os.path.join(input_dir, old_filename)
        new_filename = f"m-{group_number}-{deal_number}.png"
        new_path = os.path.join(input_dir, new_filename)
        
        try:
            # Check if target file already exists
            if os.path.exists(new_path):
                print(f"WARNING: Target file {new_filename} already exists, skipping {old_filename}")
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
    match = re.search(r'-(\d+)\.png', filename, re.IGNORECASE)
    if match:
        deal_number = match.group(1)
        print(f"DEBUG: Original pattern matched - extracted: {deal_number}")
        return deal_number
    
    # Try alternative patterns based on common naming conventions
    patterns = [
        (r'(\d+)\.png', 'number at end before .png'),
        (r'-(\d+)-', 'number between dashes'),
        (r's-(\d+)', 'number after s-'),
        (r'deal[\s-_]*(\d+)', 'number after "deal"'),
        (r'(\d+)', 'any number in filename')
    ]
    
    for pattern, description in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            deal_number = match.group(1)
            print(f"DEBUG: Alternative pattern '{description}' matched - extracted: {deal_number}")
            return deal_number
    
    print(f"WARNING: Could not extract deal number from '{filename}' using any pattern")
    return "Unknown"

def add_text_to_image(image, text):
    text_height = 40
    new_img = Image.new('RGB', (image.width, image.height + text_height), color='white')
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
    new_img = Image.new('RGB', (image.width, image.height + header_height), color='white')
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

def merge_images_vertically(cropped_images, output_dir, output_filename, group_number, deal_number):
    suffix_text = {'N': 'North hand', 'S': 'South hand', 'W': 'West hand', 'E': 'East hand'}
    images_with_text = []

    for name, img in cropped_images.items():
        text = suffix_text.get(name, '')
        images_with_text.append(add_text_to_image(img, text))

    max_width = max(img.width for img in images_with_text)
    total_height = sum(img.height for img in images_with_text) + 70 * (len(images_with_text) - 1)

    merged_image = Image.new('RGB', (max_width, total_height), color='white')

    y_offset = 0
    for i, img in enumerate(images_with_text):
        merged_image.paste(img, (0, y_offset))
        if i == 2:  # Before pasting the fourth hand (index 2 to 3)
            y_offset += img.height + 72  # Larger gap for the third gap
        else:
            y_offset += img.height + 70  # Default gap

    # Add header with Group and Deal Number
    merged_image_with_header = add_header_to_image(merged_image, group_number, deal_number)

    os.makedirs(output_dir, exist_ok=True)
    output_file_path = os.path.join(output_dir, output_filename)
    merged_image_with_header.save(output_file_path)
    
    # Enhance and overwrite the saved image
    enhance_and_overwrite_image(output_file_path)

    print(f'Merged and enhanced image saved to {output_file_path}')

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
    png_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.png')]
    
    if not png_files:
        print(f"WARNING: No PNG files found in {input_dir}")
        return files_processed, files_created
    
    print(f"Found {len(png_files)} PNG files to process")
    
    # Sort files for consistent processing order
    png_files.sort()
    
    for filename in png_files:
        full_path = os.path.join(input_dir, filename)
        print(f"\n--- Processing: {filename} ---")
        files_processed += 1
        
        try:
            cropped_images, base_name = crop_rotate_save(full_path, crop_areas)
            
            # Extract deal number from filename directly to ensure consistency
            deal_number = extract_deal_number(filename)
            print(f"DEBUG: Final deal number being used: '{deal_number}' for file: '{filename}'")
            
            # Create output filename - keep the same base name but change prefix
            if filename.startswith('m-'):
                # Already in correct format, keep the same name
                output_filename = filename
            else:
                # Legacy format, create new name
                output_filename = 'm' + filename[1:] if filename.startswith('s') else 'm-' + filename
            print(f"DEBUG: Output filename will be: '{output_filename}'")
            
            merge_images_vertically(cropped_images, output_dir, output_filename, group_number, deal_number)
            files_created += 1
            
        except Exception as e:
            print(f"ERROR processing {filename}: {str(e)}")
            continue
    
    print(f"\nSummary: {files_processed} files processed, {files_created} files created in {output_dir}")
    return files_processed, files_created

def get_default_base_dir():
    """Return hardcoded default Sheets directory."""
    return r"C:\Users\maxuk\OneDrive\Software\Projects\Handviewer\Autobridge\Sheets"

def process_group_images(group_number, base_dir=None):
    """Main processing function for a specific group."""
    crop_areas = {
        'N': (400, 30, 1154, 246, 0),
        'S': (400, 946, 1178, 246, 0),
        'E': (1810, 26, 248, 1180, 90),
        'W': (32, 36, 156, 1174, 270) 
    }

    if base_dir is None:
        base_dir = get_default_base_dir()

    input_dir = os.path.join(base_dir, f"Group{group_number}", "images", "OriginalScans")
    output_dir = os.path.join(base_dir, f"Group{group_number}", "images", "ModScans")

    print(f"Processing Group {group_number}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    files_processed, files_created = process_directory(input_dir, output_dir, crop_areas, group_number)
    
    if files_processed == 0:
        print("WARNING: No files were processed. Check if PNG files exist in the input directory.")
    elif files_created == 0:
        print("WARNING: No output files were created. Check for processing errors above.")
    else:
        print(f"SUCCESS: Processed {files_processed} files, created {files_created} enhanced images")
    
    return files_processed, files_created

def main():
    """Main function to handle command line execution."""
    parser = argparse.ArgumentParser(description='Split, merge and enhance hand images for a group')
    parser.add_argument('--group', '-g', type=int, required=True,
                       help='Group number to process')
    parser.add_argument('--base-dir', '-d', type=str,
                       help='Base directory for Sheets (optional, uses default if not provided)')
    
    args = parser.parse_args()
    
    try:
        # Validate group number
        if not (11 <= args.group <= 38):
            print(f"ERROR: Group number must be between 11 and 38, got {args.group}", file=sys.stderr)
            sys.exit(1)
        
        # Determine base directory
        base_dir = args.base_dir if args.base_dir else get_default_base_dir()
        
        # Check if group directory exists
        group_dir = os.path.join(base_dir, f"Group{args.group}")
        if not os.path.exists(group_dir):
            print(f"ERROR: Group{args.group} directory does not exist at {group_dir}", file=sys.stderr)
            print("Please create the group structure first using P1SheetEntry.py", file=sys.stderr)
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