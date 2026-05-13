"""
Bridge Hand Batch Processor v3.1 (crash-safe, dual-mode)
- Standalone (VSCode): uses tkinter GUI dialogs as before
- Dashboard (server.py): accepts --group and --csv-folder CLI args, no GUI needed
- Processes deals in batches (default 8) but WRITES OUTPUT DEAL-BY-DEAL
- Output is appended immediately after each successful deal, then images are moved to processed/
- Resume is safe: if a deal is in processed/, its lines are already in batchOutput.csv
- Uses google.genai (new SDK)
"""

from google import genai
from google.genai import types
import os
from pathlib import Path
import time
import re
import argparse
from datetime import datetime
import shutil
import sys
import io

# =========================
# Windows console encoding fix
# =========================
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

# =========================
# CONFIG
# =========================
API_KEY = "AIzaSyC_KUPrteqUuYhThnp1bLG35lo7zW_YlhU"
MODEL_NAME = "gemini-3.1-pro-preview"  # working confirmed
BATCH_SIZE = 8
PAUSE_BETWEEN_BATCHES_SEC = 2

APPEND_IF_OUTPUT_EXISTS = True

# =========================
# PRICING (USD per 1M tokens)
# =========================
FREE_TIER = False
TOKEN_THRESHOLD = 200_000
INPUT_COST_SHORT = 2.00
INPUT_COST_LONG = 4.00
OUTPUT_COST_SHORT = 12.00
OUTPUT_COST_LONG = 18.00


def calculate_cost(input_tokens: int, output_tokens: int) -> tuple[float, float, float]:
    """Return (input_cost, output_cost, total_cost) in USD."""
    if FREE_TIER:
        return 0.0, 0.0, 0.0
    if input_tokens <= TOKEN_THRESHOLD:
        ic = (input_tokens / 1_000_000) * INPUT_COST_SHORT
        oc = (output_tokens / 1_000_000) * OUTPUT_COST_SHORT
    else:
        ic = (input_tokens / 1_000_000) * INPUT_COST_LONG
        oc = (output_tokens / 1_000_000) * OUTPUT_COST_LONG
    return ic, oc, ic + oc


def load_prompt(prompts_folder: str, prompt_name: str) -> str:
    prompt_file = os.path.join(prompts_folder, prompt_name)
    if not os.path.exists(prompt_file):
        print(f"ERROR: Prompt not found: {prompt_file}")
        sys.exit(1)
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()


# =========================
# GUI helpers (only used in standalone mode)
# =========================
def _import_tkinter():
    """Lazy import of tkinter so that headless runs never touch it."""
    import tkinter as tk
    from tkinter import simpledialog, messagebox, filedialog

    return tk, simpledialog, messagebox, filedialog


def get_group_number():
    tk, simpledialog, messagebox, _ = _import_tkinter()
    root = tk.Tk()
    root.withdraw()

    while True:
        group_num = simpledialog.askstring(
            "Bridge Hand Processor",
            "Enter Group number (e.g., 35):",
            parent=root,
        )
        if group_num is None:
            root.destroy()
            return None
        if group_num.strip().isdigit():
            root.destroy()
            return group_num.strip()
        messagebox.showerror(
            "Invalid Input", "Please enter a valid number", parent=root
        )


def browse_csv_folder(group_num: str) -> Path | None:
    tk, _, _, filedialog = _import_tkinter()
    root = tk.Tk()
    root.withdraw()
    csv_folder = filedialog.askdirectory(
        title=f"Select CSV folder for Group {group_num}",
        mustexist=True,
    )
    root.destroy()
    return Path(csv_folder) if csv_folder else None


# =========================
# Folder logic
# =========================
def get_image_folder_from_csv(csv_folder: Path) -> Path:
    group_folder = csv_folder.parent
    return group_folder / "images" / "ModScans"


def backup_existing_files(csv_folder: Path):
    backup_folder = csv_folder / "backup"
    backup_folder.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files_to_backup = ["HandsFromAI.csv", "HandsTemp.csv", "batchOutput.csv"]

    print("\n" + "=" * 70)
    print("BACKING UP EXISTING FILES")
    print("=" * 70 + "\n")

    backed_up = 0
    for filename in files_to_backup:
        src = csv_folder / filename
        if not src.exists():
            print(f"  Skipped: {filename} (does not exist)")
            continue

        stem, dot, ext = filename.partition(".")
        if dot:
            dst_name = f"{stem}_{timestamp}.{ext}"
        else:
            dst_name = f"{filename}_{timestamp}"

        dst = backup_folder / dst_name
        try:
            shutil.copy2(src, dst)
            print(f"  Backed up: {filename} -> backup/{dst_name}")
            backed_up += 1
        except Exception as e:
            print(f"  Warning: Could not backup {filename}: {e}")

    print(f"\nBacked up {backed_up} file(s)")
    print("=" * 70 + "\n")


