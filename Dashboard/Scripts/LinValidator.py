import os
import re
import tkinter as tk
from tkinter import Tk, filedialog, scrolledtext, messagebox
from tkinter import ttk


class LINValidatorCombined:
    SUITS = {"S": "Spades", "H": "Hearts", "D": "Diamonds", "C": "Clubs"}
    RANKS = {
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

    POSITIONS = ["S", "W", "N", "E"]
    BID_LEVELS = ["1", "2", "3", "4", "5", "6", "7"]
    BID_SUITS = ["C", "D", "H", "S", "N"]
    RANK_ORDER = "AKQJT98765432"

    def __init__(self, filepath):
        self.filepath = filepath
        self.errors = []

    def validate(self):
        """Main validation method"""
        self.errors = []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            return False

        deals = self._split_deals(content)
        if not deals:
            self.errors.append("No deals found in file")
            return False

        for deal_num, deal in enumerate(deals, 1):
            self._validate_deal(deal, deal_num)

        return len(self.errors) == 0

    def get_errors(self):
        return self.errors

    def _split_deals(self, content):
        deals = []
        current_deal = {}
        tags = re.findall(r"([a-z]{2})\|([^|]*?)(?=\||$)", content)

        for tag, value in tags:
            if tag in current_deal and tag == "qx":
                if current_deal:
                    deals.append(current_deal)
                current_deal = {tag: value}
            else:
                if tag in current_deal:
                    if isinstance(current_deal[tag], list):
                        current_deal[tag].append(value)
                    else:
                        current_deal[tag] = [current_deal[tag], value]
                else:
                    current_deal[tag] = value

        if current_deal:
            deals.append(current_deal)

        return deals if deals else [self._parse_tags(content)]

    def _parse_tags(self, content):
        tags = {}
        matches = re.findall(r"([a-z]{2})\|([^|]*?)(?=[a-z]{2}\||$)", content)
        for tag, value in matches:
            value = value.strip()
            if tag in tags:
                if isinstance(tags[tag], list):
                    tags[tag].append(value)
                else:
                    tags[tag] = [tags[tag], value]
            else:
                tags[tag] = value
        return tags

    def _validate_deal(self, deal, deal_num):
        prefix = f"Deal {deal_num}: "

        required = ["md", "sv", "mb"]
        for tag in required:
            if tag not in deal:
                self.errors.append(f"{prefix}Missing required tag '{tag}'")
                return

        if not self._validate_dealer(deal.get("ah", ""), prefix):
            return

        if not self._validate_hands(deal.get("md", ""), prefix):
            return

        # Validate play sequence for duplicates
        if not self._validate_play_sequence(deal, prefix):
            return

        # Get dealer from md tag
        dealer_pos = self._get_dealer_from_md(deal.get("md", ""))
        if not dealer_pos:
            self.errors.append(f"{prefix}Could not determine dealer from md tag")
            return

        contract_info = self._validate_bidding(deal.get("mb", ""), dealer_pos, prefix)
        if not contract_info:
            return

        if "pc" in deal:
            # Pass prefix, but we won't prepend it to the final error message
            enhanced_errors = self._validate_card_play_enhanced(
                deal, contract_info, prefix
            )
            for e in enhanced_errors:
                # CHANGED: Append error directly without "Deal X:" prefix
                self.errors.append(e)

    def _validate_card_play_enhanced(self, deal, contract_info, prefix):
        errors = []

        md_value = deal.get("md", "")
        hands, dealer_idx = self._build_full_hands_from_md(md_value)
        if hands is None:
            errors.append(f"{prefix}Enhanced play check could not parse md tag.")
            return errors

        positions = self.POSITIONS
        final_contract = contract_info["contract"]
        trump_suit = contract_info["trump"]
        declarer = contract_info["declarer"]

        if declarer is None or final_contract == "Passed Out":
            return errors

        declarer_idx = positions.index(declarer)
        opening_leader_idx = (declarer_idx + 1) % 4

        pc_value = deal.get("pc", "")
        all_pc_segments = pc_value if isinstance(pc_value, list) else [pc_value]
        play_cards = []
        for seg in all_pc_segments:
            if not isinstance(seg, str):
                continue
            play_cards.extend(re.findall(r"([SHDC][AKQJT98765432])", seg))

        if not play_cards:
            return errors

        rank_values = {
            "A": 14,
            "K": 13,
            "Q": 12,
            "J": 11,
            "T": 10,
            "9": 9,
            "8": 8,
            "7": 7,
            "6": 6,
            "5": 5,
            "4": 4,
            "3": 3,
            "2": 2,
        }

        # Track completed tricks for history: list of lists of (player, (suit, rank))
        trick_history = []

        def find_trick_winner(trick_cards, led_suit, trump):
            winner_idx = 0
            highest_value = 0
            trump_played = False

            if trump:
                for _, card in trick_cards:
                    if card[0] == trump:
                        trump_played = True
                        break

            for idx, (player, card) in enumerate(trick_cards):
                suit = card[0]
                rank = card[1]
                value = rank_values[rank]
                if trump_played:
                    if suit == trump and value > highest_value:
                        highest_value = value
                        winner_idx = idx
                else:
                    if suit == led_suit and value > highest_value:
                        highest_value = value
                        winner_idx = idx
            return trick_cards[winner_idx][0]

        current_idx = opening_leader_idx
        expected_leader_idx = opening_leader_idx
        trick_num = 0
        trick_cards = []
        led_suit = None

        for card_num, card in enumerate(play_cards, 1):
            suit = card[0]
            rank = card[1]
            player = positions[current_idx]
            card_disp = card[1] + card[0]  # RankSuit

            if len(trick_cards) == 0:
                trick_num += 1
                led_suit = suit
                if current_idx != expected_leader_idx:
                    msg = (
                        f"LEAD ERROR: Trick {trick_num}: "
                        f"expected {positions[expected_leader_idx]} to lead "
                        f"but {player} led instead."
                    )
                    errors.append(msg)
                    return errors

            if rank not in hands[player][suit]:
                msg = (
                    f"ERROR: card #{card_num} (Trick {trick_num}, POS {len(trick_cards)+1}): "
                    f"{player} tried to play {card_disp} but does not hold it."
                )
                msg += (
                    f" [DEBUG: current_idx={current_idx}, opening_leader_idx={opening_leader_idx}, "
                    f"declarer={declarer}, declarer_idx={declarer_idx}]"
                )
                suit_cards = sorted(
                    hands[player][suit], key=lambda x: self.RANK_ORDER.index(x)
                )
                msg += f" {player}'s {suit} holding: "
                msg += ", ".join(suit_cards) if suit_cards else "NONE"
                if led_suit and suit != led_suit and hands[player][led_suit]:
                    msg += (
                        f" | REVOKE: must follow suit {led_suit} "
                        f"but played {card_disp} instead."
                    )
                errors.append(msg)
                return errors

            # REVOKE check with history (including current trick)
            if led_suit and suit != led_suit and hands[player][led_suit]:
                # Build trick history up to and including the current (partial) trick
                all_tricks_so_far = trick_history[:]
                if trick_cards:
                    all_tricks_so_far.append(trick_cards[:])

                trick_details = []
                for tnum, tcards in enumerate(all_tricks_so_far, 1):
                    if tcards:
                        t_led_suit = tcards[0][1][0]
                        winner = find_trick_winner(tcards, t_led_suit, trump_suit)
                    else:
                        winner = "?"
                    trick_str = f"Trick {tnum}: "
                    for p, c in tcards:
                        trick_str += f"{c[1]}{c[0]}({p.lower()}), "
                    trick_str = trick_str.rstrip(", ") + f" won by {winner}"
                    trick_details.append(trick_str)

                led_suit_cards_sorted = sorted(
                    hands[player][led_suit], key=lambda x: self.RANK_ORDER.index(x)
                )
                expected_card_rank = led_suit_cards_sorted[-1]
                expected_card_disp = f"{expected_card_rank}{led_suit}"

                if trick_cards:
                    leader = trick_cards[0][0]
                    leader_card_raw = trick_cards[0][1]
                    leader_card_disp = f"{leader_card_raw[1]}{leader_card_raw[0]}"
                else:
                    leader = positions[expected_leader_idx]
                    leader_card_disp = "??"

                msg = (
                    f"REVOKE: card #{card_num} (Trick {trick_num}, POS {len(trick_cards)+1}): "
                    f"{player} had {expected_card_disp} but played {card_disp}. "
                    f"{leader} led ({leader_card_disp})."
                )
                if trick_details:
                    msg += "\nTricks played so far:\n" + "\n".join(trick_details)
                errors.append(msg)
                return errors

            # Normal play
            hands[player][suit].remove(rank)
            trick_cards.append((player, (suit, rank)))

            if len(trick_cards) == 4:
                winner = find_trick_winner(trick_cards, led_suit, trump_suit)
                trick_history.append(trick_cards[:])  # record completed trick
                expected_leader_idx = positions.index(winner)
                current_idx = expected_leader_idx
                trick_cards = []
                led_suit = None
            else:
                current_idx = (current_idx + 1) % 4

        return errors

    def _validate_dealer(self, ah_value, prefix):
        if not ah_value:
            self.errors.append(f"{prefix}Dealer tag 'ah' is empty")
            return False
        return True

    def _get_dealer_from_md(self, md_value):
        """
        FIXED: Extract dealer position directly from md tag.
        md format: dealer_digit + hands
        dealer: 1=S, 2=W, 3=N, 4=E
        """
        if isinstance(md_value, list):
            md_value = md_value[0]

        match = re.match(r"^([1-4])", md_value)
        if match:
            dealer_num = int(match.group(1))
            dealer_map = {1: "S", 2: "W", 3: "N", 4: "E"}
            return dealer_map.get(dealer_num, "S")
        return None

    def _validate_hands(self, md_value, prefix):
        """IMPROVED: Validate hand distribution and check for duplicates across all 4 hands"""
        # Normalize md_value
        if isinstance(md_value, list):
            md_value = md_value[0]

        # Basic md format check
        match = re.match(r"^([1-4])(.*)", md_value)
        if not match:
            self.errors.append(f"{prefix}Invalid md format")
            return False

        # Reuse the same logic as _build_full_hands_from_md to get S, W, N, E
        hands, _dealer_idx = self._build_full_hands_from_md(md_value)
        if hands is None:
            self.errors.append(f"{prefix}Invalid md format (cannot build hands)")
            return False

        seen = set()
        total = 0

        # Walk all four positions and all suits
        for pos in ["S", "W", "N", "E"]:
            for suit in "SHDC":
                for rank in hands[pos][suit]:
                    card = suit + rank
                    if card in seen:
                        self.errors.append(f"{prefix}Duplicate card found: {card}")
                        return False
                    seen.add(card)
                    total += 1

        # Require exactly 52 distinct cards across all 4 hands
        if total != 52:
            self.errors.append(
                f"{prefix}Incorrect number of cards in deal ({total} instead of 52)"
            )
            return False

        return True

    def _validate_play_sequence(self, deal, prefix):
        """NEW: Check for duplicate cards in play sequence (pc tags)"""
        pc_value = deal.get("pc", "")
        if not pc_value:
            return True  # No play sequence to validate

        # Extract all cards from pc| tags
        all_pc_segments = pc_value if isinstance(pc_value, list) else [pc_value]
        play_cards = []
        for seg in all_pc_segments:
            if not isinstance(seg, str):
                continue
            play_cards.extend(re.findall(r"([SHDC][AKQJT98765432])", seg))

        if not play_cards:
            return True

        # Check for duplicates in play sequence
        seen_in_play = set()
        for card_num, card in enumerate(play_cards, 1):
            if card in seen_in_play:
                self.errors.append(
                    f"{prefix}Duplicate card in play sequence: {card} "
                    f"appears multiple times (first duplicate at card #{card_num})"
                )
                return False
            seen_in_play.add(card)

        return True

    def _parse_hand(self, hand_str):
        cards = []
        current_suit = None
        for char in hand_str:
            if char in self.SUITS:
                current_suit = char
            elif char in self.RANKS and current_suit:
                cards.append(current_suit + char)
        return cards

    def _validate_bidding(self, mb_value, dealer_pos, prefix):
        if isinstance(mb_value, list):
            bids = mb_value
        else:
            bids = [mb_value]

        all_bids = []
        for b in bids:
            if b and isinstance(b, str):
                b_clean = b.strip()
                if b_clean and not b_clean.endswith(":"):
                    all_bids.append(b_clean)

        if not all_bids:
            self.errors.append(f"{prefix}No bids found")
            return None

        pass_count = 0
        last_bid_level = 0
        last_bid_suit = -1
        contract = None
        double_status = "NONE"
        contract_partnership = None

        current_pos = self.POSITIONS.index(dealer_pos)

        # FIXED: Track first bidder for EACH partnership separately
        # Key: (strain, partnership_index), Value: player_position
        first_bid_map = {}

        for bid_num, bid in enumerate(all_bids, 1):
            bid = bid.strip().upper()
            if not bid:
                continue

            current_partnership = current_pos % 2

            if bid in ("P", "PASS"):
                pass_count += 1
                current_pos = (current_pos + 1) % 4
                continue

            pass_count = 0

            # FIXED: Added "D" to recognized doubles
            if bid in ("X", "DBL", "D"):
                if contract is None:
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Cannot double - no contract has been bid yet"
                    )
                    return None
                if current_partnership == contract_partnership:
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Cannot double partner's contract"
                    )
                    return None
                if double_status == "DOUBLED":
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Cannot double - contract is already doubled"
                    )
                    return None
                if double_status == "REDOUBLED":
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Cannot double - contract is already redoubled"
                    )
                    return None
                double_status = "DOUBLED"
                current_pos = (current_pos + 1) % 4
                continue

            # FIXED: Added "R", "RD", "RE" to recognized redoubles
            if bid in ("XX", "RDBL", "R", "RD", "RE"):
                if double_status != "DOUBLED":
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Cannot redouble - contract is not doubled"
                    )
                    return None
                if current_partnership != contract_partnership:
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Cannot redouble opponent's contract"
                    )
                    return None
                double_status = "REDOUBLED"
                current_pos = (current_pos + 1) % 4
                continue

            if len(bid) >= 2:
                level = bid[0]
                strain = bid[1]

                if level not in self.BID_LEVELS:
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Invalid bid level: {bid}"
                    )
                    return None
                if strain not in self.BID_SUITS:
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Invalid bid suit: {bid}"
                    )
                    return None

                bid_level = int(level)
                bid_suit_rank = self.BID_SUITS.index(strain)

                if bid_level < last_bid_level:
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Insufficient bid: {bid} after level {last_bid_level}"
                    )
                    return None
                elif bid_level == last_bid_level and bid_suit_rank <= last_bid_suit:
                    self.errors.append(
                        f"{prefix}Bid #{bid_num}: Insufficient bid: {bid}"
                    )
                    return None

                last_bid_level = bid_level
                last_bid_suit = bid_suit_rank
                contract = bid
                contract_partnership = current_partnership
                double_status = "NONE"

                # FIXED: Logic to record who introduced the strain for THIS partnership
                key = (strain, current_partnership)
                if key not in first_bid_map:
                    first_bid_map[key] = self.POSITIONS[current_pos]

                current_pos = (current_pos + 1) % 4

        if pass_count == 4 and contract is None:
            return {"contract": "Passed Out", "declarer": None, "trump": None}

        if pass_count != 3:
            self.errors.append(
                f"{prefix}Bidding must end with exactly 3 passes (found {pass_count})"
            )
            return None

        declarer = None
        if contract:
            strain = contract[1]
            # FIXED: Look up declarer based on the winning partnership
            declarer = first_bid_map.get((strain, contract_partnership))

            if not declarer:
                self.errors.append(f"{prefix}Cannot determine declarer")
                return None
        else:
            self.errors.append(f"{prefix}No contract found (incomplete auction)")
            return None

        strain_map = {"C": "C", "D": "D", "H": "H", "S": "S", "N": None}
        trump_suit = strain_map.get(strain)

        return {"contract": contract, "declarer": declarer, "trump": trump_suit}

    def _build_full_hands_from_md(self, md_value):
        """
        FIXED VERSION: Hands in LIN are ALWAYS South, West, North regardless of dealer.
        """
        if isinstance(md_value, list):
            md_value = md_value[0]

        m = re.match(r"^([1-4])(.*)", md_value)
        if not m:
            return None, None

        dealer_num = int(m.group(1))
        hands_str = m.group(2)

        # Initialize hands for absolute positions
        hands = {
            pos: {"S": set(), "H": set(), "D": set(), "C": set()}
            for pos in ["S", "W", "N", "E"]
        }

        hand_parts = hands_str.split(",")

        # The hands in a LIN md tag are ALWAYS South, West, North in that order.
        listed_positions = ["S", "W", "N"]
        missing_pos = "E"

        # Parse the three provided hands
        for i, hand_str in enumerate(hand_parts):
            if i >= 3:
                break

            pos = listed_positions[i]
            current_suit = None

            for ch in hand_str:
                if ch in "SHDC":
                    current_suit = ch
                elif current_suit and ch in self.RANK_ORDER:
                    hands[pos][current_suit].add(ch)

        # Calculate the missing hand (East) from remaining cards
        all_ranks = set(self.RANK_ORDER)
        for suit in "SHDC":
            used = set()
            for pos in listed_positions:
                used.update(hands[pos][suit])
            hands[missing_pos][suit] = all_ranks - used

        return hands, dealer_num - 1


