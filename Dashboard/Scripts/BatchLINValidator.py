import os
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk


# ── Validator ────────────────────────────────────────────────────────────────

class LINValidatorCombined:
    SUITS      = {"S": "Spades", "H": "Hearts", "D": "Diamonds", "C": "Clubs"}
    RANKS      = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
                  "T":10,"J":11,"Q":12,"K":13,"A":14}
    POSITIONS  = ["S", "W", "N", "E"]
    BID_LEVELS = ["1","2","3","4","5","6","7"]
    BID_SUITS  = ["C","D","H","S","N"]
    RANK_ORDER = "AKQJT98765432"

    def __init__(self, filepath):
        self.filepath = filepath
        self.errors   = []

    def validate(self):
        self.errors = []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
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

    # ── splitting ────────────────────────────────────────────────────────────

    def _split_deals(self, content):
        deals, current_deal = [], {}
        tags = re.findall(r"([a-z]{2})\|([^|]*?)(?=\||$)", content)
        for tag, value in tags:
            if tag == "qx" and tag in current_deal:
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
        for tag, value in re.findall(r"([a-z]{2})\|([^|]*?)(?=[a-z]{2}\||$)", content):
            value = value.strip()
            if tag in tags:
                if isinstance(tags[tag], list):
                    tags[tag].append(value)
                else:
                    tags[tag] = [tags[tag], value]
            else:
                tags[tag] = value
        return tags

    # ── deal-level validation ─────────────────────────────────────────────────

    def _validate_deal(self, deal, deal_num):
        prefix = f"Deal {deal_num}: "
        for tag in ("md", "sv", "mb"):
            if tag not in deal:
                self.errors.append(f"{prefix}Missing required tag '{tag}'")
                return
        if not self._validate_dealer(deal.get("ah", ""), prefix):
            return
        if not self._validate_hands(deal.get("md", ""), prefix):
            return
        if not self._validate_play_sequence(deal, prefix):
            return
        dealer_pos = self._get_dealer_from_md(deal.get("md", ""))
        if not dealer_pos:
            self.errors.append(f"{prefix}Could not determine dealer from md tag")
            return
        contract_info = self._validate_bidding(deal.get("mb", ""), dealer_pos, prefix)
        if not contract_info:
            return
        if "pc" in deal:
            for e in self._validate_card_play_enhanced(deal, contract_info, prefix):
                self.errors.append(e)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _validate_dealer(self, ah_value, prefix):
        if not ah_value:
            self.errors.append(f"{prefix}Dealer tag 'ah' is empty")
            return False
        return True

    def _get_dealer_from_md(self, md_value):
        if isinstance(md_value, list):
            md_value = md_value[0]
        m = re.match(r"^([1-4])", md_value)
        if m:
            return {1:"S",2:"W",3:"N",4:"E"}.get(int(m.group(1)))
        return None

    def _validate_hands(self, md_value, prefix):
        if isinstance(md_value, list):
            md_value = md_value[0]
        if not re.match(r"^([1-4])(.*)", md_value):
            self.errors.append(f"{prefix}Invalid md format")
            return False
        hands, _ = self._build_full_hands_from_md(md_value)
        if hands is None:
            self.errors.append(f"{prefix}Invalid md format (cannot build hands)")
            return False
        seen, total = set(), 0
        for pos in ("S","W","N","E"):
            for suit in "SHDC":
                for rank in hands[pos][suit]:
                    card = suit + rank
                    if card in seen:
                        self.errors.append(f"{prefix}Duplicate card found: {card}")
                        return False
                    seen.add(card)
                    total += 1
        if total != 52:
            self.errors.append(f"{prefix}Incorrect number of cards ({total} instead of 52)")
            return False
        return True

    def _validate_play_sequence(self, deal, prefix):
        pc_value = deal.get("pc", "")
        if not pc_value:
            return True
        segments = pc_value if isinstance(pc_value, list) else [pc_value]
        play_cards = []
        for seg in segments:
            if isinstance(seg, str):
                play_cards.extend(re.findall(r"([SHDC][AKQJT98765432])", seg))
        seen = set()
        for n, card in enumerate(play_cards, 1):
            if card in seen:
                self.errors.append(
                    f"{prefix}Duplicate card in play sequence: {card} "
                    f"(first duplicate at card #{n})")
                return False
            seen.add(card)
        return True

    def _validate_bidding(self, mb_value, dealer_pos, prefix):
        bids = mb_value if isinstance(mb_value, list) else [mb_value]
        all_bids = [b.strip() for b in bids
                    if b and isinstance(b, str) and b.strip() and not b.strip().endswith(":")]
        if not all_bids:
            self.errors.append(f"{prefix}No bids found")
            return None

        pass_count = 0
        last_bid_level, last_bid_suit = 0, -1
        contract = None
        double_status = "NONE"
        contract_partnership = None
        current_pos = self.POSITIONS.index(dealer_pos)
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

            if bid in ("X", "DBL", "D"):
                if contract is None:
                    self.errors.append(f"{prefix}Bid #{bid_num}: Cannot double — no contract bid yet")
                    return None
                if current_partnership == contract_partnership:
                    self.errors.append(f"{prefix}Bid #{bid_num}: Cannot double partner's contract")
                    return None
                if double_status in ("DOUBLED", "REDOUBLED"):
                    self.errors.append(f"{prefix}Bid #{bid_num}: Cannot double — already {double_status.lower()}")
                    return None
                double_status = "DOUBLED"
                current_pos = (current_pos + 1) % 4
                continue

            if bid in ("XX", "RDBL", "R", "RD", "RE"):
                if double_status != "DOUBLED":
                    self.errors.append(f"{prefix}Bid #{bid_num}: Cannot redouble — not doubled")
                    return None
                if current_partnership != contract_partnership:
                    self.errors.append(f"{prefix}Bid #{bid_num}: Cannot redouble opponent's contract")
                    return None
                double_status = "REDOUBLED"
                current_pos = (current_pos + 1) % 4
                continue

            if len(bid) >= 2:
                level, strain = bid[0], bid[1]
                if level not in self.BID_LEVELS:
                    self.errors.append(f"{prefix}Bid #{bid_num}: Invalid bid level: {bid}")
                    return None
                if strain not in self.BID_SUITS:
                    self.errors.append(f"{prefix}Bid #{bid_num}: Invalid bid suit: {bid}")
                    return None
                bid_level     = int(level)
                bid_suit_rank = self.BID_SUITS.index(strain)
                if bid_level < last_bid_level or (bid_level == last_bid_level and bid_suit_rank <= last_bid_suit):
                    self.errors.append(f"{prefix}Bid #{bid_num}: Insufficient bid: {bid}")
                    return None
                last_bid_level, last_bid_suit = bid_level, bid_suit_rank
                contract = bid
                contract_partnership = current_partnership
                double_status = "NONE"
                key = (strain, current_partnership)
                if key not in first_bid_map:
                    first_bid_map[key] = self.POSITIONS[current_pos]
                current_pos = (current_pos + 1) % 4

        if pass_count == 4 and contract is None:
            return {"contract": "Passed Out", "declarer": None, "trump": None}
        if pass_count != 3:
            self.errors.append(f"{prefix}Bidding must end with 3 passes (found {pass_count})")
            return None
        if not contract:
            self.errors.append(f"{prefix}No contract found")
            return None

        strain   = contract[1]
        declarer = first_bid_map.get((strain, contract_partnership))
        if not declarer:
            self.errors.append(f"{prefix}Cannot determine declarer")
            return None
        trump = {"C":"C","D":"D","H":"H","S":"S","N":None}.get(strain)
        return {"contract": contract, "declarer": declarer, "trump": trump}

    def _build_full_hands_from_md(self, md_value):
        if isinstance(md_value, list):
            md_value = md_value[0]
        m = re.match(r"^([1-4])(.*)", md_value)
        if not m:
            return None, None
        dealer_num = int(m.group(1))
        hands_str  = m.group(2)
        hands = {pos: {s: set() for s in "SHDC"} for pos in ("S","W","N","E")}
        for i, hand_str in enumerate(hands_str.split(",")[:3]):
            pos = ("S","W","N")[i]
            current_suit = None
            for ch in hand_str:
                if ch in "SHDC":
                    current_suit = ch
                elif current_suit and ch in self.RANK_ORDER:
                    hands[pos][current_suit].add(ch)
        for suit in "SHDC":
            used = set().union(*(hands[p][suit] for p in ("S","W","N")))
            hands["E"][suit] = set(self.RANK_ORDER) - used
        return hands, dealer_num - 1

    def _validate_card_play_enhanced(self, deal, contract_info, prefix):
        errors = []
        hands, _ = self._build_full_hands_from_md(deal.get("md",""))
        if hands is None:
            errors.append(f"{prefix}Enhanced play check could not parse md tag.")
            return errors

        positions     = self.POSITIONS
        trump_suit    = contract_info["trump"]
        declarer      = contract_info["declarer"]
        if declarer is None or contract_info["contract"] == "Passed Out":
            return errors

        declarer_idx        = positions.index(declarer)
        opening_leader_idx  = (declarer_idx + 1) % 4
        rank_values = {"A":14,"K":13,"Q":12,"J":11,"T":10,
                       "9":9,"8":8,"7":7,"6":6,"5":5,"4":4,"3":3,"2":2}

        pc_value = deal.get("pc","")
        segments = pc_value if isinstance(pc_value, list) else [pc_value]
        play_cards = []
        for seg in segments:
            if isinstance(seg, str):
                play_cards.extend(re.findall(r"([SHDC][AKQJT98765432])", seg))

        if not play_cards:
            return errors

        def find_winner(trick_cards, led_suit, trump):
            winner_idx, highest = 0, 0
            trump_played = trump and any(c[0] == trump for _, c in trick_cards)
            for idx, (_, card) in enumerate(trick_cards):
                suit, rank = card[0], card[1]
                v = rank_values[rank]
                if trump_played:
                    if suit == trump and v > highest:
                        highest, winner_idx = v, idx
                else:
                    if suit == led_suit and v > highest:
                        highest, winner_idx = v, idx
            return trick_cards[winner_idx][0]

        trick_history, trick_cards = [], []
        current_idx = expected_leader_idx = opening_leader_idx
        trick_num, led_suit = 0, None

        for card_num, card in enumerate(play_cards, 1):
            suit, rank = card[0], card[1]
            player    = positions[current_idx]
            card_disp = rank + suit

            if not trick_cards:
                trick_num += 1
                led_suit   = suit
                if current_idx != expected_leader_idx:
                    errors.append(
                        f"LEAD ERROR: Trick {trick_num}: expected "
                        f"{positions[expected_leader_idx]} to lead but {player} led.")
                    return errors

            if rank not in hands[player][suit]:
                msg = (f"ERROR: card #{card_num} (Trick {trick_num}, "
                       f"POS {len(trick_cards)+1}): {player} tried to play "
                       f"{card_disp} but does not hold it.")
                suit_cards = sorted(hands[player][suit], key=lambda x: self.RANK_ORDER.index(x))
                msg += f" {player}'s {suit} holding: " + (", ".join(suit_cards) or "NONE")
                if led_suit and suit != led_suit and hands[player][led_suit]:
                    msg += f" | REVOKE: must follow {led_suit} but played {card_disp}."
                errors.append(msg)
                return errors

            if led_suit and suit != led_suit and hands[player][led_suit]:
                led_suit_cards = sorted(hands[player][led_suit],
                                        key=lambda x: self.RANK_ORDER.index(x))
                expected_disp  = f"{led_suit_cards[-1]}{led_suit}"
                leader         = trick_cards[0][0] if trick_cards else positions[expected_leader_idx]
                leader_card    = (f"{trick_cards[0][1][1]}{trick_cards[0][1][0]}"
                                  if trick_cards else "??")
                # Build trick history string
                all_tricks = trick_history[:]
                if trick_cards:
                    all_tricks.append(trick_cards[:])
                trick_details = []
                for tnum, tcards in enumerate(all_tricks, 1):
                    t_led = tcards[0][1][0] if tcards else "?"
                    winner = find_winner(tcards, t_led, trump_suit) if tcards else "?"
                    t_str  = f"Trick {tnum}: " + ", ".join(f"{c[1]}{c[0]}({p.lower()})"
                                                            for p, c in tcards)
                    t_str += f" won by {winner}"
                    trick_details.append(t_str)
                msg = (f"REVOKE: card #{card_num} (Trick {trick_num}, "
                       f"POS {len(trick_cards)+1}): {player} had {expected_disp} "
                       f"but played {card_disp}. {leader} led ({leader_card}).")
                if trick_details:
                    msg += "\nTricks played so far:\n" + "\n".join(trick_details)
                errors.append(msg)
                return errors

            hands[player][suit].remove(rank)
            trick_cards.append((player, (suit, rank)))

            if len(trick_cards) == 4:
                winner = find_winner(trick_cards, led_suit, trump_suit)
                trick_history.append(trick_cards[:])
                expected_leader_idx = current_idx = positions.index(winner)
                trick_cards, led_suit = [], None
            else:
                current_idx = (current_idx + 1) % 4

        return errors