# =========================
# Pairing logic
# =========================
def is_image_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".pdf"]


def get_image_pairs_from_folder(modscans_folder: Path, group_num: str):
    if not modscans_folder.exists():
        print(f"\nERROR: Image folder not found: {modscans_folder}")
        return []

    all_images = sorted([p for p in modscans_folder.iterdir() if is_image_file(p)])

    if not all_images:
        print(f"\nERROR: No images found in {modscans_folder}")
        return []

    ew_images = [f for f in all_images if "EW" in f.name.upper()]
    ns_images = [f for f in all_images if "NS" in f.name.upper()]

    print(f"\nFound {len(all_images)} images in ModScans folder")
    print(f"EW images: {len(ew_images)}")
    print(f"NS images: {len(ns_images)}")

    pairs = []
    ns_by_key = {}

    for ns in ns_images:
        m = re.search(r"m-\d+-(\d+)-NS", ns.name, re.IGNORECASE)
        if not m:
            continue
        deal = int(m.group(1))
        ns_by_key[deal] = ns

    for ew in ew_images:
        m = re.search(r"m-\d+-(\d+)-EW", ew.name, re.IGNORECASE)
        if not m:
            continue
        deal = int(m.group(1))
        ns = ns_by_key.get(deal)
        if ns:
            pairs.append(
                {
                    "deal": deal,
                    "image1": str(ew),
                    "image2": str(ns),
                    "ew_name": ew.name,
                    "ns_name": ns.name,
                }
            )

    pairs.sort(key=lambda x: x["deal"])
    return pairs


# =========================
# Output parsing + durable write
# =========================
def extract_nine_lines(output_text: str):
    lines = output_text.splitlines()
    in_code = False
    out = []

    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code and s:
            out.append(s)
            if len(out) >= 9:
                break

    return out


def validate_deal_header(header_line: str) -> bool:
    """Return True only if the header matches the strict Group,X,Deal,Y format."""
    return bool(re.match(r"^Group,\d+,Deal,\d+$", header_line.strip()))


