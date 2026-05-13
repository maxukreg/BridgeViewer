import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import re

# --- Utility Functions ---


def extractnumberfromfilename(filename):
    match = re.search(r"\((\d+)\)", filename)
    return int(match.group(1)) if match else 0


def wipescannerartifacts(img, scandepth=120):
    gray = img.convert("L")
    w, h = gray.size
    draw = ImageDraw.Draw(img)
    darkthresh = 80
    barthresh = 0.60
    white = (255, 255, 255)

    for y in range(min(scandepth, h)):
        rowpixels = [gray.getpixel((x, y)) for x in range(0, w, 5)]
        darkcount = sum(1 for p in rowpixels if p < darkthresh)
        density = darkcount / len(rowpixels)
        if density > barthresh:
            draw.line([(0, y), (w, y)], fill=white, width=1)

    for y in range(h - 1, max(h - scandepth, 0), -1):
        rowpixels = [gray.getpixel((x, y)) for x in range(0, w, 5)]
        darkcount = sum(1 for p in rowpixels if p < darkthresh)
        density = darkcount / len(rowpixels)
        if density > barthresh:
            draw.line([(0, y), (w, y)], fill=white, width=1)

    for x in range(min(scandepth, w)):
        colpixels = [gray.getpixel((x, y)) for y in range(0, h, 5)]
        darkcount = sum(1 for p in colpixels if p < darkthresh)
        density = darkcount / len(colpixels)
        if density > barthresh:
            draw.line([(x, 0), (x, h)], fill=white, width=1)

    for x in range(w - 1, max(w - scandepth, 0), -1):
        colpixels = [gray.getpixel((x, y)) for y in range(0, h, 5)]
        darkcount = sum(1 for p in colpixels if p < darkthresh)
        density = darkcount / len(colpixels)
        if density > barthresh:
            draw.line([(x, 0), (x, h)], fill=white, width=1)

    return img


def findvisualsplitpoint(img, axis="y", scanrange=(0.35, 0.65)):
    gray = img.convert("L")
    width, height = gray.size
    start_pct, end_pct = scanrange
    bestcoord = 0
    maxbrightness = -1

    if axis == "y":
        start_y = int(height * start_pct)
        end_y = int(height * end_pct)
        for y in range(start_y, end_y):
            rowpixels = [gray.getpixel((x, y)) for x in range(0, width, 5)]
            avgbrightness = sum(rowpixels) / len(rowpixels)
            if avgbrightness > maxbrightness:
                maxbrightness = avgbrightness
                bestcoord = y
        if bestcoord == 0:
            bestcoord = int(height * 0.55)
    else:
        start_x = int(width * start_pct)
        end_x = int(width * end_pct)
        for x in range(start_x, end_x):
            colpixels = [gray.getpixel((x, y)) for y in range(0, height, 5)]
            avgbrightness = sum(colpixels) / len(colpixels)
            if avgbrightness > maxbrightness:
                maxbrightness = avgbrightness
                bestcoord = x
        if bestcoord == 0:
            bestcoord = int(width * 0.50)
    return bestcoord


def croprotatesave(imagepath, cropareas):
    basename = os.path.splitext(os.path.basename(imagepath))[0]
    croppedimages = {}
    with Image.open(imagepath) as img:
        for name, (x, y, w, h, rotation) in cropareas.items():
            cropped = img.crop((x, y, x + w, y + h))
            if rotation:
                cropped = cropped.rotate(rotation, expand=True)
            cropped = wipescannerartifacts(cropped, scandepth=120)
            croppedimages[name] = cropped
    return croppedimages, basename


def splitandgenerateparts(basecropimages):
    splitimages = {}
    for key, img in basecropimages.items():
        width, height = img.size
        if key in ["N", "S"]:
            split_x = findvisualsplitpoint(img, axis="x", scanrange=(0.45, 0.55))
            part1 = img.crop((0, 0, split_x, height))
            part2 = img.crop((split_x, 0, width, height))
            splitimages[f"{key}1"] = part1
            splitimages[f"{key}2"] = part2
        else:
            split_x = findvisualsplitpoint(img, axis="x", scanrange=(0.45, 0.65))
            part1 = img.crop((0, 0, split_x, height))
            part2 = img.crop((split_x, 0, width, height))
            splitimages[f"{key}1"] = part1
            splitimages[f"{key}2"] = part2
    return splitimages


def addtexttoimage(image, text, textheight=40):
    newimg = Image.new("RGB", (image.width, image.height + textheight), color="white")
    newimg.paste(image, (0, textheight))
    draw = ImageDraw.Draw(newimg)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
    text_width = draw.textlength(text, font=font)
    textposition = ((newimg.width - text_width) / 2, 5)
    draw.text(textposition, text, fill="black", font=font)
    return newimg


