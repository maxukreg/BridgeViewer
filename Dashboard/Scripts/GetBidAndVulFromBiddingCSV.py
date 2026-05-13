import os
import argparse
import sys
import re
from google import genai
from google.genai import types


# CONFIG
# API_KEY = "AIzaSyCLxt5NtOWios78YemBGg-hkvW6UuI8ofU"

API_KEY = "AIzaSyA-E_GQ5uUKZRsaecTFrpn_LXuNc_Q4yIE"
MODEL_NAME = "gemini-3.1-flash-preview"


def get_paths(script_dir: str, groupnum: str):
    sheets_root = os.path.normpath(os.path.join(script_dir, ".."))
    group_root = os.path.join(sheets_root, f"Group{groupnum}")
    booklet_pdf = os.path.join(group_root, "Booklet", "Deals", "Booklet.pdf")
    csv_folder = os.path.join(group_root, "CSV")
    bidding_csv = os.path.join(csv_folder, "bidding.csv")
    hands_csv = os.path.join(csv_folder, "HandsFromAI.csv")
    return booklet_pdf, csv_folder, bidding_csv, hands_csv


def run_gemini_bidding(booklet_pdf: str, bidding_csv: str, prompts_folder: str):
    prompt_file = os.path.join(prompts_folder, "GetBiddingAndDlrVulFromBooklet.txt")
    if not os.path.exists(prompt_file):
        print(f"ERROR: Prompt not found: {prompt_file}")
        sys.exit(1)
    if not os.path.exists(booklet_pdf):
        print(f"ERROR: Booklet.pdf not found: {booklet_pdf}")
        sys.exit(1)
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_text = f.read()
    print("Configuring Gemini...")
    client = genai.Client(api_key=API_KEY)
    print(f"Uploading Booklet.pdf: {booklet_pdf}")
    uploaded = client.files.upload(
        file=booklet_pdf, config={"mime_type": "application/pdf"}
    )
    print("Requesting bidding extraction from Gemini...")
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt_text, uploaded],
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=32768,
        ),
    )
    if not response.text:
        print("ERROR: No response from Gemini!")
        sys.exit(1)
    os.makedirs(os.path.dirname(bidding_csv), exist_ok=True)
    with open(bidding_csv, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"bidding.csv saved: {bidding_csv} ({len(response.text)} chars)")


def parse_vulnerability(vul_text):
    vul_lower = vul_text.lower()
    if "neither" in vul_lower:
        return "0"
    elif "both" in vul_lower:
        return "B"
    elif "north-south" in vul_lower and "not" not in vul_lower:
        return "N"
    elif "east-west" in vul_lower:
        return "E"
    return ""


def normalize_bid(bid):
    bid_lower = bid.lower().strip()
    if bid_lower.startswith("pass") or bid_lower in ["p", "pass"]:
        return "Pass"  # Capital P internally
    suit_map = {
        "hearts": "H",
        "heart": "H",
        "diamonds": "D",
        "diamond": "D",
        "clubs": "C",
        "club": "C",
        "spades": "S",
        "spade": "S",
    }
    for full, abbr in suit_map.items():
        bid_lower = re.sub(r"\b" + full + r"\b", abbr, bid_lower)
    double_map = {"double": "X", "dbl": "X", "redouble": "XX", "xx": "XX", "rdbl": "XX"}
    for full, abbr in double_map.items():
        if full in bid_lower:
            return abbr
    # Numbers + suits: '2 h' -> '2H'
    return re.sub(
        r"(\d+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), bid_lower.title()
    )


