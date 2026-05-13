import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

# Ensure UTF-8 encoding for suit symbols
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def reflow_text(text):
    """
    Joins short lines into full paragraphs for the web,
    but keeps bridge diagrams blocky.
    """
    if not text:
        return ""

    # 1. Strip out AI markers/markdown code blocks if they exist
    text = re.sub(r"===(Start|End) of (PDF|OCR).*?===", "", text)
    text = text.replace("```", "")

    # 2. Split into blocks by double newlines (paragraphs/diagrams)
    blocks = re.split(r"\n\s*\n", text)
    processed_blocks = []

    for block in blocks:
        # DETECTION: If block contains NORTH or many symbols, it's a diagram.
        # Preserve original line breaks for diagrams.
        if "NORTH" in block or (len(re.findall(r"[♠♥♦♣]", block)) > 3):
            processed_blocks.append(block.strip())
        else:
            # It's a paragraph: remove internal newlines and normalize spaces
            # This turns narrow columns into wide, readable paragraphs.
            cleaned = block.replace("\n", " ")
            cleaned = re.sub(r"\s+", " ", cleaned)
            processed_blocks.append(cleaned.strip())

    return "\n\n".join(processed_blocks)


def update_js_section(content, group_num, deal_num, new_text):
    """Targets a specific Deal slot in the JS file and replaces its backtick content."""
    # This regex looks for GroupXXDealYY: `...`
    pattern = rf"(Group{group_num}Deal{deal_num}:\s*`)(.*?)(`,)"

    if not re.search(pattern, content, re.DOTALL):
        return content, False

    # Replace the text inside the backticks with the cleaned/reflowed text
    replacement = f"\\1\n{new_text}\n  \\3"
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    return updated_content, True


def main():
    root = tk.Tk()
    root.withdraw()

    # 1. Get Group Number from user
    group = simpledialog.askinteger("Importer", "Enter Group Number (e.g., 26):")
    if not group:
        return

    # 2. Get the Deals directory from user
    messagebox.showinfo("Select Folder", "Please select the 'Deals' folder.")
    deals_dir = filedialog.askdirectory(title="Select the 'Deals' Folder")
    if not deals_dir:
        return

    # 3. Establish Paths (JS and Deals.txt are in the selected folder)
    js_path = os.path.join(deals_dir, f"deals{group}.js")
    deals_txt_path = os.path.join(deals_dir, "booklet.txt")

    # Intro folder is a sibling to the selected folder
    intro_txt_path = os.path.normpath(
        os.path.join(deals_dir, "..", "Intro", "booklet.txt")
    )

    if not os.path.exists(js_path):
        messagebox.showerror("Error", f"JS file not found in Deals folder:\n{js_path}")
        return

    try:
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        # --- STEP 1: PROCESS INTRO (Deal 0) ---
        if os.path.exists(intro_txt_path):
            print(f"Processing Intro from: {intro_txt_path}")
            with open(intro_txt_path, "r", encoding="utf-8") as f:
                intro_raw = f.read()

            intro_cleaned = "  ### Intro\n\n" + reflow_text(intro_raw)
            js_content, success = update_js_section(js_content, group, 0, intro_cleaned)
            if success:
                print("Successfully updated Intro (Deal 0)")
        else:
            print(f"Skipping Intro: No booklet.txt found at {intro_txt_path}")

        # --- STEP 2: PROCESS DEALS (Deal 1 to X) ---
        if os.path.exists(deals_txt_path):
            print(f"Processing Deals from: {deals_txt_path}")
            with open(deals_txt_path, "r", encoding="utf-8") as f:
                deals_raw = f.read()

            # Split text by headers like "DEAL No. 34" or "DEAL 34"
            deal_splits = re.split(r"(?i)DEAL\s+No?\.\s*(\d+)", deals_raw)

            # loop through matches: splits[i] is number, splits[i+1] is the text content
            for i in range(1, len(deal_splits), 2):
                d_num = deal_splits[i]
                d_text = deal_splits[i + 1]

                # Identify Bidding and Play sections inside the deal text
                bidding_match = re.search(
                    r"(?i)The Bidding\s+(.*?)(?=The Play|\Z)", d_text, re.DOTALL
                )
                play_match = re.search(r"(?i)The Play\s+(.*?)$", d_text, re.DOTALL)

                combined_deal_text = ""
                if bidding_match:
                    clean_bid = reflow_text(bidding_match.group(1))
                    combined_deal_text += f"  ### The Bidding\n\n{clean_bid}\n\n"

                if play_match:
                    clean_play = reflow_text(play_match.group(1))
                    combined_deal_text += f"  ### The Play\n\n{clean_play}"

                # Update the JS content for this specific Deal number
                js_content, success = update_js_section(
                    js_content, group, d_num, combined_deal_text
                )
                if success:
                    print(f"Updated Deal {d_num}")
                else:
                    print(
                        f"Skipped Deal {d_num}: Could not find Group{group}Deal{d_num} in JS file."
                    )
        else:
            print(f"Skipping Deals: No booklet.txt found at {deals_txt_path}")

        # --- STEP 3: SAVE UPDATED JS FILE ---
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)

        messagebox.showinfo(
            "Success",
            f"Process Complete!\n\nGroup {group} JS file updated in the Deals folder.",
        )

    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")


if __name__ == "__main__":
    main()