# ── GUI ───────────────────────────────────────────────────────────────────────

GROUP_NUMBERS = list(range(11, 39))   # 11 – 38 inclusive

GROUP_NAMES = {
    11: "The Squeeze Play Part 1",       12: "The Squeeze Play Part 2",
    13: "The Deceptive Play Part 1",     14: "The Deceptive Play Part 2",
    15: "Intermediate Play Part 1",      16: "Intermediate Play Part 2",
    17: "Play Technique Part 1",         18: "Play Technique Part 2",
    19: "The Finesse Part 1",            20: "The Finesse Part 2",
    21: "Entries Part 1",                22: "Entries Part 2",
    23: "Help from the Enemy Part 1",    24: "Help from the Enemy Part 2",
    25: "Trump Management Part 1",       26: "Trump Management Part 2",
    27: "Slam Bidding & Defensive Play Part 1",
    28: "Slam Bidding & Defensive Play Part 2",
    29: "Basic Play at Notrump Part 1",  30: "Basic Play at Notrump Part 2",
    31: "Basic play at Trump Part 1",    32: "Basic play at Trump Part 2",
    33: "Match-point Tournament Play Part 1",
    34: "Match-point Tournament Play Part 2",
    35: "Safety Plays Part 1",           36: "Safety Plays Part 2",
    37: "End Plays Part 1",              38: "End Plays Part 2",
}