class ErrorSummaryWindow:
    """GUI window to display error summary with clipboard functionality"""

    def __init__(self, error_data):
        self.window = tk.Toplevel()
        self.window.title("LIN Validation - Error Summary")
        self.window.geometry("900x600")

        self.summary_text = self._build_summary(error_data)

        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        title_label = ttk.Label(
            main_frame, text="Files with Errors", font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        self.text_widget = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, font=("Courier", 10)
        )
        self.text_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.text_widget.insert("1.0", self.summary_text)
        self.text_widget.config(state="disabled")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0))

        copy_btn = ttk.Button(
            button_frame, text="Copy to Clipboard", command=self.copy_to_clipboard
        )
        copy_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(button_frame, text="Close", command=self.window.destroy)
        close_btn.pack(side=tk.LEFT, padx=5)

    def _build_summary(self, error_data):
        if not error_data:
            return "No errors found!"

        lines = []
        for filename, errors in sorted(error_data.items()):
            lines.append(f"{'='*70}")
            lines.append(f"{filename}")
            lines.append(f"{'='*70}")
            lines.append("")

            parsed_errors = []
            for error in errors:
                if error.startswith("Deal "):
                    match = re.match(r"Deal (\d+): (.+)", error)
                    if match:
                        deal_num = int(match.group(1))
                        error_msg = match.group(2)

                        error_msg = error_msg.replace("position", "POS")
                        error_msg = re.sub(r"\bat\b", "", error_msg)
                        error_msg = error_msg.replace("player ", "")
                        error_msg = re.sub(r"\s+", " ", error_msg).strip()

                        parsed_errors.append((deal_num, error_msg))
                    else:
                        parsed_errors.append((999999, error))
                else:
                    parsed_errors.append((999999, error))

            parsed_errors.sort(key=lambda x: x[0])

            has_revoke = any("REVOKE" in msg for _, msg in parsed_errors)

            for deal_num, error_msg in parsed_errors:
                if deal_num == 999999:
                    lines.append(f"  {error_msg}")
                else:
                    deal_prefix = f" {deal_num}" if deal_num < 10 else f"{deal_num}"
                    lines.append(f"  {deal_prefix}: {error_msg}")

            if has_revoke:
                lines.append("")
                lines.append("  NOTE: Revoke(s) detected — possible causes:")
                lines.append("    - Wrong contract recorded (e.g. 4S instead of 4H)")
                lines.append("    - Wrong play sequence order ")
                lines.append("    - Misprint in play sequence on deal sheet")
                lines.append(
                    "    - revoking card wrong suit (C S) and card belongs in another hand"
                )

            lines.append("")

        return "\n".join(lines)

    def copy_to_clipboard(self):
        self.window.clipboard_clear()
        self.window.clipboard_append(self.summary_text)
        self.window.update()
        messagebox.showinfo("Copied", "Error summary copied to clipboard!")


def main():
    root = Tk()
    root.withdraw()

    folder_path = filedialog.askdirectory(title="Select folder containing LIN files")
    if not folder_path:
        print("No folder selected. Exiting.")
        return

    lin_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".lin")]
    if not lin_files:
        print(f"No .lin files found in {folder_path}")
        return

    print(f"\nValidating {len(lin_files)} LIN file(s)...\n")

    valid_count = 0
    error_count = 0
    error_data = {}

    for filename in sorted(lin_files):
        filepath = os.path.join(folder_path, filename)
        validator = LINValidatorCombined(filepath)
        if validator.validate():
            print(f"{filename}: VALID")
            valid_count += 1
        else:
            print(f"{filename}: ERRORS FOUND")
            errors = validator.get_errors()
            error_data[filename] = errors
            for error in errors:
                print(f" - {error}")
            error_count += 1
        print()

    print("\n" + "=" * 60)
    print(f"Summary: {valid_count} valid, {error_count} with errors")
    print("=" * 60)

    if error_data:
        print("\nOpening error summary window...")
        ErrorSummaryWindow(error_data)
        root.mainloop()


if __name__ == "__main__":
    main()