def addheadertoimage(image, groupnumber, dealnumber):
    headertext = f"Group {groupnumber} - Deal {dealnumber}"
    return addtexttoimage(image, headertext, textheight=20)


def enhanceimage(imagepath):
    with Image.open(imagepath) as img:
        stretchedimage = img.resize((int(img.width * 1.8), img.height))
        sharpenedimage = stretchedimage.filter(ImageFilter.SHARPEN)
        contrastenhancer = ImageEnhance.Contrast(sharpenedimage)
        contrastimage = contrastenhancer.enhance(1.8)
        colorenhancer = ImageEnhance.Color(contrastimage)
        saturatedimage = colorenhancer.enhance(1.5)
        return saturatedimage


def enhanceandoverwrite(imagepath):
    enhanced = enhanceimage(imagepath)
    enhanced.save(imagepath)


def mergensew(splitimages, outputdir, baseoutputname, groupnumber, dealnumber):
    def stackhandparts(part1, part2, labeltext):
        combined_height = part1.height + part2.height
        max_width = max(part1.width, part2.width)
        tmp = Image.new("RGB", (max_width, combined_height), color="white")
        tmp.paste(part1, (0, 0))
        tmp.paste(part2, (0, part1.height))
        return addtexttoimage(tmp, labeltext)

    ns_order = [("N1", "N2", "North hand"), ("S1", "S2", "South hand")]
    ns_blocks = [
        stackhandparts(splitimages[p1], splitimages[p2], label)
        for p1, p2, label in ns_order
    ]
    max_width_ns = max(img.width for img in ns_blocks)
    total_height_ns = sum(img.height for img in ns_blocks) + 70 * (len(ns_blocks) - 1)
    ns_merged = Image.new("RGB", (max_width_ns, total_height_ns), color="white")
    y_offset = 0
    for img in ns_blocks:
        ns_merged.paste(img, (0, y_offset))
        y_offset += img.height + 70
    ns_with_header = addheadertoimage(ns_merged, groupnumber, dealnumber)
    ns_filename = f"{baseoutputname}-NS.png"
    ns_path = os.path.join(outputdir, ns_filename)
    ns_with_header.save(ns_path)
    enhanceandoverwrite(ns_path)

    ew_order = [("E1", "E2", "East hand"), ("W1", "W2", "West hand")]
    ew_blocks = [
        stackhandparts(splitimages[p1], splitimages[p2], label)
        for p1, p2, label in ew_order
    ]
    max_width_ew = max(img.width for img in ew_blocks)
    total_height_ew = sum(img.height for img in ew_blocks) + 70 * (len(ew_blocks) - 1)
    ew_merged = Image.new("RGB", (max_width_ew, total_height_ew), color="white")
    y_offset = 0
    for img in ew_blocks:
        ew_merged.paste(img, (0, y_offset))
        y_offset += img.height + 70
    ew_with_header = addheadertoimage(ew_merged, groupnumber, dealnumber)
    ew_filename = f"{baseoutputname}-EW.png"
    ew_path = os.path.join(outputdir, ew_filename)
    ew_with_header.save(ew_path)
    enhanceandoverwrite(ew_path)


def merge_all_hands_vertically(
    croppedimages, outputdir, baseoutputname, groupnumber, dealnumber
):
    """Creates a single merged image with all four hands: North, South, East, West."""
    suffix_text = {
        "N": "North hand",
        "S": "South hand",
        "W": "West hand",
        "E": "East hand",
    }
    hands_order = ["N", "S", "E", "W"]  # North, South, East, West order
    images_with_text = []

    for name in hands_order:
        img = croppedimages[name]
        text = suffix_text.get(name, "")
        images_with_text.append(addtexttoimage(img, text))

    max_width = max(img.width for img in images_with_text)
    total_height = sum(img.height for img in images_with_text) + 70 * (
        len(images_with_text) - 1
    )
    merged_image = Image.new("RGB", (max_width, total_height), color="white")
    y_offset = 0

    for img in images_with_text:
        merged_image.paste(img, (0, y_offset))
        y_offset += img.height + 70  # Consistent gap

    merged_image_with_header = addheadertoimage(merged_image, groupnumber, dealnumber)
    output_filename = f"{baseoutputname}.png"
    output_filepath = os.path.join(outputdir, output_filename)
    merged_image_with_header.save(output_filepath)
    enhanceandoverwrite(output_filepath)