def write_deal_lines(output_file: Path, deal_lines: list[str]):
    header = deal_lines[0].strip()  # first line: "Group,35,Deal,1"
    existing_lines: list[str] = []
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    found_at: int | None = None
    for i, line in enumerate(existing_lines):
        if line.strip() == header:
            found_at = i
            break

    new_block = [line + "\n" for line in deal_lines]

    if found_at is not None:
        existing_lines[found_at : found_at + 9] = new_block
        action = "Overwrote"
    else:
        if existing_lines and not existing_lines[-1].endswith("\n"):
            existing_lines[-1] += "\n"
        existing_lines.extend(new_block)
        action = "Appended"

    tmp_file = output_file.with_suffix(".tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.writelines(existing_lines)
        f.flush()
        os.fsync(f.fileno())
    tmp_file.replace(output_file)

    print(f" {action} deal block for: {header}")


def response_to_text(resp) -> str:
    txt = getattr(resp, "text", None)
    if txt:
        return txt
    try:
        parts = resp.candidates.content.parts
        return "".join(getattr(p, "text", "") for p in parts if getattr(p, "text", ""))
    except Exception:
        return str(resp)


# =========================
# Main
# =========================
def process_bridge_hands(group_num=None, csv_folder_str=None):
    headless = (group_num is not None) and (csv_folder_str is not None)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_folder = os.path.join(script_dir, "..", "Prompts")
    prompt = load_prompt(prompts_folder, "GeminiGetHandsFromImage.txt")

    print("=" * 80)
    print("BRIDGE HAND BATCH PROCESSOR v3.1 - crash-safe (deal-by-deal output)")
    print("=" * 80)

    if headless:
        csv_folder = Path(csv_folder_str)
        print(f"Headless mode: group={group_num}, csv_folder={csv_folder}")
    else:
        group_num = get_group_number()
        if group_num is None:
            print("Cancelled.")
            return
        csv_folder = browse_csv_folder(group_num)
        if csv_folder is None:
            print("No CSV folder selected. Cancelled.")
            return

    image_folder = get_image_folder_from_csv(csv_folder)

    print(f"\nCSV folder: {csv_folder}")
    print(f"Derived image folder: {image_folder}")
    print(f"Image folder exists? {image_folder.exists()}")

    if not image_folder.exists():
        msg = f"Image folder not found:\n{image_folder}"
        print(f"ERROR: {msg}")
        if not headless:
            _, _, messagebox, _ = _import_tkinter()
            messagebox.showerror("Error", msg)
        return

    backup_existing_files(csv_folder)

    pairs = get_image_pairs_from_folder(image_folder, group_num)
    if not pairs:
        msg = f"No image pairs found in Group {group_num}"
        print(f"ERROR: {msg}")
        if not headless:
            _, _, messagebox, _ = _import_tkinter()
            messagebox.showerror("Error", msg)
        return

    output_file = csv_folder / "batchOutput.csv"
    resume_file = csv_folder / "last_batch.txt"

    output_exists = output_file.exists()
    is_resume_run = output_exists and APPEND_IF_OUTPUT_EXISTS

    if not is_resume_run:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("")
        print("\nStarting fresh: cleared batchOutput.csv")
    else:
        print("\nResume run: will append/overwrite deals in batchOutput.csv")

    start_batch = 0
    if resume_file.exists():
        try:
            start_batch = int(resume_file.read_text(encoding="utf-8").strip())
            print(f"RESUME: Starting from batch {start_batch + 1}")
        except Exception:
            start_batch = 0

    total_batches = (len(pairs) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nFound {len(pairs)} boards to process")
    print(f"Processing {len(pairs)} boards in {total_batches} batches of {BATCH_SIZE}")

    # Initialise new SDK client
    client = genai.Client(api_key=API_KEY)

    processed_folder = image_folder / "processed"
    processed_folder.mkdir(exist_ok=True)

    start_time = datetime.now()
    failed_deals_all = []
    malformed_deals = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0

    for batch_num in range(start_batch, total_batches):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, len(pairs))
        batch_pairs = pairs[batch_start:batch_end]

        print("\n" + "=" * 80)
        print(
            f"BATCH {batch_num + 1}/{total_batches} | "
            f"Deals {batch_pairs[0]['deal']}-{batch_pairs[-1]['deal']} | "
            f"{batch_start + 1}-{batch_end}/{len(pairs)}"
        )
        print("=" * 80)

        for idx, pair in enumerate(batch_pairs, 1):
            global_progress = batch_start + idx
            deal_num = pair["deal"]

            print(
                f"[{global_progress}/{len(pairs)}] [{idx}/{len(batch_pairs)}] Deal {deal_num}..."
            )

            image1 = None
            image2 = None
            output_text = None
            hand_start = time.time()

            max_retries = 5
            retry_count = 0
            success = False

            while retry_count < max_retries and not success:
                try:
                    if retry_count == 0:
                        image1 = client.files.upload(file=pair["image1"])
                        image2 = client.files.upload(file=pair["image2"])
                        time.sleep(1)

                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[prompt, image1, image2],
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            top_p=0.95,
                            top_k=40,
                            max_output_tokens=8192,
                        ),
                    )

                    output_text = response_to_text(response)
                    hand_elapsed = time.time() - hand_start

                    usage = getattr(response, "usage_metadata", None)
                    hand_input_tok = getattr(usage, "prompt_token_count", 0) or 0
                    hand_output_tok = getattr(usage, "candidates_token_count", 0) or 0
                    ic, oc, tc = calculate_cost(hand_input_tok, hand_output_tok)
                    total_input_tokens += hand_input_tok
                    total_output_tokens += hand_output_tok
                    total_cost_usd += tc

                    cost_str = "$0.00 (free tier)" if FREE_TIER else f"${tc:.6f}"
                    print(
                        f"  Time: {hand_elapsed:.1f}s | "
                        f"Tokens in: {hand_input_tok:,} out: {hand_output_tok:,} | "
                        f"Cost: {cost_str}"
                    )

                    success = True

                except Exception as e:
                    retry_count += 1
                    msg = str(e)
                    if (
                        "503" in msg or "unavailable" in msg.lower()
                    ) and retry_count < max_retries:
                        wait_time = 3 * retry_count
                        print(f"  Retry {retry_count}/{max_retries} in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        print(f"  FAILED Deal {deal_num}: {msg}")
                        failed_deals_all.append(deal_num)
                        break

            if success and output_text:
                nine_lines = extract_nine_lines(output_text)
                if len(nine_lines) != 9:
                    (csv_folder / f"debug_deal_{deal_num}.txt").write_text(
                        output_text, encoding="utf-8"
                    )
                    failed_deals_all.append(deal_num)
                    print(
                        f"  MALFORMED Deal {deal_num}: expected 9 lines, got {len(nine_lines)}"
                    )
                elif not validate_deal_header(nine_lines[0]):
                    (csv_folder / f"debug_deal_{deal_num}.txt").write_text(
                        output_text, encoding="utf-8"
                    )
                    failed_deals_all.append(deal_num)
                    print(
                        f"  MALFORMED Deal {deal_num}: bad header format '{nine_lines[0]}' "
                        f"(expected Group,X,Deal,Y)"
                    )
                else:
                    write_deal_lines(output_file, nine_lines)
                    try:
                        shutil.move(
                            pair["image1"], str(processed_folder / pair["ew_name"])
                        )
                        shutil.move(
                            pair["image2"], str(processed_folder / pair["ns_name"])
                        )
                    except Exception as e:
                        print(f"  Warning: output saved but could not move images: {e}")

            # Clean up uploaded files
            try:
                if image1:
                    client.files.delete(name=image1.name)
                if image2:
                    client.files.delete(name=image2.name)
            except Exception:
                pass

            time.sleep(1)

        # Update resume tracker at end of each batch
        try:
            resume_file.write_text(str(batch_num + 1), encoding="utf-8")
        except Exception as e:
            print(f"Warning: could not update resume file: {e}")

        if batch_num < total_batches - 1 and PAUSE_BETWEEN_BATCHES_SEC:
            print(f"Pausing {PAUSE_BETWEEN_BATCHES_SEC} seconds before next batch...")
            time.sleep(PAUSE_BETWEEN_BATCHES_SEC)

    # Clean up resume file
    try:
        if resume_file.exists():
            resume_file.unlink()
    except Exception:
        pass

    end_time = datetime.now()
    elapsed = end_time - start_time
    mins = int(elapsed.total_seconds() // 60)
    secs = int(elapsed.total_seconds() % 60)

    print("\n" + "=" * 80)
    print("ALL BATCHES COMPLETE!")
    print(f"Results saved to: {output_file}")
    print(f"Time taken: {mins}m {secs}s")
    print(f"\n--- Token Usage (all hands) ---")
    print(f"  Total input tokens : {total_input_tokens:,}")
    print(f"  Total output tokens: {total_output_tokens:,}")
    print(f"  Total tokens       : {total_input_tokens + total_output_tokens:,}")
    if FREE_TIER:
        print(f"  Total cost         : $0.00 (free preview tier)")
    else:
        _, _, run_total = calculate_cost(total_input_tokens, total_output_tokens)
        print(f"  Total cost         : ${total_cost_usd:.4f} USD")

    failed_unique = sorted(set(failed_deals_all))
    malformed_unique = sorted(set(malformed_deals))

    if not failed_unique and not malformed_unique:
        print(f"All {len(pairs)} deals processed successfully. No action needed.")
    else:
        print(f"Succeeded : {len(pairs) - len(failed_unique)}/{len(pairs)}")
        print("\nACTION NEEDED:")
        for d in failed_unique:
            print(
                f"  RERUN - Deal {d}: move images back to ModScans/ and rerun "
                f"(check debug_deal_{d}.txt for AI output)"
            )
        for d in malformed_unique:
            print(
                f"  FIX CSV - Deal {d}: malformed header (auto-corrected if Option 2 applied)"
            )

    print("=" * 80)

    if headless:
        pass
    else:
        tk, _, messagebox, _ = _import_tkinter()
        root = tk.Tk()
        root.withdraw()
        root.lift()
        root.attributes("-topmost", True)
        root.after_idle(root.attributes, "-topmost", False)
        root.update()

        msg = f"Done.\n\nOutput:\n{output_file}\n\nTime: {mins}m {secs}s"
        if failed_deals_all:
            msg += f"\n\nFailed deals: {', '.join(map(str, sorted(set(failed_deals_all))))}"
        messagebox.showinfo("Processing Complete", msg, parent=root)
        root.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bridge Hand Batch Processor")
    parser.add_argument("--group", default=None, help="Group number (e.g. 35)")
    parser.add_argument(
        "--csv-folder",
        default=None,
        help="Full path to the CSV folder for this group",
    )
    args = parser.parse_args()

    if bool(args.group) != bool(args.csv_folder):
        print("ERROR: --group and --csv-folder must both be provided, or neither.")
        sys.exit(1)

    try:
        process_bridge_hands(
            group_num=args.group,
            csv_folder_str=args.csv_folder,
        )
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
