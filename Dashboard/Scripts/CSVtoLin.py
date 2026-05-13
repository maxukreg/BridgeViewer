import os
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
import re
from pathlib import Path

# --- Configuration ---
home_dir = Path.home()
one_drive_folder = next(home_dir.glob("OneDrive*"), home_dir)
BASE_DIR = (
    one_drive_folder / "Software" / "Projects" / "Handviewer" / "Autobridge" / "Sheets"
)

# --- Helper Functions (Card/Game Logic) ---


def get_card_rank(card_str):
    ranks = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "T": 10,
        "J": 11,
        "Q": 12,
        "K": 13,
        "A": 14,
    }
    return ranks[card_str[0].upper()]


def get_card_suit(card_str):
    return card_str[1].upper()


def get_play_sequence(leader_pos):
    positions = {
        "West": ["West", "North", "East", "South"],
        "North": ["North", "East", "South", "West"],
        "East": ["East", "South", "West", "North"],
        "South": ["South", "West", "North", "East"],
    }
    return positions[leader_pos]


def get_position_index(position_str):
    return {"North": 0, "South": 1, "East": 2, "West": 3}[position_str]


def format_hand_for_lin(cards_list):
    suits = {"S": [], "H": [], "D": [], "C": []}
    for card in cards_list:
        rank, suit = card[0], card[1].upper()
        suits[suit].append(rank)

    formatted_str = ""
    for suit_char in ["S", "H", "D", "C"]:
        if suits[suit_char]:
            formatted_str += suit_char + "".join(
                sorted(
                    suits[suit_char], key=lambda x: "AKQJT98765432".index(x[0].upper())
                )
            )
    return formatted_str


def find_card_by_sequence(hand_cards, play_sequences, sequence_num):
    for card, play_num in zip(hand_cards, play_sequences):
        if play_num == sequence_num:
            return card
    return None


def determine_trick_winner(trick_played_cards, lead_suit_char, trump_suit_char):
    highest_rank_val = -1
    winner_pos = None
    trump_played_in_trick = False

    if trump_suit_char:
        for pos, card in trick_played_cards:
            if get_card_suit(card) == trump_suit_char:
                if not trump_played_in_trick or get_card_rank(card) > highest_rank_val:
                    highest_rank_val, winner_pos, trump_played_in_trick = (
                        get_card_rank(card),
                        pos,
                        True,
                    )

    if not trump_played_in_trick:
        highest_rank_val = -1
        for pos, card in trick_played_cards:
            if get_card_suit(card) == lead_suit_char:
                if get_card_rank(card) > highest_rank_val:
                    highest_rank_val, winner_pos = get_card_rank(card), pos
    return winner_pos


def get_played_cards_lin_sequence(
    all_hands_data, all_plays_data, initial_leader, trump_suit_char
):
    lin_play_sequence = []
    current_leader_pos = initial_leader

    for trick_num in range(1, 14):
        trick_cards_played = []
        play_order = get_play_sequence(current_leader_pos)
        lead_card = None

        for player_pos in play_order:
            player_idx = get_position_index(player_pos)
            card_played = find_card_by_sequence(
                all_hands_data[player_idx], all_plays_data[player_idx], trick_num
            )

            if card_played:
                suit_char, rank_char = card_played[1].upper(), card_played[0].upper()
                trick_cards_played.append((player_pos, card_played))
                lin_play_sequence.append(f"pc|{suit_char}{rank_char}|")
                if len(trick_cards_played) == 1:
                    lead_card = card_played

        if trick_cards_played:
            lin_play_sequence.append("pg||")
            if len(trick_cards_played) == 4:
                current_leader_pos = determine_trick_winner(
                    trick_cards_played, get_card_suit(lead_card), trump_suit_char
                )
        else:
            break
    return lin_play_sequence


def organize_bids_in_rotation(biddingdatadict, dealerposchar):
    organizedbids = []
    player_order = ["North", "East", "South", "West"]
    dealer_fullname = {"N": "North", "E": "East", "S": "South", "W": "West"}[
        dealerposchar.upper()
    ]

    start_idx = player_order.index(dealer_fullname)
    rotation = player_order[start_idx:] + player_order[:start_idx]

    # Create pointers for each player's bid list
    bid_indices = {player: 0 for player in player_order}

    # Interleave bids in rotation order
    while True:
        added_any = False
        for player in rotation:
            playerbids = biddingdatadict.get(player, [])
            if bid_indices[player] < len(playerbids):
                organizedbids.append(playerbids[bid_indices[player]])
                bid_indices[player] += 1
                added_any = True

        if not added_any:
            break

    return organizedbids