def run_validation(sheets_dir, log_widget, summary_label):
    """Walk every Group<n>/Lin folder, validate all .lin files, stream results."""
    log_widget.config(state="normal")
    log_widget.delete("1.0", tk.END)

    total_files   = 0
    total_valid   = 0
    total_errors  = 0
    error_data    = {}   # {group_num: {filename: [errors]}}
    missing_folders = []

    for grp in GROUP_NUMBERS:
        lin_folder = os.path.join(sheets_dir, f"Group{grp}", "Lin")

        if not os.path.isdir(lin_folder):
            missing_folders.append(f"Group{grp}/Lin")
            continue

        lin_files = sorted(f for f in os.listdir(lin_folder)
                           if f.lower().endswith(".lin"))
        if not lin_files:
            log_widget.insert(tk.END,
                f"Group {grp} — {GROUP_NAMES[grp]}\n"
                f"  (no .lin files found)\n\n")
            log_widget.see(tk.END)
            log_widget.update()
            continue

        log_widget.insert(tk.END,
            f"{'='*60}\n"
            f"Group {grp} — {GROUP_NAMES[grp]}\n"
            f"{'='*60}\n")

        group_errors = {}
        for filename in lin_files:
            filepath  = os.path.join(lin_folder, filename)
            validator = LINValidatorCombined(filepath)
            total_files += 1
            if validator.validate():
                log_widget.insert(tk.END, f"  ✓  {filename}\n")
                total_valid += 1
            else:
                errs = validator.get_errors()
                log_widget.insert(tk.END, f"  ✗  {filename}  ({len(errs)} error(s))\n")
                for e in errs:
                    log_widget.insert(tk.END, f"       → {e}\n")
                group_errors[filename] = errs
                total_errors += 1

        if group_errors:
            error_data[grp] = group_errors

        log_widget.insert(tk.END, "\n")
        log_widget.see(tk.END)
        log_widget.update()

    # Missing folder warnings
    if missing_folders:
        log_widget.insert(tk.END,
            f"{'='*60}\n"
            f"WARNING — The following Lin folders were not found:\n")
        for mf in missing_folders:
            log_widget.insert(tk.END, f"  • {mf}\n")
        log_widget.insert(tk.END, "\n")

    # Final summary line
    summary_label.config(
        text=f"Done.  Files checked: {total_files}   "
             f"✓ Valid: {total_valid}   ✗ With errors: {total_errors}")

    log_widget.config(state="disabled")
    return error_data


