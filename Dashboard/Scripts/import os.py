import os
import argparse
import google.generativeai as genai
import sys
import win32com.client
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)


# Windows console encoding fix (works with/without subprocess capture)
if hasattr(sys.stdout, "buffer"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

# CONFIG
API_KEY = "AIzaSyCLxt5NtOWios78YemBGg-hkvW6UuI8ofU"
MODEL_NAME = "gemini-3-flash-preview"


def get_group_folder(script_dir: str, group_num: str) -> str:
    """Find GroupXX/Deals folder using --group or auto-detect."""
    if group_num:
        print(f"Using group from dashboard: {group_num}")
        sheets_root = os.path.join(script_dir, "..")
        group_folder = os.path.join(
            sheets_root, f"Group{group_num}", "Booklet", "Deals"
        )
        print(f"Looking for Deals folder: {group_folder}")
        if os.path.exists(group_folder):
            return group_folder
        else:
            print(f"Group{group_num}/Deals not found at {group_folder}")
            sys.exit(1)

    # Fallback: auto-detect from existing GroupXX folders
    sheets_root = os.path.join(script_dir, "..")
    for folder in os.listdir(sheets_root):
        if folder.startswith("Group") and os.path.isdir(
            os.path.join(sheets_root, folder)
        ):
            group_folder = os.path.join(sheets_root, folder, "Deals")
            if os.path.exists(group_folder):
                group_num = folder
                print(f"Auto-detected Group: {group_num}")
                return group_folder
    print("No GroupXX/Deals folder found!")
    sys.exit(1)


def load_prompt(prompts_folder: str, prompt_name: str) -> str:
    prompt_file = os.path.join(prompts_folder, prompt_name)
    if not os.path.exists(prompt_file):
        print(f"ERROR: Prompt not found: {prompt_file}")
        sys.exit(1)
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()


def run_transcription(group_num: str, pdf_path: str, prompts_folder: str):
    """Core transcription logic shared by both interactive and CLI modes."""
    print(f"Processing Group {group_num}: {pdf_path}")

    # Load prompt
    prompt_text = load_prompt(prompts_folder, "TranscribeBookletFromPDF.txt")

    # Gemini processing
    print("Configuring Gemini...")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    print("Uploading PDF...")
    uploaded = genai.upload_file(pdf_path, mime_type="application/pdf")

    print("Generating transcription...")
    response = model.generate_content(
        [prompt_text, uploaded],
        generation_config={"temperature": 0.2, "max_output_tokens": 65536},
        request_options={"timeout": 600},
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
    import re

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
            # Check if this line and the next are separated by exactly one blank
            # line and both look like "block" lines (short, no trailing period).
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
                # Merge: output this line, skip the blank, continue loop
                # (next iteration will pick up lines[i+2])
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

    # Save outputs
    deals_dir = os.path.dirname(pdf_path)
    text_out = os.path.join(deals_dir, "Booklet.txt")
    output_pdf = os.path.join(deals_dir, "Booklet.pdf")

    with open(text_out, "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"Saved raw text: {text_out}")

    # Word → PDF
    print("Creating PDF via Word...")
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        # Close any already-open Booklet.docx to avoid naming conflict
        temp_docx = os.path.abspath(os.path.join(deals_dir, "Booklet.docx"))
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
    group_num = input("Enter group number (e.g., 36): ").strip()
    if not group_num:
        print("ERROR: Group number required.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_folder = os.path.join(script_dir, "..", "Prompts")

    print(f"Using prompts folder: {prompts_folder}")

    group_folder = get_group_folder(script_dir, group_num)
    pdf_path = os.path.join(group_folder, "BookletImagesSplit.pdf")

    print(f"\nBookletTranscribe - Group {group_num}")
    print(f"PDF path: {pdf_path}")
    print(f"Prompts folder: {prompts_folder}")

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    run_transcription(group_num, pdf_path, prompts_folder)
    print(f"\nGroup {group_num} complete!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-path", help="Direct PDF from dashboard")
    parser.add_argument("--base-dir", default=".", help="Base directory")
    parser.add_argument("--prompts-folder", help="Folder containing prompt files")
    parser.add_argument("--group", help="Group number")
    args = parser.parse_args()

    print("BookletTranscribe.py started from dashboard")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")

    group_folder = get_group_folder(script_dir, args.group)
    pdf_path = args.pdf_path or os.path.join(group_folder, "BookletImagesSplit.pdf")

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    group_num = args.group or os.path.basename(os.path.dirname(group_folder))
    prompts_folder = args.prompts_folder or os.path.join(script_dir, "..", "Prompts")

    run_transcription(group_num, pdf_path, prompts_folder)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) == 1:  # No command line args → interactive/VSCode mode
        interactive_mode()
    else:
        main()  # Dashboard CLI mode (unchanged behaviour)