def parse_trump_suit_from_contract(contract_str):
    if not contract_str:
        return None
    c_upper = contract_str.upper()
    if "N" in c_upper:
        return None
    for s in ["S", "H", "D", "C"]:
        if s in c_upper:
            return s
    return None


def map_vul_to_lin(csv_vul_char):
    return {"0": "o", "N": "n", "E": "e", "B": "b"}.get(csv_vul_char.upper(), "o")


def get_declarer_from_bidding(organized_bids, dealer_char, trump_suit_char):
    positions = ["North", "East", "South", "West"]
    dealer_name = {"N": "North", "E": "East", "S": "South", "W": "West"}[
        dealer_char.upper()
    ]
    start_idx = positions.index(dealer_name)
    rotation = positions[start_idx:] + positions[:start_idx]

    for i, bid in enumerate(organized_bids):
        bid_upper = bid.upper().strip()
        if bid_upper in ["P", "X", "XX"]:
            continue
        if trump_suit_char is None:
            if "N" in bid_upper:
                return rotation[i % 4]
        else:
            if trump_suit_char in bid_upper:
                return rotation[i % 4]
    return "South"


def get_opening_leader(declarer_name):
    return {"North": "East", "East": "South", "South": "West", "West": "North"}[
        declarer_name
    ]


# --- File Processing ---


def is_deal_fully_populated(deal_block):
    if len(deal_block) < 13:
        return False
    for i in range(1, 9):
        if not deal_block[i].strip().replace(",", "").replace('"', "").strip():
            return False
    return True


def read_deals_from_ai_csv(group_csv_path):
    """
    Reads deals from CSV with improved error handling.
    Returns: (deal_numbers, all_deals_data, skipped_deals)
    """
    deal_numbers = []
    all_deals_data = []
    skipped_deals = []

    if not os.path.exists(group_csv_path):
        return [], [], []

    try:
        with open(group_csv_path, "r") as f:
            lines = [
                line.strip().replace('"', "") for line in f.readlines() if line.strip()
            ]

        i = 0
        while i < len(lines):
            # Look for a header line (starts with "Group,")
            if not lines[i].startswith("Group,"):
                i += 1
                continue

            # Extract deal number from header
            header_parts = lines[i].split(",")
            if len(header_parts) <= 3:
                i += 1
                continue

            deal_num = header_parts[3]

            # Collect the next 12 lines (should be hands + bidding)
            deal_block = [lines[i]]
            j = i + 1
            while j < len(lines) and len(deal_block) < 13:
                # Stop if we hit another header
                if lines[j].startswith("Group,"):
                    break
                deal_block.append(lines[j])
                j += 1

            # Check if this deal is complete
            if is_deal_fully_populated(deal_block):
                all_deals_data.append(list(deal_block))
                deal_numbers.append(deal_num)
            else:
                # Record incomplete deal
                skipped_deals.append(
                    {
                        "deal_num": deal_num,
                        "lines_found": len(deal_block),
                        "reason": f"Incomplete deal (expected 13 lines, found {len(deal_block)})",
                    }
                )

            # Move to next potential deal
            i = j

    except Exception as e:
        return [], [], [{"error": str(e)}]

    return deal_numbers, all_deals_data, skipped_deals


