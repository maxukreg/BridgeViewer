import os
import glob
import re
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


def get_image_files(directory):
    """Finds only PNG files and sorts them by filename."""
    files = glob.glob(os.path.join(directory, "*.png"))
    files.sort(key=extract_sort_key)
    return files


def auto_rotate_to_landscape(img):
    """
    Automatically rotates portrait images to landscape orientation.
    If the image is taller than it is wide, rotate it 270° (or 90° clockwise).
    """
    width, height = img.size

    if height > width:
        # Image is in portrait, rotate 270° (same as 90° clockwise)
        img = img.rotate(270, expand=True)
        print(f"  Rotated portrait image to landscape (270 deg)")

    return img


def find_split_points(img_arr, width):
    """Finds the best 3 split points based on lowest ink density."""
    is_ink = img_arr < 200
    ink_profile = np.sum(is_ink, axis=0)

    split_points = [0]
    expected_ratios = [0.25, 0.50, 0.75]
    search_window = width // 20

    for ratio in expected_ratios:
        expected_center = int(width * ratio)
        start = max(0, expected_center - search_window)
        end = min(width, expected_center + search_window)

        if start < end:
            local_min = np.argmin(ink_profile[start:end]) + start
            split_points.append(local_min)
        else:
            split_points.append(expected_center)

    split_points.append(width)
    return split_points


def resize_image_to_fit_page(
    input_path, output_path, target_width_inches=7.5, target_height_inches=9.5
):
    """
    Resizes the split image to fit an 8.5x11 page with margins.
    This prevents cropping when placed in Word or PDF.
    """
    img = Image.open(input_path)
    original_width, original_height = img.size
    aspect_ratio = original_height / original_width

    # Convert target dimensions to pixels (assuming 150 DPI for screen reading)
    dpi = 150
    target_width_px = int(target_width_inches * dpi)
    target_height_px = int(target_height_inches * dpi)

    # Calculate new dimensions while maintaining aspect ratio
    if aspect_ratio > (target_height_inches / target_width_inches):
        # Image is taller relative to page, constrain by height
        new_height = target_height_px
        new_width = int(new_height / aspect_ratio)
    else:
        # Image is wider relative to page, constrain by width
        new_width = target_width_px
        new_height = int(new_width * aspect_ratio)

    # Resize and save
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
    resized_img.save(output_path, quality=95)
    print(f"Resized and saved: {os.path.basename(output_path)}")


def create_pdf_from_images(image_folder, output_path):
    """Compiles all Booklet-XXX.jpg images into a PDF."""
    print(f"\nCreating PDF at: {output_path}")

    images = glob.glob(os.path.join(image_folder, "Booklet-*.jpg"))
    images.sort(key=lambda x: int(os.path.basename(x)[8:11]))

    if not images:
        print("No split images found.")
        return

    # Create PDF with letter-size pages (8.5 x 11 inches)
    pdf = canvas.Canvas(output_path, pagesize=letter)
    page_width, page_height = letter  # in points

    for img_path in images:
        print(f"Adding to PDF: {os.path.basename(img_path)}")
        try:
            img = Image.open(img_path)
            img_width_px, img_height_px = img.size

            # Convert pixels to points (1 inch = 72 points, DPI=150)
            dpi = 150
            img_width_points = (img_width_px / dpi) * 72
            img_height_points = (img_height_px / dpi) * 72

            # Center the image on the page with 0.5 inch margins
            margin = 0.5 * inch
            x_position = (page_width - img_width_points) / 2
            y_position = page_height - margin - img_height_points

            # Add image to PDF
            pdf.drawImage(
                img_path,
                x_position,
                y_position,
                width=img_width_points,
                height=img_height_points,
            )

            # Add a new page for the next image
            pdf.showPage()

        except Exception as e:
            print(f"Warning: Could not add {img_path}. Error: {e}")

    pdf.save()
    print("PDF Saved Successfully!")