def getsortedinfofromfilename(filename):
    basename = os.path.splitext(filename)[0]
    # Match the pattern: s-{group}-{deal}
    match = re.search(r"s-(\d+)-(\d+)$", basename, re.IGNORECASE)
    if match:
        group = match.group(1)
        deal = match.group(2)
        output_base = f"m-{group}-{deal}"
        return group, deal, output_base
    else:
        # Fallback: if the match fails, try to extract the numbers
        digit_match = re.search(r"(\d+)", basename)
        if digit_match:
            deal = digit_match.group(1)
            return "Unknown", deal, f"m-Unknown-{deal}"
        else:
            return "Unknown", "Unknown", "m-Unknown-Unknown"


def processfile(filepath, modscans_dir, cropareas, groupnumber):
    # Extract info and generate output filenames
    input_filename = os.path.basename(filepath)
    group, deal, output_base = getsortedinfofromfilename(input_filename)

    # Construct full output filenames
    ns_filename = f"{output_base}.NS.png"
    ew_filename = f"{output_base}.EW.png"
    merged_filename = f"{output_base}.png"

    ns_path = os.path.join(modscans_dir, ns_filename)
    ew_path = os.path.join(modscans_dir, ew_filename)
    merged_path = os.path.join(modscans_dir, merged_filename)

    try:
        # Crop, rotate, and wipe scanner artifacts
        basecroppedimages, basename = croprotatesave(filepath, cropareas)
        splitimages = splitandgenerateparts(basecroppedimages)

        # Create and save NS file
        mergensew(splitimages, modscans_dir, output_base, group, deal)

        # Create and save merged file with North, South, East, West order
        merge_all_hands_vertically(
            basecroppedimages, modscans_dir, output_base, group, deal
        )

        # All files are saved and processed
        return True
    except Exception as e:
        print(f"ERROR processing {filepath}: {e}", file=sys.stderr)
        return False


def processdirectory(inputdir, modscans_dir, cropareas, groupnumber):
    filesprocessed = 0
    filescreated = 0
    pngfiles = sorted(
        [f for f in os.listdir(inputdir) if f.lower().endswith(".png")],
        key=extractnumberfromfilename,
    )
    if not pngfiles:
        print(f"WARNING: No PNG files found in {inputdir}", file=sys.stderr)
        return 0, 0

    for filename in pngfiles:
        fullpath = os.path.join(inputdir, filename)
        if processfile(fullpath, modscans_dir, cropareas, groupnumber):
            filesprocessed += 1
            filescreated += 3
    return filesprocessed, filescreated


# --- Main Execution ---


def get_user_choice():
    root = tk.Tk()
    root.title("File Processing Choice")
    choice = tk.StringVar()
    choice.set("all")  # This sets the default selection to "all"

    def on_submit():
        root.destroy()

    tk.Label(root, text="Choose processing mode:").pack(pady=10)
    tk.Radiobutton(
        root, text="Process all files in a directory", variable=choice, value="all"
    ).pack()
    tk.Radiobutton(root, text="Process one file", variable=choice, value="one").pack()
    tk.Button(root, text="Submit", command=on_submit).pack(pady=10)
    root.mainloop()

    return choice.get()


def main():
    mode = get_user_choice()
    cropareas = {
        "N": (350, 10, 1250, 350, 0),
        "S": (380, 930, 1250, 280, 0),
        "E": (1770, 20, 280, 1200, 90),
        "W": (0, 30, 200, 1190, 270),
    }

    if mode == "all":
        inputdir = filedialog.askdirectory(title="Select OrginalScans folder ")
        if not inputdir:
            print("No directory selected.")
            return
        modscans_dir = os.path.join(os.path.dirname(inputdir), "ModScans")
        os.makedirs(modscans_dir, exist_ok=True)
        filesprocessed, filescreated = processdirectory(
            inputdir, modscans_dir, cropareas, "38"
        )  # adjust group number as needed
    elif mode == "one":
        filepath = filedialog.askopenfilename(
            title="Select One File", filetypes=[("PNG files", "*.png")]
        )
        if not filepath:
            print("No file selected.")
            return
        modscans_dir = os.path.join(
            os.path.dirname(os.path.dirname(filepath)), "ModScans"
        )
        os.makedirs(modscans_dir, exist_ok=True)
        if processfile(
            filepath, modscans_dir, cropareas, "38"
        ):  # adjust group number as needed
            filescreated = 3
        else:
            filescreated = 0
    else:
        print("Invalid mode selected.")
        return

    print(f"Processed {filescreated} output files in {modscans_dir}.")


if __name__ == "__main__":
    main()