def create_lin_file_for_deal(deal_data_lines, output_lin_path, group_num_str):
    """Creates a .lin file using the absolute BBO Standard: South, West, North."""
    deal_id_str_for_error = "UnknownDeal"
    if deal_data_lines and deal_data_lines[0]:
        try:
            header_parts_for_error = deal_data_lines[0].split(",")
            if len(header_parts_for_error) > 3:
                deal_id_str_for_error = header_parts_for_error[3]
        except:
            pass

    try:
        # 1. Parse Header
        header_fields = deal_data_lines[0].split(",")
        deal_num_str = header_fields[3]
        dealer_char = header_fields[5].upper()
        lin_vul_str = map_vul_to_lin(header_fields[7])
        contract_str = header_fields[9]
        trump_suit_char = parse_trump_suit_from_contract(contract_str)

        # Mapping for the 'md' tag (1=S, 2=W, 3=N, 4=E)
        dealer_to_num = {"S": "1", "W": "2", "N": "3", "E": "4"}
        numeric_dealer = dealer_to_num.get(dealer_char, "1")

        # 2. Parse Hands (CSV order is North:0, South:1, East:2, West:3)
        parsed_hands = [[] for _ in range(4)]
        parsed_plays = [[] for _ in range(4)]
        row_map = {0: 1, 1: 3, 2: 5, 3: 7}
        for i in range(4):
            parsed_hands[i] = [
                c.strip() for c in deal_data_lines[row_map[i]].split(",") if c.strip()
            ]
            parsed_plays[i] = [
                int(p.strip())
                for p in deal_data_lines[row_map[i] + 1].split(",")
                if p.strip()
            ]

        # 3. Construct LIN
        # BBO STANDARD: Hand 1 is ALWAYS South, Hand 2 is ALWAYS West, Hand 3 is ALWAYS North.
        lin_content = f"qx|o{deal_num_str}|md|{numeric_dealer}"
        lin_content += f"{format_hand_for_lin(parsed_hands[1])},"  # Slot 1: South
        lin_content += f"{format_hand_for_lin(parsed_hands[3])},"  # Slot 2: West
        lin_content += f"{format_hand_for_lin(parsed_hands[0])}"  # Slot 3: North
        lin_content += "|"

        lin_content += (
            f"rh|Group {group_num_str}|ah|Board {deal_num_str}|sv|{lin_vul_str}|"
        )

        # 4. Bidding
        bidding_dict = {
            "North": [
                b.strip().upper() for b in deal_data_lines[9].split(",") if b.strip()
            ],
            "East": [
                b.strip().upper() for b in deal_data_lines[10].split(",") if b.strip()
            ],
            "South": [
                b.strip().upper() for b in deal_data_lines[11].split(",") if b.strip()
            ],
            "West": [
                b.strip().upper() for b in deal_data_lines[12].split(",") if b.strip()
            ],
        }
        organized_bids = organize_bids_in_rotation(bidding_dict, dealer_char)

        for bid in organized_bids:
            b = bid.strip().upper()
            if b == "P":
                lin_content += "mb|p|"
            elif b == "X":
                lin_content += "mb|d|"
            elif b == "XX":
                lin_content += "mb|r|"
            else:
                lin_content += f"mb|{b}|"
        lin_content += "pg||"

        # 5. Play Sequence
        meaningful_bids = [
            b for b in organized_bids if b.upper() not in ["P", "X", "XX"]
        ]
        if meaningful_bids:
            declarer_name = get_declarer_from_bidding(
                organized_bids, dealer_char, trump_suit_char
            )
            opening_leader = get_opening_leader(declarer_name)

            play_seq = get_played_cards_lin_sequence(
                parsed_hands, parsed_plays, opening_leader, trump_suit_char
            )
            if play_seq:
                lin_content += "".join(play_seq)

        if not lin_content.endswith("|"):
            lin_content += "|"

        with open(output_lin_path, "w", encoding="utf-8") as f:
            f.write(lin_content)

        return True, f"LIN created: {output_lin_path}", lin_content

    except Exception as e:
        return False, f"Error processing Deal {deal_id_str_for_error}: {str(e)}", None


# --- JS Update ---