def process_booklet_workflow():
    root = tk.Tk()
    root.withdraw()

    print("Please select booklet deals folder...")
    input_dir = filedialog.askdirectory(
        title="Select booklet deals folder with Scanned Images"
    )
    if not input_dir:
        print("No folder selected. Exiting.")
        return

    # Folders
    processed_dir = os.path.join(input_dir, "Processed_Booklet")
    resized_dir = os.path.join(input_dir, "Resized_for_PDF")

    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(resized_dir, exist_ok=True)

    # Clear old output
    def clear_folder(folder_path):
        if os.path.exists(folder_path):
            for f in glob.glob(os.path.join(folder_path, "*")):
                if os.path.isfile(f):
                    os.remove(f)
            print(f"Cleared {folder_path}")

    clear_folder(processed_dir)
    clear_folder(resized_dir)

    old_pdf = os.path.join(input_dir, "BookletImagesSplit.pdf")
    if os.path.exists(old_pdf):
        os.remove(old_pdf)
        print("Deleted old PDF")

    scan_files = get_image_files(input_dir)
    if not scan_files:
        print("No images found in selected directory.")
        return

    print(f"Found {len(scan_files)} raw scans. Starting split process...")

    global_page_counter = 1

    # STEP 1: split
    for filepath in scan_files:
        filename = os.path.basename(filepath)
        print(f"\nSplitting: {filename}...")
        try:
            with Image.open(filepath) as img:
                # AUTO-ROTATE: Convert portrait to landscape
                img = auto_rotate_to_landscape(img)

                gray = img.convert("L")
                width, height = img.size
                img_arr = np.array(gray)
                points = find_split_points(img_arr, width)

                for i in range(4):
                    left = points[i]
                    right = points[i + 1]
                    box = (left, 0, right, height)
                    crop = img.crop(box)

                    out_name = f"Booklet-{global_page_counter:03d}.jpg"
                    out_path = os.path.join(processed_dir, out_name)
                    crop.save(out_path)
                    global_page_counter += 1

        except Exception as e:
            print(f"Skipping {filename} due to error: {e}")

    print("\nSplitting complete. Now resizing for PDF...")

    # STEP 2: resize
    split_images = glob.glob(os.path.join(processed_dir, "Booklet-*.jpg"))
    split_images.sort(key=lambda p: int(os.path.basename(p)[8:11]))

    for split_img_path in split_images:
        filename = os.path.basename(split_img_path)
        resized_path = os.path.join(resized_dir, filename)
        resize_image_to_fit_page(split_img_path, resized_path)

    # delete original splits and folder
    for split_img_path in split_images:
        if os.path.exists(split_img_path):
            os.remove(split_img_path)
    print("Deleted original split images; only resized copies kept.")

    import shutil

    try:
        if os.path.isdir(processed_dir):
            shutil.rmtree(processed_dir)
            print("Removed Processed_Booklet folder.")
    except PermissionError as e:
        print(f"Could not remove {processed_dir}: {e}")

    print("Resizing complete. Creating PDF...")

    # STEP 3: PDF from resized images (ascending order)
    pdf_filename = "BookletImagesSplit.pdf"
    pdf_output_path = os.path.join(input_dir, pdf_filename)
    images = glob.glob(os.path.join(resized_dir, "Booklet-*.jpg"))
    images.sort(key=lambda x: int(os.path.basename(x)[8:11]))  # Normal ascending order

    if not images:
        print("No resized images found.")
        return

    pdf = canvas.Canvas(pdf_output_path, pagesize=letter)
    page_width, page_height = letter
    dpi = 150

    for img_path in images:
        print(f"Adding to PDF: {os.path.basename(img_path)}")
        try:
            with Image.open(img_path) as img:
                img_width_px, img_height_px = img.size
                img_width_points = (img_width_px / dpi) * 72
                img_height_points = (img_height_px / dpi) * 72

                margin = 0.5 * inch
                x_position = (page_width - img_width_points) / 2
                y_position = page_height - margin - img_height_points

                pdf.drawImage(
                    img_path,
                    x_position,
                    y_position,
                    width=img_width_points,
                    height=img_height_points,
                )
                pdf.showPage()
        except Exception as e:
            print(f"Warning: Could not add {img_path}. Error: {e}")

    pdf.save()
    print("\n" + "=" * 60)
    print("ALL DONE!")
    print(f"1. Resized images: {resized_dir}")
    print(f"2. Final PDF: {pdf_output_path}")
    print("=" * 60)


def extract_sort_key(filename):
    """Handles Windows-style bracketed numbers: filename (1).ext"""
    basename = os.path.basename(filename)

    # Match: "basename (number).extension"
    match = re.match(r"^(.+?) \((\d+)\)\.(\w+)$", basename)
    if match:
        base_name = match.group(1)
        number = int(match.group(2))
        return (base_name, number)

    # No brackets - remove extension and use 0
    base_name = re.sub(r"\.\w+$", "", basename)
    return (base_name, 0)


if __name__ == "__main__":
    process_booklet_workflow()
