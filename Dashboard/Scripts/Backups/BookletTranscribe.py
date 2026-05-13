import os
import argparse
from google import genai
from google.genai import types
import sys
import win32com.client
import re

# Windows console encoding fix (works with/without subprocess capture)
if hasattr(sys.stdout, "buffer"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

# CONFIG
API_KEY = "AIzaSyA-E_GQ5uUKZRsaecTFrpn_LXuNc_Q4yIE"
MODEL_NAME = "gemini-3-flash-preview"

# Mode configuration — drives folder name, prompt file, and output location
MODE_CONFIG = {
    "deals": {
        "folder": "Deals",
        "prompt_file": "TranscribeBookletFromPDF.txt",
        "label": "Deals",
    },
    "intro": {
        "folder": "Intro",
        "prompt_file": "TranscribeIntroFromPDF.txt",
        "label": "Intro",
    },
}


def ask_mode() -> str:
    """Prompt the user to choose between intro and deals mode."""
    while True:
        choice = input("Run mode — enter 'intro' or 'deals': ").strip().lower()
        if choice in MODE_CONFIG:
            return choice
        print("  Please type 'intro' or 'deals'.")


def get_group_folder(script_dir: str, group_num: str, mode: str) -> str:
    """Find GroupXX/<mode-folder> using --group or auto-detect."""
    folder_name = MODE_CONFIG[mode]["folder"]

    if group_num:
        print(f"Using group from dashboard: {group_num}")
        sheets_root = os.path.join(script_dir, "..")
        group_folder = os.path.join(
            sheets_root, f"Group{group_num}", "Booklet", folder_name
        )
        print(f"Looking for {folder_name} folder: {group_folder}")
        if os.path.exists(group_folder):
            return group_folder
        else:
            print(f"Group{group_num}/Booklet/{folder_name} not found at {group_folder}")
            sys.exit(1)

    # Fallback: auto-detect from existing GroupXX folders
    sheets_root = os.path.join(script_dir, "..")
    for folder in os.listdir(sheets_root):
        if folder.startswith("Group") and os.path.isdir(
            os.path.join(sheets_root, folder)
        ):
            group_folder = os.path.join(sheets_root, folder, "Booklet", folder_name)
            if os.path.exists(group_folder):
                group_num = folder
                print(f"Auto-detected Group: {group_num}")
                return group_folder
    print(f"No GroupXX/Booklet/{folder_name} folder found!")
    sys.exit(1)


def load_prompt(prompts_folder: str, prompt_name: str) -> str:
    prompt_file = os.path.join(prompts_folder, prompt_name)
    if not os.path.exists(prompt_file):
        print(f"ERROR: Prompt not found: {prompt_file}")
        sys.exit(1)
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()


def run_transcription(group_num: str, pdf_path: str, prompts_folder: str, mode: str):
    """Core transcription logic shared by both interactive and CLI modes."""
    cfg = MODE_CONFIG[mode]
    print(f"Processing Group {group_num} [{cfg['label']}]: {pdf_path}")

    # Load the appropriate prompt for this mode
    prompt_text = load_prompt(prompts_folder, cfg["prompt_file"])

    # Gemini processing
    print("Configuring Gemini...")
    client = genai.Client(api_key=API_KEY)

    print("Uploading PDF...")
    uploaded = client.files.upload(
        file=pdf_path, config={"mime_type": "application/pdf"}
    )

    print("Generating transcription...")
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt_text, uploaded],
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=65536,
            http_options=types.HttpOptions(timeout=600000),
        ),
    )

    if not response.text:
        print("ERROR: No response from Gemini!")
        sys.exit(1)

    result_text = response.text
    print(f"Received {len(result_text)} chars")

    # Clean up excessive blank lines from Gemini output.
    # Gemini tends to put a blank line after every single line.
    # Strategy: collapse runs of 3+ newlines to 2, then rejoin consecutive
    # non-empty lines that belong together (dealer/vuln/bidding table rows).

    # Step 1: normalise line endings
    result_text = result_text.replace("\r\n", "\n").replace("\r", "\n")

    # Step 2: collapse 3+ consecutive blank lines down to one blank line
    result_text = re.sub(r"\n{3,}", "\n\n", result_text)

    # Step 3: remove the blank line that Gemini inserts between lines that
    # belong in the same block (dealer line, vulnerability line, bidding rows).
    # A "block line" is a short line that is NOT a section heading and NOT a
    # deal heading and NOT a prose sentence (heuristic: <= 60 chars, no full stop).
    def rejoin_block_lines(text):
        lines = text.split("\n")
        out = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if (
                i + 2 < len(lines)
                and lines[i + 1] == ""  # blank separator
                and lines[i + 2] != ""  # next content line exists
                and len(line) > 0
                and len(line) <= 60
                and not line.endswith(".")
                and not line.startswith("DEAL NO.")
                and not lines[i + 2].startswith("DEAL NO.")
                and lines[i + 2] not in ("The Bidding", "The Play")
                and len(lines[i + 2]) <= 60
                and not lines[i + 2].endswith(".")
            ):
                out.append(line)
                i += 2  # skip the blank line
            else:
                out.append(line)
                i += 1
        return "\n".join(out)

    result_text = rejoin_block_lines(result_text)

    # Step 4: final pass — collapse any remaining 3+ newlines
    result_text = re.sub(r"\n{3,}", "\n\n", result_text)

    print(f"Cleaned text: {len(result_text)} chars")

    # Output directory is always the folder the PDF lives in
    # (Deals/ for deals mode, Intro/ for intro mode)
    output_dir = os.path.dirname(pdf_path)
    text_out = os.path.join(output_dir, "Booklet.txt")
    output_pdf = os.path.join(output_dir, "Booklet.pdf")

    with open(text_out, "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"Saved raw text: {text_out}")

    # Word → PDF
    print("Creating PDF via Word...")
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        # Close any already-open Booklet.docx to avoid naming conflict
        temp_docx = os.path.abspath(os.path.join(output_dir, "Booklet.docx"))
        for open_doc in list(word.Documents):
            if os.path.abspath(open_doc.FullName) == temp_docx:
                open_doc.Close(False)  # False = don't save changes

        doc = word.Documents.Add()
        doc.Content.Delete()

        # Zero out the Normal style BEFORE inserting any text so all
        # paragraphs inherit zero spacing from the start.
        normal_style = doc.Styles("Normal")
        normal_style.ParagraphFormat.SpaceAfter = 0
        normal_style.ParagraphFormat.SpaceBefore = 0
        normal_style.ParagraphFormat.LineSpacingRule = 0  # wdLineSpaceSingle
        normal_style.Font.Name = "Calibri"
        normal_style.Font.Size = 12

        doc.Content.Text = result_text

        # Belt-and-braces: re-apply formatting to the entire content range.
        rng = doc.Content
        rng.Font.Name = "Calibri"
        rng.Font.Size = 12
        rng.ParagraphFormat.SpaceAfter = 0
        rng.ParagraphFormat.SpaceBefore = 0
        rng.ParagraphFormat.LineSpacingRule = 0  # wdLineSpaceSingle

        doc.SaveAs2(temp_docx, FileFormat=16)

        doc.ExportAsFixedFormat(
            OutputFileName=os.path.abspath(output_pdf),
            ExportFormat=17,  # PDF
            OpenAfterExport=False,
        )

        doc.Close(False)
        word.Quit()
        print(f"SUCCESS: {output_pdf}")

    except Exception as e:
        print(f"Word error: {e}")
        sys.exit(1)


def interactive_mode():
    """Interactive mode for running standalone in VSCode/terminal."""
    print("=== BookletTranscribe Interactive Mode ===")

    # Ask which mode to run
    mode = ask_mode()

    group_num = input("Enter group number (e.g., 36): ").strip()
    if not group_num:
        print("ERROR: Group number required.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_folder = os.path.join(script_dir, "..", "Prompts")

    print(f"Mode: {MODE_CONFIG[mode]['label']}")
    print(f"Using prompts folder: {prompts_folder}")

    group_folder = get_group_folder(script_dir, group_num, mode)
    pdf_path = os.path.join(group_folder, "BookletImagesSplit.pdf")

    print(f"\nBookletTranscribe - Group {group_num} [{MODE_CONFIG[mode]['label']}]")
    print(f"PDF path: {pdf_path}")
    print(f"Prompts folder: {prompts_folder}")

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    run_transcription(group_num, pdf_path, prompts_folder, mode)
    print(f"\nGroup {group_num} [{MODE_CONFIG[mode]['label']}] complete!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-path", help="Direct PDF from dashboard")
    parser.add_argument("--base-dir", default=".", help="Base directory")
    parser.add_argument("--prompts-folder", help="Folder containing prompt files")
    parser.add_argument("--group", help="Group number")
    parser.add_argument(
        "--mode",
        choices=["deals", "intro"],
        default="deals",
        help="Transcription mode: 'deals' (default) or 'intro'",
    )
    args = parser.parse_args()

    mode = args.mode
    print(
        f"BookletTranscribe.py started from dashboard — mode: {MODE_CONFIG[mode]['label']}"
    )
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")

    group_folder = get_group_folder(script_dir, args.group, mode)
    pdf_path = args.pdf_path or os.path.join(group_folder, "BookletImagesSplit.pdf")

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    group_num = args.group or os.path.basename(os.path.dirname(group_folder))
    prompts_folder = args.prompts_folder or os.path.join(script_dir, "..", "Prompts")

    run_transcription(group_num, pdf_path, prompts_folder, mode)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) == 1:  # No command line args → interactive/VSCode mode
        interactive_mode()
    else:
        main()  # Dashboard CLI mode (unchanged behaviour)