def update_js_file(group_num_str, deal_num_str, raw_lin_string):
    group_num = int(group_num_str)
    deal_start, deal_end = (33, 64) if group_num % 2 == 0 else (1, 32)
    js_file_path = os.path.join(
        BASE_DIR, f"Group{group_num_str}", "Lin", f"group{group_num_str}.js"
    )
    os.makedirs(os.path.dirname(js_file_path), exist_ok=True)

    current_query = f"bbo=y&lin={raw_lin_string}"
    deal_id = f"Group{group_num_str}Deal{deal_num_str}"

    if not os.path.exists(js_file_path):
        entries = [
            f'    {{\n        "id": "Group{group_num_str}Deal{i}",\n        "query": "{current_query if str(i)==deal_num_str else ""}"\n    }}'
            for i in range(deal_start, deal_end + 1)
        ]
        content = (
            f"const group{group_num_str}Data = [\n" + ",\n".join(entries) + "\n];\n\n"
        )
        with open(js_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, "JS Created"
    else:
        with open(js_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = re.compile(
            r'("id":\s*"' + re.escape(deal_id) + r'"\s*,\s*"query":\s*")[^"]*(")'
        )
        new_content, count = pattern.subn(
            lambda m: m.group(1) + current_query + m.group(2), content
        )
        if count > 0:
            with open(js_file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, "JS Updated"
        return False, "Placeholder missing"


# --- Main App Class (GUI) ---


class CSVtoLinApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("CSV to LIN Converter")
        self.root.geometry("550x500")
        (
            self.all_deals_data,
            self.current_group_num,
            self.selected_deal_num,
            self.process_all_var,
        ) = ([], tk.StringVar(), tk.StringVar(), tk.BooleanVar(value=False))

        # Group Frame
        gf = ttk.LabelFrame(self.root, text="Group Selection", padding="10")
        gf.pack(padx=10, pady=10, fill="x")
        ttk.Label(gf, text="Group:").pack(side=tk.LEFT)
        ttk.Entry(gf, textvariable=self.current_group_num, width=10).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(gf, text="Load", command=self.load_deals).pack(side=tk.LEFT)

        # Deal Frame
        df = ttk.LabelFrame(self.root, text="Deal Selection", padding="10")
        df.pack(padx=10, pady=5, fill="x")
        self.cb = ttk.Combobox(
            df, textvariable=self.selected_deal_num, state="readonly", width=10
        )
        self.cb.pack(side=tk.LEFT)
        ttk.Checkbutton(
            df,
            text="Process All",
            variable=self.process_all_var,
            command=self.toggle_cb,
        ).pack(side=tk.LEFT, padx=10)

        # Action
        ttk.Button(self.root, text="Process", command=self.process).pack(pady=10)

        # Log area
        log_frame = ttk.LabelFrame(self.root, text="Processing Log", padding="10")
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        ).pack(side=tk.BOTTOM, fill="x")

    def log(self, message):
        """Add message to log window"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def toggle_cb(self):
        self.cb.config(state="disabled" if self.process_all_var.get() else "readonly")

    def load_deals(self):
        g = self.current_group_num.get().strip()
        if not g.isdigit():
            return
        path = os.path.join(BASE_DIR, f"Group{g}", "CSV", "HandsFromAI.csv")
        nums, self.all_deals_data, skipped = read_deals_from_ai_csv(path)
        self.cb["values"] = nums
        if nums:
            self.selected_deal_num.set(nums[0])

        self.log_text.delete(1.0, tk.END)
        self.log(f"Loaded {len(nums)} complete deals from {path}")

        if skipped:
            self.log(f"\nWARNING: {len(skipped)} deal(s) were skipped:")
            for skip in skipped:
                if "error" in skip:
                    self.log(f"  ERROR: {skip['error']}")
                else:
                    self.log(f"  Deal {skip['deal_num']}: {skip['reason']}")

        self.status_var.set(f"Loaded {len(nums)} deals, skipped {len(skipped)}")

    def process(self):
        g = self.current_group_num.get().strip()
        if not g or not self.all_deals_data:
            return

        to_process = (
            self.all_deals_data
            if self.process_all_var.get()
            else [
                d
                for d in self.all_deals_data
                if d[0].split(",")[3] == self.selected_deal_num.get()
            ]
        )

        self.log("\n=== Starting Processing ===")
        success_count = 0
        error_count = 0

        for deal in to_process:
            d_num = deal[0].split(",")[3]
            path = os.path.join(
                BASE_DIR, f"Group{g}", "Lin", f"Group{g}Deal{d_num}.lin"
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)

            success, msg, raw_lin = create_lin_file_for_deal(deal, path, g)
            if success and raw_lin:
                update_js_file(g, d_num, raw_lin)
                self.log(f"✓ Deal {d_num}: Success")
                success_count += 1
            else:
                self.log(f"✗ Deal {d_num}: {msg}")
                error_count += 1

        summary = (
            f"\n=== Complete: {success_count} successful, {error_count} errors ==="
        )
        self.log(summary)
        messagebox.showinfo(
            "Done",
            f"Processing Complete\n{success_count} successful, {error_count} errors",
        )
        self.status_var.set(f"Complete: {success_count} OK, {error_count} errors")


if __name__ == "__main__":
    root = tk.Tk()
    CSVtoLinApp(root)
    root.mainloop()