class BatchLINValidatorApp:
    def __init__(self, root):
        self.root  = root
        self.root.title("Batch LIN Validator")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Sheets directory:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.dir_var, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Browse…", command=self._browse).pack(side=tk.LEFT)

        mid = ttk.Frame(self.root, padding=(10, 0))
        mid.pack(fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(
            mid, wrap=tk.WORD, font=("Courier", 9), state="disabled")
        self.log.pack(fill=tk.BOTH, expand=True)

        bot = ttk.Frame(self.root, padding=10)
        bot.pack(fill=tk.X)

        self.summary_label = ttk.Label(bot, text="", font=("Arial", 10, "bold"))
        self.summary_label.pack(side=tk.LEFT)

        ttk.Button(bot, text="Run Validation", command=self._run).pack(side=tk.RIGHT)

    def _browse(self):
        d = filedialog.askdirectory(title="Select the Sheets parent directory")
        if d:
            self.dir_var.set(d)

    def _run(self):
        sheets_dir = self.dir_var.get().strip()
        if not sheets_dir or not os.path.isdir(sheets_dir):
            messagebox.showerror("Error", "Please select a valid Sheets directory first.")
            return
        run_validation(sheets_dir, self.log, self.summary_label)


def main():
    root = tk.Tk()
    BatchLINValidatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
