import csv
import sys
from pathlib import Path
from tkinter import Tk, filedialog, messagebox


def map_vulnerability(vul_value):
    """Map vulnerability from hdrInfo format to CSV format"""
    vul_map = {"N-S": "N", "E-W": "E", "Both": "B", "Neither": "0"}
    # Return mapped value if found, otherwise return original
    return vul_map.get(vul_value, vul_value)


def populate_hands_header(csv_dir):
    hdr_path = csv_dir / "hdrInfo.csv"
    ai_path = csv_dir / "HandsFromAI.csv"

    if not hdr_path.exists():
        messagebox.showerror("File Error", f"Required file missing: {hdr_path}")
        return

    if not ai_path.exists():
        messagebox.showerror("File Error", f"Required file missing: {ai_path}")
        return

    hdr_info = {}
    with open(hdr_path, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            hdr_info[(str(row["Group"]), str(row["Deal"]))] = (
                row["Dealer"],
                row["Vul"],
            )

    with open(ai_path, newline="") as f:
        rows = list(csv.reader(f))

    for row in rows:
        if len(row) >= 8 and row[0] == "Group" and row[2] == "Deal":
            key = (str(row[1]), str(row[3]))
            dealer, vul = hdr_info.get(key, ("", ""))
            row[5] = dealer
            row[7] = map_vulnerability(vul)  # Apply mapping here

    with open(ai_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    messagebox.showinfo(
        "Complete", f"Population of Dealer/Vul in {ai_path} is complete."
    )


if __name__ == "__main__":
    root = Tk()
    root.withdraw()

    # Configure larger font for dialogs
    root.option_add("*Dialog.msg.font", "Helvetica 12")
    root.option_add("*Dialog.msg.wrapLength", "4i")

    prerequisite_message = """PREREQUISITE STEPS - Complete Before Running:

1. Copy full set of Original Scans into Word document
2. Save Word document as PDF
3. Upload PDF to Perplexity Space
   Prompt: "Extract the bridge board data"
4. Create 'hdrInfo.csv' in Group's CSV folder
5. Copy extracted output into hdrInfo.csv

Have all steps been completed?"""

    user_response = messagebox.askyesno("Prerequisites Check", prerequisite_message)

    if not user_response:
        print("User aborted: Prerequisites not completed", file=sys.stderr)
        sys.exit(1)

    folder_selected = filedialog.askdirectory(
        title="Select folder with hdrInfo.csv and HandsFromAI.csv"
    )

    if not folder_selected:
        print("User cancelled folder selection", file=sys.stderr)
        sys.exit(1)

    populate_hands_header(Path(folder_selected))
