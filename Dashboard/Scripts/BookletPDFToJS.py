import os
import re
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox

# --- CONFIGURATION ---
# This is your main project folder. The script will look inside here for "GroupXX"
BASE_DIR = r"C:\Users\maxuk\OneDrive\Software\Projects\Handviewer\Autobridge\Sheets"

# Ensure UTF-8 encoding for suit symbols
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def reflow_text(text):
    """Joins prose into paragraphs but preserves full bridge hand diagrams."""
    if not text:
        return ""

    text = re.sub(r"===(Start|End) of (PDF|OCR).*?===", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = text.replace("\r", "")

    lines = text.split("\n")
    processed_blocks = []
    paragraph_lines = []
    i = 0

    def flush_paragraph():
        nonlocal paragraph_lines
        if not paragraph_lines:
            return

        joined = " ".join(line.strip() for line in paragraph_lines if line.strip())
        joined = re.sub(r"\s+", " ", joined).strip()
        if joined:
            processed_blocks.append(joined)

        paragraph_lines = []

    def is_suit_line(line):
        return bool(re.match(r"^\s*[♠♥♦♣]", line.strip()))

    def is_seat_line(line):
        stripped = line.strip()
        return stripped in {"NORTH", "SOUTH", "EAST", "WEST"} or bool(
            re.match(r"^WEST\s+EAST$", stripped)
        )

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Start of a hand diagram
        if stripped == "NORTH":
            flush_paragraph()

            hand_lines = []
            seen_south = False

            while i < len(lines):
                current = lines[i]
                current_stripped = current.strip()

                if current_stripped == "SOUTH":
                    seen_south = True

                hand_lines.append(current.rstrip())
                i += 1

                if i >= len(lines):
                    break

                next_line = lines[i]
                next_stripped = next_line.strip()

                # Keep blank lines inside diagram
                if next_stripped == "":
                    hand_lines.append("")
                    i += 1
                    continue

                # Keep seat/suit lines as part of diagram
                if is_seat_line(next_line) or is_suit_line(next_line):
                    continue

                # After SOUTH has appeared, first normal prose line ends the diagram
                if seen_south:
                    break

            hand_text = "\n".join(hand_lines).rstrip()
            if hand_text:
                processed_blocks.append(hand_text)
            continue

        # Blank line ends prose paragraph
        if stripped == "":
            flush_paragraph()
            i += 1
            continue

        # Normal prose
        paragraph_lines.append(stripped)
        i += 1

    flush_paragraph()

    return "\n\n".join(processed_blocks)


def update_js_section(content, group_num, deal_num, new_text):
    """Targets a specific Deal slot in the JS file and replaces its backtick content."""
    pattern = rf"(Group{group_num}Deal{deal_num}:\s*`)(.*?)(`,)"
    if not re.search(pattern, content, re.DOTALL):
        return content, False

    replacement = f"\\1\n{new_text}\n \\3"
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    return updated_content, True


def main():
    root = tk.Tk()
    root.withdraw()

    # 1. ONLY prompt for the Group Number
    group = simpledialog.askinteger("Bridge Importer", "Enter Group Number (e.g., 26):")
    if not group:
        return

    # 2. Automatically construct all paths
    group_folder = os.path.join(BASE_DIR, f"Group{group}")
    booklet_folder = os.path.join(group_folder, "Booklet")
    deals_dir = os.path.join(booklet_folder, "Deals")
    intro_dir = os.path.join(booklet_folder, "Intro")

    js_path = os.path.join(deals_dir, f"deals{group}.js")
    deals_txt_path = os.path.join(deals_dir, "booklet.txt")
    intro_txt_path = os.path.join(intro_dir, "booklet.txt")

    # 3. Verify the JS file exists (the only mandatory file)
    if not os.path.exists(js_path):
        messagebox.showerror("Error", f"Target JS file not found at:\n{js_path}")
        return

    try:
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        intro_updated = False
        deals_updated_count = 0

        # --- STEP 1: PROCESS INTRO ---
        if os.path.exists(intro_txt_path):
            print(f"Processing Intro: {intro_txt_path}")
            with open(intro_txt_path, "r", encoding="utf-8") as f:
                intro_raw = f.read()

            intro_cleaned = " ### Intro\n\n" + reflow_text(intro_raw)
            js_content, success = update_js_section(js_content, group, 0, intro_cleaned)

            if success:
                intro_updated = True
        else:
            print("Notice: Intro booklet.txt not found. Skipping.")

        # --- STEP 2: PROCESS DEALS ---
        if os.path.exists(deals_txt_path):
            print(f"Processing Deals: {deals_txt_path}")
            with open(deals_txt_path, "r", encoding="utf-8") as f:
                deals_raw = f.read()

            deal_splits = re.split(r"(?i)DEAL\s+No?\.\s*(\d+)", deals_raw)

            for i in range(1, len(deal_splits), 2):
                d_num = deal_splits[i]
                d_text = deal_splits[i + 1]

                bidding_match = re.search(
                    r"(?i)The Bidding\s+(.*?)(?=The Play|\Z)", d_text, re.DOTALL
                )
                play_match = re.search(r"(?i)The Play\s+(.*?)$", d_text, re.DOTALL)

                combined_deal_text = ""

                if bidding_match:
                    clean_bid = reflow_text(bidding_match.group(1))
                    combined_deal_text += f" ### The Bidding\n\n{clean_bid}\n\n"

                if play_match:
                    clean_play = reflow_text(play_match.group(1))
                    combined_deal_text += f" ### The Play\n\n{clean_play}"

                js_content, success = update_js_section(
                    js_content, group, d_num, combined_deal_text
                )

                if success:
                    deals_updated_count += 1
        else:
            print("Notice: Deals booklet.txt not found. Skipping.")

        # --- STEP 3: SAVE ---
        if intro_updated or deals_updated_count > 0:
            with open(js_path, "w", encoding="utf-8") as f:
                f.write(js_content)

            summary = (
                f"Success!\n\n"
                f"- Intro Updated: {'Yes' if intro_updated else 'No'}\n"
                f"- Deals Updated: {deals_updated_count}"
            )
            messagebox.showinfo("Complete", summary)
        else:
            messagebox.showwarning(
                "No Changes",
                "Found the folders, but booklet.txt files were missing or empty.",
            )

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")


if __name__ == "__main__":
    main()