def parse_bidding_file(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip markdown code fences if Gemini added them
    content = re.sub(r"\n?```$", "", content.strip())

    deal_sections = re.split(r"(?i)deal[, ]", content)
    deals = {}
    for section in deal_sections[1:]:
        lines = [line.strip() for line in section.split("\n") if line.strip()]
        if len(lines) < 3:
            continue
        deal_num = lines[0].split(",")[0].strip()
        dealer_line = lines[1].strip()
        vul_line = lines[2].strip()
        dealer = ""
        if "North" in dealer_line:
            dealer = "N"
        elif "South" in dealer_line:
            dealer = "S"
        elif "East" in dealer_line:
            dealer = "E"
        elif "West" in dealer_line:
            dealer = "W"
        vul = parse_vulnerability(vul_line)

        bids = []
        for i in range(3, len(lines)):
            if lines[i].strip():
                raw_bids = [b.strip() for b in lines[i].split(",") if b.strip()]
                line_bids = [normalize_bid(b) for b in raw_bids]
                bids.extend(line_bids)

        deals[deal_num] = {"dealer": dealer, "vul": vul, "bids": bids}
    print(f"Parsed {len(deals)} deals from bidding.csv")
    return deals


def get_final_contract(bids):
    if not bids:
        return ""
    pass_count = 0
    for i in range(len(bids) - 1, -1, -1):
        bid_lower = bids[i].lower()
        if bid_lower.startswith("pass") or bid_lower in ["p", "pass"]:
            pass_count += 1
        else:
            pass_count = 0
        if pass_count == 3:
            orig_final_j = -1
            for j in range(i - 1, -1, -1):
                if not (
                    bids[j].lower().startswith("pass")
                    or bids[j].lower() in ["p", "pass"]
                ):
                    orig_final_j = j
                    break
            if orig_final_j == -1:
                return ""
            double_types = ["x", "xx", "double", "redouble", "dbl", "rdbl"]
            base_j = orig_final_j
            while base_j > 0:
                bid_check = bids[base_j].lower()
                if (
                    bid_check in double_types
                    or bid_check.startswith("pass")
                    or bid_check in ["p", "pass"]
                ):
                    base_j -= 1
                else:
                    break
            if base_j == 0:
                return bids[base_j]
            final_mult = ""
            for k in range(base_j + 1, i):
                mult_lower = bids[k].lower()
                if mult_lower in ["x", "double", "dbl"]:
                    final_mult = "X"
                elif mult_lower in ["xx", "redouble", "rdbl"]:
                    final_mult = "XX"
            return f"{bids[base_j]} {final_mult}".strip()
    return ""


def dealer_to_index(dealer):
    mapping = {"S": 0, "W": 1, "N": 2, "E": 3}
    return mapping.get(dealer, 0)


def rotate_calls_to_players(all_calls, start_dir):
    players = [[] for _ in range(4)]  # 0=N, 1=E, 2=S, 3=W
    dir_order = [2, 3, 0, 1]  # S=0->idx2, W=1->idx3, N=2->idx0, E=3->idx1
    for i, call in enumerate(all_calls):
        seat = (start_dir + i) % 4
        players[dir_order[seat]].append(call)
    return players  # [N, E, S, W]


def calls_to_csv_string(calls):
    short_calls = ["P" if c == "Pass" else c for c in calls]
    return ",".join(short_calls[:8])  # Your format: 1H,P,2H,2S,...


def update_output_file(output_file, groupnum, deals):
    with open(output_file, "rb") as f:
        data = f.read()
    data = data.replace(b"\r\r\n", b"\r\n")
    lines = data.split(b"\r\n")

    updated_count = 0

    for deal_num, deal_info in deals.items():
        for i, line in enumerate(lines):
            try:
                line_str = line.decode("utf-8")
            except Exception:
                continue
            parts = line_str.split(",")
            if (
                len(parts) >= 4
                and parts[0] == "Group"
                and parts[1] == str(groupnum)
                and parts[2] == "Deal"
                and parts[3] == str(deal_num)
            ):
                while len(parts) < 10:
                    parts.append("")

                # Group,[1],Deal,[3],Dealer,[5],Vul,[7],Contract,[9]
                parts[5] = deal_info["dealer"]
                parts[7] = deal_info["vul"]
                parts[9] = get_final_contract(deal_info["bids"])
                lines[i] = ",".join(parts).encode("utf-8")

                bids = deal_info["bids"]
                start_dir = dealer_to_index(deal_info["dealer"])
                players = rotate_calls_to_players(bids, start_dir)

                for k in range(4):
                    target = i + 9 + k
                    if target < len(lines):
                        lines[target] = calls_to_csv_string(players[k]).encode("utf-8")

                updated_count += 1
                break

    with open(output_file, "wb") as f:
        f.write(b"\r\n".join(lines))

    print(f"Updated {updated_count} deals in HandsFromAI.csv")


def interactive_mode():
    print("=== GetBidAndVulFromBiddingCSV Interactive Mode ===")
    group_num = input("Enter group number (e.g., 36): ").strip()
    if not group_num:
        print("ERROR: Group number required.")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_folder = os.path.join(script_dir, "..", "Prompts")
    booklet_pdf, csv_folder, bidding_csv, hands_csv = get_paths(script_dir, group_num)

    print(f"\nGroup {group_num}")
    print(f"Booklet PDF : {booklet_pdf}")
    print(f"bidding.csv : {bidding_csv}")
    print(f"HandsFromAI: {hands_csv}")

    if not os.path.exists(hands_csv):
        print(f"ERROR: HandsFromAI.csv not found: {hands_csv}")
        sys.exit(1)

    print("\n--- Step 1: Gemini extraction ---")
    run_gemini_bidding(booklet_pdf, bidding_csv, prompts_folder)

    print("\n--- Steps 2-3: Parse bidding.csv & update HandsFromAI.csv ---")
    deals = parse_bidding_file(bidding_csv)
    update_output_file(hands_csv, group_num, deals)

    print(f"\nGroup {group_num} complete!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", help="Group number e.g. 36", required=True)
    parser.add_argument("--prompts-folder", help="Path to Prompts folder")
    args = parser.parse_args()

    group_num = args.group
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_folder = args.prompts_folder or os.path.join(script_dir, "..", "Prompts")
    booklet_pdf, csv_folder, bidding_csv, hands_csv = get_paths(script_dir, group_num)

    print(f"Group {group_num}")
    print(f"Booklet PDF : {booklet_pdf}")
    print(f"bidding.csv : {bidding_csv}")
    print(f"HandsFromAI: {hands_csv}")

    if not os.path.exists(hands_csv):
        print(f"ERROR: HandsFromAI.csv not found: {hands_csv}")
        sys.exit(1)

    print("\n--- Step 1: Gemini extraction ---")
    run_gemini_bidding(booklet_pdf, bidding_csv, prompts_folder)

    print("\n--- Steps 2-3: Parse bidding.csv & update HandsFromAI.csv ---")
    deals = parse_bidding_file(bidding_csv)
    update_output_file(hands_csv, group_num, deals)

    print(f"\nGroup {group_num} complete!")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        main()
