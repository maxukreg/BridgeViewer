import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
import csv
import re
import os
from pathlib import Path
import sys
import argparse

print("Script started - April 2025 version")  # Debug print to confirm script version


class BridgeHandEditor:
    def validate_and_correct_cards(self, hands):
        """
        Validates and cleans whitespace and bad formatting in card codes for each hand.
        Automatically corrects cards with extra spaces (e.g. '3 D' → '3D').
        Returns (list of correction messages, list of irreparable problems).
        Mutates input hand data in place.
        """
        valid_ranks = {"2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"}
        valid_suits = {"S", "H", "D", "C"}
        corrections = []
        problems = []
        for hand_name, hand_cards in hands.items():
            for idx, card_obj in enumerate(hand_cards):
                original = card_obj["card"]
                cleaned = "".join(original.split())  # Remove ALL whitespace
                # If changed, show correction
                if cleaned != original:
                    corrections.append(
                        f"{hand_name.capitalize()} card {idx+1}: '{original}' → '{cleaned}'"
                    )
                    card_obj["card"] = cleaned
                # Now validate
                if (
                    len(cleaned) != 2
                    or cleaned[0] not in valid_ranks
                    or cleaned[1] not in valid_suits
                ):
                    problems.append(
                        f"{hand_name.capitalize()} card {idx+1}: '{cleaned}' – invalid"
                    )
        return corrections, problems

    def __init__(self, root):
        self.root = root
        self.root.title("Bridge Hand Editor")

        # Parse command line arguments
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--group", type=int, help="Group number to pre-populate")
        args, unknown = parser.parse_known_args()
        self.default_group = args.group if args.group else None

        # a) Small size: Set compact dimensions for front screen
        # b) Appear on launching window: Use mouse position to detect current screen
        try:
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
            # Small window size (500x400) positioned near mouse cursor
            self.root.geometry(f"500x400+{mouse_x-250}+{mouse_y-200}")
        except:
            # Fallback: small size with default positioning
            self.root.geometry("500x400+100+100")

        self.root.configure(bg="white")

        # **CHANGE 2: Launch full screen**
        # self.root.state('zoomed')  # Windows full screen
        # Alternative for cross-platform: self.root.attributes('-zoomed', True)

        self.root.configure(bg="white")

        # **CHANGE 1: Disable timeout by preventing idle events from closing**
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.keep_alive()  # Start keep-alive mechanism

        # Base directory for data files
        home_dir = Path.home()
        one_drive_folder = next(home_dir.glob("OneDrive*"))
        self.base_directory = (
            one_drive_folder
            / "Software"
            / "Projects"
            / "Handviewer"
            / "Autobridge"
            / "Sheets"
        )

        # Data variables
        self.deals = []
        self.current_deal_index = 0
        self.duplicate_highlights = {}
        self.highlight_colors = [
            "#ffcccc",  # light red
            "#cce5ff",  # light blue
            "#ccffcc",  # light green
            "#ffffcc",  # light yellow
            "#e5ccff",  # light purple
            "#ffccff",  # light pink
            "#ccffff",  # light cyan
        ]

        # Start with group selection
        self.show_group_selection()

    def keep_alive(self):
        """Prevent timeout by keeping the application active"""
        # Schedule this method to run every 30 seconds to prevent timeout
        self.root.after(30000, self.keep_alive)

    def on_closing(self):
        """Handle window closing event"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

    def update_info_from_entries(self):
        """Read dealer, vulnerability, and contract from UI entries and update the current deal data"""
        if not self.deals or self.current_deal_index >= len(self.deals):
            return

        current_deal = self.deals[self.current_deal_index]
        info = current_deal["info"]

        # Update dealer
        dealer = self.dealer_entry.get().upper().strip()
        if dealer in ["N", "S", "E", "W"]:
            info["dealer"] = dealer

        # Update vulnerability
        vul = self.vul_entry.get().upper().strip()
        if vul in ["N", "E", "B", "0"]:
            info["vul"] = vul

        # Update contract
        contract = self.contract_entry.get().upper().strip()
        if self.is_valid_contract(contract):
            info["contract"] = contract

        print(
            f"Updated info from UI entries: Dealer={info['dealer']}, Vul={info['vul']}, Contract={info['contract']}"
        )

    def is_valid_contract(self, contract):
        if not contract:
            return False
        if len(contract) < 2 or len(contract) > 4:
            return False
        # First character: digit 1-7
        level = contract[0]
        if not (level.isdigit() and "1" <= level <= "7"):
            return False
        # Second character: C, D, H, S, or N
        strain = contract[1]
        if strain not in "CDHSN":
            return False
        # Third character: (optional) X for double
        if len(contract) == 3:
            if contract[2] != "X":
                return False
        # Fourth character: (optional) X for redouble
        if len(contract) == 4:
            if contract[2] != "X" or contract[3] != "X":
                return False
        return True

    def export_current_deal(self):
        # Update info from UI entries FIRST, before any validation
        self.update_info_from_entries()

        # THEN validate with the updated dealer value
        if not self.validate_dealer_bidding(ask_continue_on_error=True):
            return  # Abort export if user does not want to proceed

        contract = self.contract_entry.get().strip().upper()
        if not contract or not self.is_valid_contract(contract):
            self.contract_entry.config(bg="#ffcccc")
            messagebox.showerror(
                "Export Error",
                "Invalid contract: Please enter a valid contract before exporting.",
            )
            print("Export blocked due to invalid contract")
            return

        self.update_bidding_from_entries()
        # No need to call update_info_from_entries() again since we did it at the top

        import csv

        if not self.deals or self.current_deal_index >= len(self.deals):
            return

        current_deal = self.deals[self.current_deal_index]
        info = current_deal["info"]
        hands = current_deal["hands"]
        bidding = current_deal["bidding"]

        group = str(info["group"])
        deal = str(info["deal"])

        # Direct export path without prompts
        export_dir = f"{self.base_directory}\\Group{group}\\CSV"
        export_path = f"{export_dir}\\HandsFromAI.csv"

        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        # Prepare the 13 rows for the current deal
        current_metadata = [
            "Group",
            group,
            "Deal",
            deal,
            "Dealer",
            info["dealer"],
            "Vul",
            info["vul"],
            "Contract",
            info["contract"],
        ]

        def format_cards(hand_data):
            # Return individual card values as separate fields (plain unquoted row)
            return [card["card"] for card in hand_data]

        def format_sequences(hand_data):
            # Return individual sequence values as separate fields
            return [card["sequence"] for card in hand_data]

        def format_bidding(bids):
            # Pad to 8 fields and return as a single quoted CSV cell
            padded = (list(bids) + [""] * 8)[:8]
            return [",".join(padded)]

        current_deal_rows = [
            current_metadata,
            format_cards(hands["north"]),
            format_sequences(hands["north"]),
            format_cards(hands["south"]),
            format_sequences(hands["south"]),
            format_cards(hands["east"]),
            format_sequences(hands["east"]),
            format_cards(hands["west"]),
            format_sequences(hands["west"]),
            format_bidding(bidding["north"]),
            format_bidding(bidding["east"]),
            format_bidding(bidding["south"]),
            format_bidding(bidding["west"]),
        ]

        # Read all blocks from the existing data
        block_size = 13
        existing_data = []
        if os.path.exists(export_path):
            with open(export_path, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row:
                        existing_data.append(row)

        # Find and replace the block for the current deal.
        updated_data = []
        replaced = False
        i = 0
        # Find and replace the block for the current deal.
        updated_data = []
        replaced = False
        i = 0
        while i + block_size <= len(
            existing_data
        ):  # FIXED: changed from "i + block_size - 1 <"
            meta_row = existing_data[i]
            header_str = ",".join(meta_row).replace('"', "").replace(" ", "")
            parts = header_str.split(",")
            if (
                len(parts) >= 4
                and parts[0] == "Group"
                and parts[2] == "Deal"
                and parts[1] == group
                and parts[3] == deal
            ):
                # Replace this block with new one
                updated_data.extend(current_deal_rows)
                replaced = True
                i += block_size
            else:
                updated_data.extend(existing_data[i : i + block_size])
                i += block_size

        # ADDED: Append any remaining rows that weren't part of a complete block
        if i < len(existing_data):
            updated_data.extend(existing_data[i:])

        # Append as new block if not found and replaced
        if not replaced:
            updated_data.extend(current_deal_rows)

        # Write the updated CSV
        try:
            # Write in binary mode to preserve CRLF without double-CR corruption.
            # Bidding rows (single-element lists whose value contains commas) are
            # written quoted; all other rows are written as plain comma-separated.
            lines_out = []
            for row in updated_data:
                if len(row) == 1 and "," in str(row[0]):
                    # Bidding row: write as single quoted cell
                    lines_out.append('"' + str(row[0]) + '"')
                else:
                    lines_out.append(",".join(str(v) for v in row))
            with open(export_path, "wb") as csvfile:
                csvfile.write(b"\r\n".join(l.encode("utf-8") for l in lines_out))

            print(
                f"Deal {deal} exported directly to {export_path}. (Block {'replaced' if replaced else 'added'})"
            )

        except Exception as e:
            print(f"Export failed: {e}")
            messagebox.showerror("Error", f"Failed to export deal: {e}")
            return

        # Move to next deal as before
        next_deal_index = self.current_deal_index + 1
        if next_deal_index < len(self.deals):
            self.current_deal_index = next_deal_index
            next_deal = self.deals[self.current_deal_index]
            next_info = next_deal["info"]
            self.deal_var.set(next_info["deal"])
            if hasattr(self, "toolbar_deal_var"):
                self.toolbar_deal_var.set(next_info["deal"])
            self.update_view()
            self.find_duplicates()
            print(
                f"Moved to next deal: Group {next_info['group']}, Deal {next_info['deal']}"
            )
        else:
            next_deal_num = int(deal) + 1
            messagebox.showinfo(
                "End of Deals", f"Group {group} Deal {next_deal_num} does not exist."
            )
            print(f"No next deal exists after Group {group}, Deal {deal}")

    def previous_deal(self):
        """Navigate to previous deal"""
        if self.current_deal_index > 0:
            self.current_deal_index -= 1
            self.update_view()
            self.find_duplicates()

    def next_deal(self):
        """Navigate to next deal"""
        if self.current_deal_index < len(self.deals) - 1:
            self.current_deal_index += 1
            self.update_view()
            self.find_duplicates()

    def parse_command_line_args(self):
        """Parse command line arguments to get group number if provided"""
        try:
            parser = argparse.ArgumentParser(description="Bridge Hand Editor")
            parser.add_argument("--group", type=int, help="Group number to load")
            args, unknown = parser.parse_known_args()
            return args.group if args.group else None
        except:
            return None

    def show_group_selection(self):
        """Show dialog to input a group number with real-time validation"""

        # Parse command line arguments for group number
        selected_group_from_args = self.parse_command_line_args()

        # Clear all widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Build the UI first
        select_frame = tk.Frame(self.root, bg="white", padx=20, pady=20)
        select_frame.pack(expand=True)

        tk.Label(
            select_frame,
            text="Bridge Hand Editor",
            font=("Arial", 24, "bold"),
            bg="white",
        ).pack(pady=10)

        group_frame = tk.Frame(select_frame, bg="white")
        group_frame.pack(pady=10)

        tk.Label(group_frame, text="Group:", font=("Arial", 14), bg="white").pack(
            side=tk.LEFT, padx=5
        )

        self.group_entry = tk.Entry(group_frame, font=("Arial", 12), width=15)
        self.group_entry.pack(side=tk.LEFT, padx=5)
        self.group_entry.bind("<KeyRelease>", self.validate_group_on_change)

        available_groups = self.get_available_groups()
        if available_groups:
            available_text = "Available groups: " + ", ".join(available_groups)
        else:
            available_text = "No groups found"

        tk.Label(
            select_frame, text=available_text, font=("Arial", 10), bg="white"
        ).pack(pady=5)

        self.deal_frame = tk.Frame(select_frame, bg="white")
        self.deal_frame.pack(pady=10)

        tk.Label(self.deal_frame, text="Deal:", font=("Arial", 14), bg="white").pack(
            side=tk.LEFT, padx=5
        )

        self.deal_var = tk.StringVar()
        self.deal_dropdown = ttk.Combobox(
            self.deal_frame,
            textvariable=self.deal_var,
            font=("Arial", 12),
            width=15,
            state="disabled",
        )
        self.deal_dropdown.pack(side=tk.LEFT, padx=5)

        self.deal_count_label = tk.Label(
            select_frame, text="", font=("Arial", 10), bg="white"
        )
        self.deal_count_label.pack(pady=5)

        self.edit_button = tk.Button(
            select_frame,
            text="Edit Deal",
            font=("Arial", 12),
            command=self.edit_selected_hand,
            state="disabled",
        )
        self.edit_button.pack(pady=10)

        tk.Label(
            select_frame,
            text=f"Base directory: {self.base_directory}",
            font=("Arial", 8),
            bg="white",
        ).pack(pady=5, side=tk.BOTTOM)

        # ---- CENTER THE WINDOW AFTER UI IS BUILT ----
        def center_window():
            desired_w, desired_h = 600, 400
            self.root.update_idletasks()  # Ensure window is ready
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = (screen_w - desired_w) // 2
            y = (screen_h - desired_h) // 2
            self.root.geometry(f"{desired_w}x{desired_h}+{x}+{y}")

        # Schedule centering after window is mapped
        self.root.after_idle(center_window)

        # ---- Populate group number based on command line args or first available ----
        target_group = None

        # Priority 1: Use command line argument if provided
        if selected_group_from_args:
            target_group_name = f"Group{selected_group_from_args}"
            if target_group_name in available_groups:
                target_group = target_group_name
                print(f"Using group from command line: {target_group}")
            else:
                print(
                    f"Command line group {selected_group_from_args} not found in available groups"
                )

        # Priority 2: Use first available group if no command line arg or invalid arg
        if not target_group and available_groups:
            target_group = available_groups[0]
            print(f"Using first available group: {target_group}")

        if target_group:
            # Extract number from group name (e.g., 'Group27' -> '27')
            group_num = target_group.replace("Group", "")
            self.group_entry.delete(0, tk.END)
            self.group_entry.insert(0, group_num)
            # FIXED: Pass single group name, not entire list
            self.load_deals_for_group(target_group)  # ← This is correct
        else:
            # If no groups, keep UI elements disabled/informative
            self.group_entry.delete(0, tk.END)
            self.deal_dropdown.config(state="disabled", values=[])
            self.deal_var.set("")
            self.deal_count_label.config(text="No groups available")
            self.edit_button.config(state="disabled")

    def validate_group_on_change(self, event):
        """Validate group as user types and update deal dropdown"""
        group_name = self.group_entry.get().strip()

        if not group_name:
            self.deal_dropdown.config(state="disabled", values=[])
            self.deal_var.set("")
            self.deal_count_label.config(text="")
            self.edit_button.config(state="disabled")
            return

        if not group_name.startswith("Group"):
            group_name = "Group" + group_name

        group_dir = os.path.join(self.base_directory, group_name)

        if not os.path.exists(group_dir):
            self.deal_dropdown.config(state="disabled", values=[])
            self.deal_var.set("")
            self.deal_count_label.config(text="Group not found")
            self.edit_button.config(state="disabled")
            return

        csv_dir = os.path.join(group_dir, "CSV")
        if not os.path.exists(csv_dir):
            self.deal_dropdown.config(state="disabled", values=[])
            self.deal_var.set("")
            self.deal_count_label.config(text="CSV directory not found")
            self.edit_button.config(state="disabled")
            return

        csv_file = os.path.join(csv_dir, "HandsFromAI.csv")
        if not os.path.exists(csv_file):
            self.deal_dropdown.config(state="disabled", values=[])
            self.deal_var.set("")
            self.deal_count_label.config(text="HandsFromAI.csv not found")
            self.edit_button.config(state="disabled")
            return

        self.load_deals_for_group(group_name)

    def get_deal_range_for_group(self, group_number):
        """
        Returns the deal range (start, end) for a given group number.

        Standard groups:
        - Odd groups (1, 3, 5, ...): deals 1-32
        - Even groups (2, 4, 6, ...): deals 33-64

        Special groups:
        - Group 33: deals 1-24 (only 24 boards)
        - Group 34: deals 25-48 (only 24 boards)
        """
        if group_number == 33:
            return (1, 24)
        elif group_number == 34:
            return (25, 48)
        elif group_number % 2 == 1:  # Odd groups
            return (1, 32)
        else:  # Even groups
            return (33, 64)

    def load_deals_for_group(self, group_name):
        """Load deal numbers for the selected group"""
        csv_dir = os.path.join(self.base_directory, group_name, "CSV")
        csv_file = os.path.join(csv_dir, "HandsFromAI.csv")

        try:
            self.deals = self.parse_csv_file(csv_file)
            if not self.deals:
                self.deal_dropdown.config(state="disabled", values=[])
                self.deal_var.set("")
                self.deal_count_label.config(text="No valid deals found")
                self.edit_button.config(state="disabled")
                return

            # Extract group number from group_name (e.g., "Group33" -> 33)
            group_number = int(group_name.replace("Group", ""))

            # Get the valid deal range for this group
            start_deal, end_deal = self.get_deal_range_for_group(group_number)

            # DEBUG PRINTS - Remove these after testing
            print(f"Loading group: {group_name}")
            print(f"Group number extracted: {group_number}")
            print(f"Deal range returned: {start_deal} to {end_deal}")

            # Filter deals to only include those in the valid range
            all_deals = list(set(deal["info"]["deal"] for deal in self.deals))

            # DEBUG: Show all deals before filtering
            print(
                f"All deals found in CSV: {sorted(all_deals, key=lambda x: int(x) if x.isdigit() else 0)}"
            )

            available_deals = [
                deal
                for deal in all_deals
                if deal.isdigit() and start_deal <= int(deal) <= end_deal
            ]

            # Sort the filtered deals
            available_deals = sorted(
                available_deals,
                key=lambda x: int(x) if x.isdigit() else x,
            )

            # DEBUG: Show filtered deals
            print(
                f"Deals after filtering for range {start_deal}-{end_deal}: {available_deals}"
            )

            self.deal_dropdown.config(values=available_deals, state="readonly")
            if available_deals:
                self.deal_var.set(available_deals[0])
                self.deal_count_label.config(
                    text=f"({len(available_deals)} deals available: {start_deal}-{end_deal})"
                )
                self.edit_button.config(state="normal")
            else:
                self.deal_var.set("")
                self.deal_count_label.config(
                    text=f"(No deals available for range {start_deal}-{end_deal})"
                )
                self.edit_button.config(state="disabled")

        except Exception as e:
            print(f"Error loading CSV: {str(e)}")
            import traceback

            traceback.print_exc()
            self.deal_dropdown.config(state="disabled", values=[])
            self.deal_var.set("")
            self.deal_count_label.config(text="Error loading deals")
            self.edit_button.config(state="disabled")

    def get_available_groups(self):
        groups = []
        try:
            for item in os.listdir(self.base_directory):
                item_path = os.path.join(self.base_directory, item)
                if os.path.isdir(item_path) and item.startswith("Group"):
                    groups.append(item)
            groups.sort()
        except Exception as e:
            print(f"Error getting group directories: {e}")
            messagebox.showerror(
                "Error", f"Could not access the base directory:\n{str(e)}"
            )
        return groups

    def edit_selected_hand(self):
        selected_deal = self.deal_var.get()
        if not selected_deal:
            messagebox.showerror("Error", "Please select a deal")
            return

        for i, deal in enumerate(self.deals):
            if deal["info"]["deal"] == selected_deal:
                self.current_deal_index = i
                break

        print(f"Editing deal {selected_deal}, index {self.current_deal_index}")

        try:
            current_deal = self.deals[self.current_deal_index]
            hands = current_deal["hands"]

            # --- Dealer/Bidding validation (insert your helper here if needed) ---
            # if not self.validate_dealer_bidding(ask_continue_on_error=False):
            #  return
            # ---------------------------------------------------------

            # Validate/correct card formatting
            corrections, problems = self.validate_and_correct_cards(hands)
            msg = ""
            if corrections:
                msg += "Card format corrections:\n" + "\n".join(corrections)
            if problems:
                msg += "\nInvalid cards detected:\n" + "\n".join(problems)
            if msg:
                messagebox.showwarning("Card Data Corrections", msg)

            contract = current_deal["info"]["contract"]
            north_cards = [card["card"] for card in hands["north"]]
            north_sequences = [card["sequence"] for card in hands["north"]]
            # re_suited_north = self.resuit_north_hand(
            #     north_cards, contract, north_sequences
            # )

            # new_north_hand = []
            # for i, new_card in enumerate(re_suited_north):
            #     sequence = north_sequences[i] if i < len(north_sequences) else ""
            #     new_north_hand.append({"card": new_card, "sequence": sequence})
            # hands["north"] = new_north_hand[:13]

            # Clear all widgets from the screen
            for widget in self.root.winfo_children():
                widget.destroy()

            self.create_menu()
            self.create_toolbar()
            self.create_main_view()
            self.update_view()

            # Restore editor window size and center
            desired_w, desired_h = 1200, 700
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = (screen_w - desired_w) // 2
            y = (screen_h - desired_h) // 2
            self.root.geometry(f"{desired_w}x{desired_h}+{x}+{y}")

            print("Calling find_duplicates from edit_selected_hand")
            self.find_duplicates(edited_position=None)

        except Exception as e:
            print(f"Error in edit_selected_hand: {str(e)}")
            messagebox.showerror("Error", f"Failed to load deal: {str(e)}")

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Select Group", command=self.show_group_selection)
        file_menu.add_command(
            label="Export Current Deal", command=self.export_current_deal
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Find Duplicates", command=self.find_duplicates)
        edit_menu.add_command(label="Clear Highlights", command=self.clear_highlights)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar)

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=2)

        ttk.Button(toolbar, text="Previous Deal", command=self.previous_deal).pack(
            side=tk.LEFT, padx=2, pady=2
        )

        self.deal_label = ttk.Label(toolbar, text="Deal 1 of 1")
        self.deal_label.pack(side=tk.LEFT, padx=5, pady=2)

        ttk.Button(toolbar, text="Next Deal", command=self.next_deal).pack(
            side=tk.LEFT, padx=2, pady=2
        )

        deal_select_frame = ttk.Frame(toolbar)
        deal_select_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(deal_select_frame, text="Select Deal:").pack(side=tk.LEFT, padx=2)

        deal_numbers = [deal["info"]["deal"] for deal in self.deals]
        self.toolbar_deal_var = tk.StringVar()
        if deal_numbers:
            self.toolbar_deal_var.set(deal_numbers[self.current_deal_index])

        self.deal_dropdown = ttk.Combobox(
            deal_select_frame,
            textvariable=self.toolbar_deal_var,
            values=deal_numbers,
            width=10,
        )
        self.deal_dropdown.pack(side=tk.LEFT, padx=2)
        self.deal_dropdown.bind(
            "<<ComboboxSelected>>", self.on_toolbar_deal_selection_change
        )

        # Add Export Current Deal button
        ttk.Button(
            toolbar, text="Export Current Deal", command=self.export_current_deal
        ).pack(side=tk.LEFT, padx=2, pady=2)

    def on_toolbar_deal_selection_change(self, event):
        selected_deal = self.toolbar_deal_var.get()

        for i, deal in enumerate(self.deals):
            if deal["info"]["deal"] == selected_deal:
                self.current_deal_index = i

                # Re-suit North hand for the selected deal
                hands = self.deals[self.current_deal_index]["hands"]
                contract = self.deals[self.current_deal_index]["info"]["contract"]

                north_cards = [card["card"] for card in hands["north"]]
                north_sequences = [card["sequence"] for card in hands["north"]]
                # re_suited_north = self.resuit_north_hand(
                #     north_cards, contract, north_sequences
                # )

                # new_north_hand = []
                # for i, new_card in enumerate(re_suited_north):
                #     sequence = north_sequences[i] if i < len(north_sequences) else ""
                #     new_north_hand.append({"card": new_card, "sequence": sequence})

                # hands["north"] = new_north_hand[:13]  # Update with re-suited hand

                self.update_view()
                self.find_duplicates()
                break

    def create_main_view(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Configure ttk style for left_frame to ensure white background
        style = ttk.Style()
        style.configure("White.TFrame", background="white")

        left_frame = ttk.Frame(main_frame, style="White.TFrame")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Header section
        top_frame = tk.Frame(left_frame, bg="white")
        top_frame.pack(fill=tk.X)

        header_info_frame = tk.Frame(top_frame, bg="white")
        header_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.group_deal_label = tk.Label(
            header_info_frame,
            text="Group ? - Deal ?",
            font=("Arial", 16, "bold"),
            bg="white",
            anchor="w",
        )
        self.group_deal_label.pack(fill=tk.X, pady=1)

        # Create editable info frame instead of label
        info_edit_frame = tk.Frame(header_info_frame, bg="white")
        info_edit_frame.pack(fill=tk.X, pady=1)

        # Dealer field
        tk.Label(info_edit_frame, text="Dealer:", font=("Arial", 11), bg="white").pack(
            side=tk.LEFT, padx=(0, 2)
        )
        self.dealer_entry = tk.Entry(
            info_edit_frame, font=("Arial", 11), width=2, justify="center"
        )
        self.dealer_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Vulnerability field
        tk.Label(
            info_edit_frame, text="Vulnerability:", font=("Arial", 11), bg="white"
        ).pack(side=tk.LEFT, padx=(0, 2))
        self.vul_entry = tk.Entry(
            info_edit_frame, font=("Arial", 11), width=2, justify="center"
        )
        self.vul_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Contract field
        tk.Label(
            info_edit_frame, text="Contract:", font=("Arial", 11), bg="white"
        ).pack(side=tk.LEFT, padx=(0, 2))
        self.contract_entry = tk.Entry(
            info_edit_frame, font=("Arial", 11), width=4, justify="left"
        )
        self.contract_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Bind validation events - validate when leaving field, not on every keystroke
        self.dealer_entry.bind("<FocusOut>", self.validate_dealer)
        self.vul_entry.bind("<FocusOut>", self.validate_vulnerability)
        self.contract_entry.bind("<FocusOut>", self.validate_contract)

        # Content area with hands and image
        content_frame = tk.Frame(left_frame, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Hands container (left side)
        hands_container = tk.Frame(content_frame, bg="white")
        hands_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.hands_frame = tk.Frame(hands_container, bg="white")
        self.hands_frame.pack(fill=tk.BOTH, expand=True)

        # Create hand frames
        self.north_frame = self.create_hand_frame(self.hands_frame, "North hand")
        self.north_frame.pack(fill=tk.X, pady=2)

        self.south_frame = self.create_hand_frame(self.hands_frame, "South hand")
        self.south_frame.pack(fill=tk.X, pady=2)

        self.east_frame = self.create_hand_frame(self.hands_frame, "East hand")
        self.east_frame.pack(fill=tk.X, pady=2)

        self.west_frame = self.create_hand_frame(self.hands_frame, "West hand")
        self.west_frame.pack(fill=tk.X, pady=2)

        # Bidding section
        bidding_container = tk.Frame(self.hands_frame, bg="white")
        bidding_container.pack(fill=tk.X, pady=1)

        bidding_container.grid_columnconfigure(1, weight=1)

        bidding_label = tk.Label(
            bidding_container, text="Bidding", font=("Arial", 14, "bold"), bg="white"
        )
        bidding_label.grid(row=0, column=0, sticky="w", padx=(5, 10), pady=0)

        self.bidding_frame = tk.Frame(bidding_container, bg="white")
        self.bidding_frame.grid(row=0, column=1, sticky="w")

        self.bidding_entries = {"north": [], "east": [], "south": [], "west": []}

        for i, direction in enumerate(["north", "east", "south", "west"]):
            direction_frame = tk.Frame(self.bidding_frame, bg="white")
            direction_frame.grid(row=i, column=0, sticky="w", pady=0)

            for j in range(8):
                entry = tk.Entry(direction_frame, font=("Arial", 12), width=3)
                entry.grid(row=0, column=j, padx=1, pady=1)
                self.bidding_entries[direction].append(entry)

        # Image frame (center)
        self.image_frame = tk.Frame(content_frame, bg="white")
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.image_label = tk.Label(self.image_frame, bg="white")
        self.image_label.place(x=5, y=10, anchor="nw")

        # Right side container for buttons and duplicates (positioned closer to image)
        right_container = tk.Frame(main_frame, bg="white", width=180)
        right_container.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        right_container.pack_propagate(False)

        # Buttons frame at top of right container
        buttons_frame = tk.Frame(right_container, bg="white")
        buttons_frame.pack(fill=tk.X, pady=(0, 5))

        # Find Duplicates and Clear Highlights buttons
        find_dup_btn = tk.Button(
            buttons_frame,
            text="Find Duplicates",
            command=self.find_duplicates,
            font=("Arial", 9),
        )
        find_dup_btn.pack(fill=tk.X, pady=1)

        clear_btn = tk.Button(
            buttons_frame,
            text="Clear Highlights",
            command=self.clear_highlights,
            font=("Arial", 9),
        )
        clear_btn.pack(fill=tk.X, pady=1)

        # Duplicates frame below buttons
        self.right_duplicates_frame = tk.LabelFrame(
            right_container,
            text="Duplicate Cards",
            font=("Arial", 12, "bold"),
            bg="white",
        )
        self.right_duplicates_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    def validate_dealer(self, event):
        """Validate dealer entry (N, S, E, W only)"""
        value = self.dealer_entry.get().upper()
        if value and value not in ["N", "S", "E", "W"]:
            # Remove invalid characters
            valid_value = "".join(c for c in value if c in "NSEW")[:1]
            self.dealer_entry.delete(0, tk.END)
            self.dealer_entry.insert(0, valid_value)
        elif len(value) > 1:
            # Limit to 1 character
            self.dealer_entry.delete(1, tk.END)

    def validate_vulnerability(self, event):
        """Validate vulnerability entry (N, E, B, 0 only)"""
        value = self.vul_entry.get().upper()
        if value and value not in ["N", "E", "B", "0"]:
            # Remove invalid characters
            valid_value = "".join(c for c in value if c in "NEB0")[:1]
            self.vul_entry.delete(0, tk.END)
            self.vul_entry.insert(0, valid_value)
        elif len(value) > 1:
            # Limit to 1 character
            self.vul_entry.delete(1, tk.END)

    def validate_contract(self, event):
        """Validate contract entry (must be non-empty and valid); stays red if invalid."""
        value = self.contract_entry.get().strip().upper()

        # Always update the field to show uppercase version
        if value != self.contract_entry.get():
            self.contract_entry.delete(0, tk.END)
            self.contract_entry.insert(0, value)

        if not value or not self.is_valid_contract(value):
            # Invalid: set red and keep it red until fixed
            self.contract_entry.config(bg="#ffcccc")
            print("Contract field is empty or invalid")
        else:
            # Valid: set white
            self.contract_entry.config(bg="white")
            print(f"Valid contract: {value}")

    def validate_dealer_bidding(self, ask_continue_on_error=False):
        """
        Checks that the dealer (N/E/S/W) has at least as many bids as any other player.
        Shows an error (or ask to continue if export).
        Returns True (validation passes or user chooses to continue), or False (cancel).
        """
        directions = ["N", "E", "S", "W"]
        current_deal = self.deals[self.current_deal_index]
        dealer = current_deal["info"]["dealer"]  # Single letter format: N, E, S, W
        bidding = current_deal["bidding"]  # Full name format: north, east, south, west

        if dealer not in directions:
            messagebox.showerror("Dealer Error", "Dealer must be N, E, S, or W.")
            return False

        # Convert single letter dealer to full name for bidding lookup
        dealer_map = {"N": "north", "E": "east", "S": "south", "W": "west"}
        dealer_full = dealer_map[dealer]

        if dealer_full not in bidding:
            messagebox.showerror("Dealer Error", "Bidding data is missing for dealer.")
            return False

        dealer_bids = len([b for b in bidding[dealer_full] if b])

        # Check all other directions
        for direction_letter in directions:
            if direction_letter == dealer:
                continue

            direction_full = dealer_map[direction_letter]
            if direction_full not in bidding:
                continue

            other_bids = len([b for b in bidding[direction_full] if b])
            if other_bids > dealer_bids:
                if ask_continue_on_error:
                    result = messagebox.askyesno(
                        "Dealer/Bid Error",
                        f"Dealer {dealer} has {dealer_bids} bids but {direction_letter} has {other_bids} bids. Continue with export?",
                    )
                    return result  # True if user chooses Yes
                else:
                    messagebox.showerror(
                        "Dealer/Bid Error",
                        f"Dealer {dealer} has {dealer_bids} bids but {direction_letter} has {other_bids} bids.",
                    )
                    return False
        return True

    def create_hand_frame(self, parent, title):
        frame = tk.LabelFrame(
            parent, text=title, font=("Arial", 14, "bold"), bg="white"
        )
        self.card_frames = tk.Frame(frame, padx=1, pady=1, bg="white")
        self.card_frames.pack(fill=tk.X, padx=5, pady=2)
        return frame

    def display_hand(self, parent_frame, cards, hand_type):
        # Debug check to verify 13 cards
        print(f"- Cards for {hand_type}: {cards}")

        card_container = tk.Frame(parent_frame, bg="white", width=400)
        card_container.pack_propagate(False)
        card_container.pack(fill=tk.NONE, expand=False)

        for i, card_data in enumerate(cards):
            highlight_key = f"{hand_type}-{i}"
            card_bg = "white"
            is_duplicate = highlight_key in self.duplicate_highlights

            button_text = "E"
            button_bg = "#e0e0e0"

            if is_duplicate:
                color_index = self.duplicate_highlights[highlight_key]
                button_bg = self.highlight_colors[color_index]
                button_text = "D"

            card_frame = tk.Frame(
                card_container, padx=0, pady=0, bg=card_bg, borderwidth=0, relief="flat"
            )
            card_frame.grid(row=0, column=i, padx=0, sticky="nsew")

            card_str = card_data["card"]
            sequence = card_data["sequence"]

            rank, suit = self.parse_card(card_str)

            canvas = tk.Canvas(
                card_frame,
                width=18,
                height=45,
                bg=card_bg,
                highlightthickness=0,
                borderwidth=0,
            )
            canvas.pack(pady=0)

            color = "red" if suit in ["H", "D"] else "black"
            canvas.create_text(9, 12, text=rank, font=("Arial", 18, "bold"), fill=color)

            suit_symbol = self.get_suit_symbol(suit)
            canvas.create_text(
                9, 28, text=suit_symbol, font=("Arial", 18, "bold"), fill=color
            )

            seq_label = tk.Label(
                card_frame,
                text=sequence,
                font=("Arial", 12),
                bg=card_bg,
                padx=0,
                pady=0,
            )
            seq_label.pack(pady=0)

            edit_btn = tk.Button(
                card_frame,
                text=button_text,
                font=("Arial", 9),
                command=lambda h=hand_type, i=i, c=card_data: self.edit_card(h, i, c),
                padx=0,
                pady=0,
                width=2,
                height=1,
                bg=button_bg,
                relief="raised" if is_duplicate else "flat",
                borderwidth=2 if is_duplicate else 1,
            )
            edit_btn.pack(pady=0)

        # CHANGE: Set fixed width for each column and prevent container expansion
        card_container.pack_propagate(False)  # Prevent container from expanding
        for i in range(len(cards)):
            card_container.grid_columnconfigure(i, weight=0, minsize=30, uniform="card")

    def update_duplicate_list(self):
        # Ensure the frame exists before proceeding
        if not hasattr(self, "right_duplicates_frame"):
            print("right_duplicates_frame not found!")
            return

        # Debug print to confirm method is called
        print("Updating duplicate list, clearing right_duplicates_frame")

        # Clear all existing widgets in the right_duplicates_frame
        for widget in self.right_duplicates_frame.winfo_children():
            widget.destroy()

        # If no duplicates, display a message and return
        if not self.duplicate_highlights:
            tk.Label(
                self.right_duplicates_frame,
                text="No duplicates found",
                font=("Arial", 10),
                bg="white",
            ).pack(pady=10)
            return

        # Group duplicates by their highlight color
        color_to_cards = {}
        for key, color_index in self.duplicate_highlights.items():
            hand_type, index = key.split("-")
            hand_index = int(index)
            card_data = self.deals[self.current_deal_index]["hands"][hand_type][
                hand_index
            ]
            card_str = card_data["card"]

            if color_index not in color_to_cards:
                color_to_cards[color_index] = []
            color_to_cards[color_index].append(f"{hand_type.capitalize()}: {card_str}")

        # Display each set of duplicates with their respective highlight color
        for set_number, (color_index, cards) in enumerate(
            color_to_cards.items(), start=1
        ):
            color = self.highlight_colors[color_index]

            dup_frame = tk.Frame(self.right_duplicates_frame, bg=color, padx=2, pady=2)
            dup_frame.pack(fill=tk.X, padx=2, pady=2)

            tk.Label(
                dup_frame,
                text=f"Set {set_number}: {', '.join(cards)}",
                bg=color,
                font=("Arial", 9),
                wraplength=170,
            ).pack(anchor="w")

    def parse_card(self, card_str):
        if not card_str or not isinstance(card_str, str):
            return "", ""

        card_str = card_str.strip('"')
        suit_indices = [card_str.rfind(suit) for suit in "SHDC"]
        suit_index = max(suit_indices)

        if suit_index == -1:
            return card_str, ""

        rank = card_str[:suit_index]
        suit = card_str[suit_index]

        if rank == "10":
            rank = "T"

        return rank, suit

    def get_suit_symbol(self, suit):
        symbols = {"S": "\u2660", "H": "\u2665", "D": "\u2666", "C": "\u2663"}
        return symbols.get(suit, "")

    def get_opposite_suit(self, suit):
        """Return the opposite suit of the same color."""
        suit_pairs = {"S": "C", "C": "S", "H": "D", "D": "H"}
        return suit_pairs.get(suit, suit)

    def _rank_value(self, rank):
        """Convert rank to a numerical value for comparison."""
        rank_order = {
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
        return rank_order.get(rank, 0)

    def resuit_north_hand(self, cards, contract, sequences):
        """Re-suit the North hand based on the contract and rank group distribution, preserving original order."""
        if not cards or not contract or len(cards) != 13 or len(sequences) != 13:
            return cards

        # Parse the contract to get the trump suit and level
        # FIXED: Strip X/XX from end before extracting trump
        contract_base = contract.rstrip("X").strip()

        # Handle notrump contracts and single suits
        if contract_base.endswith("NT"):
            trump_suit = "N"
        elif contract_base and contract_base[-1] in ["C", "D", "H", "S", "N"]:
            trump_suit = contract_base[-1]
        else:
            trump_suit = None

        # Extract level from original contract (first character)
        level = int(contract[0]) if contract and contract[0].isdigit() else 1

        print(f"Parsed contract: {contract}, trump_suit: {trump_suit}, level: {level}")

        # Combine cards and sequences for processing
        hand_with_sequences = list(zip(cards, sequences))

        # Group ranks into up to 4 groups based on descending order in original hand
        rank_groups = [[]]
        for i, (card, seq) in enumerate(hand_with_sequences):
            if not card:
                continue

            rank = card[:-1]

            if i == 0:
                rank_groups[0].append((card, seq))
            else:
                last_group = rank_groups[-1]
                last_card = last_group[-1][0]
                last_rank = last_card[:-1]

                current_rank_value = self._rank_value(rank)
                last_rank_value = self._rank_value(last_rank)

                if (
                    current_rank_value < last_rank_value
                ):  # Strictly descending rank, continue in same group
                    rank_groups[-1].append((card, seq))
                else:
                    # Start a new group if the rank is greater than or equal to the previous rank
                    rank_groups.append([(card, seq)])

            # Ensure no more than 4 groups
            if len(rank_groups) == 4:
                rank_groups[3].extend(
                    [(c, s) for c, s in hand_with_sequences[i + 1 :] if c]
                )
                break

        # Determine the suit of Group 1
        if rank_groups[0]:
            group1_suits = [card[0][-1] for card, _ in rank_groups[0] if card]
            group1_suit = (
                max(set(group1_suits), key=group1_suits.count) if group1_suits else None
            )
        else:
            group1_suit = None

        print(f"Rank groups: {[[(c, s) for c, s in group] for group in rank_groups]}")
        print(f"Suit of Group 1: {group1_suit}")

        # Check suit distribution across groups
        suit_in_other_groups = {
            "S": any(
                any(card[-1] == "S" for card, _ in group) for group in rank_groups[1:]
            ),
            "H": any(
                any(card[-1] == "H" for card, _ in group) for group in rank_groups[1:]
            ),
            "D": any(
                any(card[-1] == "D" for card, _ in group) for group in rank_groups[1:]
            ),
            "C": any(
                any(card[-1] == "C" for card, _ in group) for group in rank_groups[1:]
            ),
        }

        print(f"Suit presence in other groups: {suit_in_other_groups}")

        # Re-suit only if conditions are met
        if trump_suit in ["S", "N"]:
            should_resuit = group1_suit != "S" or suit_in_other_groups["S"]
            if should_resuit:
                print(f"Re-suiting for contract {contract} (S or N), order: S-H-C-D")
                return self._resuit_hand(
                    hand_with_sequences, rank_groups, ["S", "H", "C", "D"]
                )
            print(
                f"No re-suiting for contract {contract} (S or N), S is dominant and not in other groups"
            )
            return [card for card, _ in hand_with_sequences]

        elif trump_suit == "H":
            should_resuit = group1_suit != "H" or suit_in_other_groups["H"]
            if should_resuit:
                print(f"Re-suiting for contract {contract} (H), order: H-S-D-C")
                return self._resuit_hand(
                    hand_with_sequences, rank_groups, ["H", "S", "D", "C"]
                )
            print(
                f"No re-suiting for contract {contract} (H), H is dominant and not in other groups"
            )
            return [card for card, _ in hand_with_sequences]

        elif trump_suit == "C" or trump_suit == "D":
            if trump_suit == "C":
                print(f"Re-suiting for contract {contract} (C), order: C-H-S-D")
                return self._resuit_hand(
                    hand_with_sequences, rank_groups, ["C", "H", "S", "D"]
                )
            elif trump_suit == "D":
                print(f"Re-suiting for contract {contract} (D), order: D-C-H-S")
                return self._resuit_hand(
                    hand_with_sequences, rank_groups, ["D", "S", "H", "C"]
                )

        return [card for card, _ in hand_with_sequences]

    def update_bidding_from_entries(self):
        """Read bidding data from UI entries and update the current deal data"""
        if not self.deals or self.current_deal_index >= len(self.deals):
            return

        current_deal = self.deals[self.current_deal_index]
        bidding = current_deal["bidding"]

        # Read bidding entries from the UI and update the deal data
        for direction in ["north", "east", "south", "west"]:
            bids = []
            for entry in self.bidding_entries[direction]:
                bid_text = entry.get().strip()
                if bid_text:
                    bids.append(bid_text)

            # Pad to ensure consistent length
            while len(bids) < 8:  # Or whatever length you want
                bids.append("")

            bidding[direction] = bids

        print(f"Updated bidding data from UI entries")

    def _resuit_hand(self, hand_with_sequences, rank_groups, suit_order):
        """Helper method to re-suit the hand based on the given suit order and rank groups, preserving original order."""
        # Extract the original cards and sequences
        cards = [card for card, _ in hand_with_sequences]
        sequences = [seq for _, seq in hand_with_sequences]

        # Create a mapping of original positions
        card_positions = [
            (card, idx) for idx, (card, _) in enumerate(hand_with_sequences) if card
        ]

        # Determine the new suits for each rank group
        new_cards = [""] * len(cards)
        current_suit_idx = 0

        for group_idx, group in enumerate(rank_groups):
            if current_suit_idx < len(suit_order):
                new_suit = suit_order[current_suit_idx]
            else:
                new_suit = suit_order[-1]  # Cycle to the last suit if needed

            # Assign the new suit to all cards in this group, preserving their original order
            for card, seq in group:
                original_idx = next(
                    (
                        idx
                        for idx, (c, s) in enumerate(hand_with_sequences)
                        if c == card and s == seq
                    ),
                    None,
                )
                if original_idx is not None and card:
                    rank = card[:-1]
                    new_card = f"{rank}{new_suit}" if rank != "10" else f"10{new_suit}"
                    new_cards[original_idx] = new_card

            current_suit_idx += 1

        print(f"Re-suited cards: {new_cards}")
        return new_cards[:13]

    def edit_card(self, hand_type, card_index, card=None):
        card_data = self.deals[self.current_deal_index]["hands"][hand_type][card_index]
        card = card_data["card"]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Change card for {card}")
        dialog.transient(self.root)  # Keep dialog on top of main window
        dialog.grab_set()  # Make dialog modal

        # Position dialog relative to main window
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        dialog.geometry(
            f"650x270+{main_x + 200}+{main_y + 200}"
        )  # Slightly taller for OK/Cancel buttons

        # Track the selected suit, rank, and sequence
        self.selected_suit = None
        self.selected_rank = None
        self.selected_sequence = None

        # Current card display
        current_frame = tk.Frame(dialog)
        current_frame.pack(pady=5)
        rank, suit = self.parse_card(card)
        current_sequence = card_data["sequence"]
        tk.Label(
            current_frame,
            text=f"Current: {card} (Sequence: {current_sequence})",
            font=("Arial", 12, "bold"),
        ).pack()

        # Suit buttons (horizontal)
        suit_frame = tk.Frame(dialog)
        suit_frame.pack(pady=5)
        tk.Label(suit_frame, text="Change Suit:", font=("Arial", 12)).grid(
            row=0, column=0, padx=5
        )

        suits = [
            ("♠", "S", "black"),
            ("♥", "H", "red"),
            ("♦", "D", "red"),
            ("♣", "C", "black"),
        ]

        for col, (symbol, suit_code, color) in enumerate(suits, start=1):
            tk.Button(
                suit_frame,
                text=symbol,
                font=("Arial", 20),
                fg=color,
                command=lambda s=suit_code: self.select_suit(s),
            ).grid(row=0, column=col, padx=5)

        # Rank buttons (horizontal)
        rank_frame = tk.Frame(dialog)
        rank_frame.pack(pady=5)
        tk.Label(rank_frame, text="Change Card:", font=("Arial", 12)).grid(
            row=0, column=0, padx=5
        )

        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
        for col, rank_val in enumerate(ranks, start=1):
            tk.Button(
                rank_frame,
                text=rank_val,
                font=("Arial", 12),
                width=2,
                command=lambda r=rank_val: self.select_rank(r),
            ).grid(row=0, column=col, padx=2)

        # Play Sequence buttons (horizontal)
        sequence_frame = tk.Frame(dialog)
        sequence_frame.pack(pady=(20, 5))
        tk.Label(sequence_frame, text="Change Play Seq:", font=("Arial", 12)).grid(
            row=0, column=0, padx=5
        )
        for seq_num in range(1, 14):
            tk.Button(
                sequence_frame,
                text=str(seq_num),
                font=("Arial", 12),
                width=2,
                command=lambda s=str(seq_num): self.select_sequence(s),
            ).grid(row=0, column=seq_num, padx=2)

        # OK and Cancel buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        def ok_action():
            card_data = self.deals[self.current_deal_index]["hands"][hand_type][
                card_index
            ]
            card = card_data["card"]
            current_sequence = card_data["sequence"]
            rank, suit = self.parse_card(card)

            # Determine the new rank, suit, and sequence
            new_rank = self.selected_rank if self.selected_rank else rank
            new_suit = self.selected_suit if self.selected_suit else suit
            new_sequence = (
                self.selected_sequence if self.selected_sequence else current_sequence
            )
            new_card = f"{new_rank}{new_suit}"

            # Only apply check for East/West hands
            if hand_type in ["east", "west"]:
                north_cards = [
                    c["card"]
                    for c in self.deals[self.current_deal_index]["hands"]["north"]
                ]
                south_cards = [
                    c["card"]
                    for c in self.deals[self.current_deal_index]["hands"]["south"]
                ]
                ns_cards = set(north_cards + south_cards)
                if new_card in ns_cards:
                    messagebox.showerror(
                        "Duplicate Card Error",
                        f"Card '{new_card}' is already in North or South hands. Please choose a different card.",
                    )
                    return

            # Save the change
            self.deals[self.current_deal_index]["hands"][hand_type][card_index][
                "card"
            ] = new_card
            self.deals[self.current_deal_index]["hands"][hand_type][card_index][
                "sequence"
            ] = new_sequence

            print(
                f"Card changed from {card} to {new_card}, sequence: {current_sequence} -> {new_sequence}"
            )

            self.selected_suit = None
            self.selected_rank = None
            self.selected_sequence = None

            # Update the view and close the dialog
            self.find_duplicates()
            self.update_view()
            dialog.destroy()

        tk.Button(
            button_frame,
            text="OK",
            font=("Arial", 12),
            command=ok_action,
            bg="#4CAF50",
            fg="white",
            padx=20,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Cancel",
            font=("Arial", 12),
            command=dialog.destroy,
            bg="#f44336",
            fg="white",
            padx=20,
        ).pack(side=tk.LEFT, padx=10)

    def select_suit(self, new_suit):
        """Handle suit selection without closing dialog"""
        self.selected_suit = new_suit
        print(f"Selected suit: {new_suit}")

    def select_rank(self, new_rank):
        """Handle rank selection without closing dialog"""
        self.selected_rank = new_rank
        print(f"Selected rank: {new_rank}")

    def select_sequence(self, new_sequence):
        """Handle sequence selection without closing dialog"""
        self.selected_sequence = new_sequence
        print(f"Selected sequence: {new_sequence}")

    def confirm_card_change(self, hand_type, card_index, dialog):
        """Apply all selected changes and close the dialog"""
        card_data = self.deals[self.current_deal_index]["hands"][hand_type][card_index]
        card = card_data["card"]
        current_sequence = card_data["sequence"]

        rank, suit = self.parse_card(card)

        # Determine the new rank, suit, and sequence
        new_rank = self.selected_rank if self.selected_rank else rank
        new_suit = self.selected_suit if self.selected_suit else suit
        new_sequence = (
            self.selected_sequence if self.selected_sequence else current_sequence
        )

        # Create the new card and update both card and sequence
        new_card = f"{new_rank}{new_suit}"
        self.deals[self.current_deal_index]["hands"][hand_type][card_index][
            "card"
        ] = new_card
        self.deals[self.current_deal_index]["hands"][hand_type][card_index][
            "sequence"
        ] = new_sequence

        print(
            f"Card changed from {card} to {new_card}, sequence: {current_sequence} -> {new_sequence}"
        )

        # Reset selections
        self.selected_suit = None
        self.selected_rank = None
        self.selected_sequence = None

        # Update the view and close the dialog
        self.find_duplicates()
        self.update_view()
        dialog.destroy()

    def find_duplicates(self, edited_position=None):
        """
        Find duplicate cards and highlight them, but DO NOT automatically change them.
        Only provides visual feedback for the user to manually resolve duplicates.
        """
        print("Entering find_duplicates method (highlight-only version)")
        self.duplicate_highlights = {}

        if not self.deals or self.current_deal_index >= len(self.deals):
            print("No deals or invalid index, skipping find_duplicates")
            return 0

        current_deal = self.deals[self.current_deal_index]
        hands = current_deal["hands"]

        # Collect all cards from all hands
        all_cards = []
        for hand_type, cards in hands.items():
            for i, card_data in enumerate(cards):
                card_info = {
                    "card": card_data["card"],
                    "hand": hand_type,
                    "index": i,
                }
                all_cards.append(card_info)

        # Group cards by their value to find duplicates
        card_groups = defaultdict(list)
        for card_info in all_cards:
            card_groups[card_info["card"]].append(card_info)

        # Find all duplicates (cards that appear more than once)
        duplicates = [
            (card, positions)
            for card, positions in card_groups.items()
            if len(positions) > 1
        ]

        print(f"Found {len(duplicates)} duplicate card(s)")

        # Highlight all duplicates with different colors
        for i, (card, positions) in enumerate(duplicates):
            color_index = i % len(self.highlight_colors)
            # Build position list for printing
            pos_list = [f"{pos['hand']}[{pos['index']}]" for pos in positions]
            print(f"Duplicate: {card} appears in {pos_list}")

            for pos in positions:
                key = f"{pos['hand']}-{pos['index']}"
                self.duplicate_highlights[key] = color_index

        # Update the view to show highlights
        self.update_view()

        return len(duplicates)

    def clear_highlights(self):
        self.duplicate_highlights = {}
        self.update_view()

    def update_view(self):
        deal = self.deals[self.current_deal_index]
        info = deal["info"]
        hands = deal["hands"]
        bidding = deal["bidding"]

        # Update header
        group = info["group"]
        deal_num = info["deal"]
        self.group_deal_label.config(text=f"Group {group} - Deal {deal_num}")
        # Update editable info fields
        self.dealer_entry.delete(0, tk.END)
        self.dealer_entry.insert(0, info["dealer"])

        self.vul_entry.delete(0, tk.END)
        self.vul_entry.insert(0, info["vul"])

        self.contract_entry.delete(0, tk.END)
        self.contract_entry.insert(0, info["contract"])
        if self.is_valid_contract(info["contract"]):
            self.contract_entry.config(bg="white")
        else:
            self.contract_entry.config(bg="#ffcccc")
        # Update deal label in toolbar
        self.deal_label.config(
            text=f"Deal {self.current_deal_index + 1} of {len(self.deals)}"
        )
        if hasattr(self, "toolbar_deal_var"):
            self.toolbar_deal_var.set(deal_num)

        # Update hands
        for hand_type, frame in [
            ("north", self.north_frame),
            ("south", self.south_frame),
            ("east", self.east_frame),
            ("west", self.west_frame),
        ]:
            for widget in frame.winfo_children():
                widget.destroy()
            self.display_hand(frame, hands[hand_type], hand_type)

        # Update bidding entries
        for direction in ["north", "east", "south", "west"]:
            bids = bidding[direction]
            for entry in self.bidding_entries[direction]:
                entry.delete(0, tk.END)
                entry.insert(0, "")  # Clear all entries by default

            for i, bid in enumerate(bids):
                if i < len(
                    self.bidding_entries[direction]
                ):  # Ensure we don't exceed available entries
                    self.bidding_entries[direction][i].delete(0, tk.END)
                    self.bidding_entries[direction][i].insert(0, bid)

        # Update image
        try:
            from PIL import Image, ImageTk

            # Construct the image path
            image_path = f"{self.base_directory}\\Group{group}\\images\\ModScans\\m-{group}-{deal_num}.png"

            # Load and resize the image
            image = Image.open(image_path)
            # Increase size to 600x800 while maintaining aspect ratio
            image.thumbnail((600, 1000), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            # Update the image label and keep a reference to prevent garbage collection
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Store reference

        except Exception as e:
            print(f"Error loading image: {e}")
            self.image_label.config(image="")  # Clear the image if loading fails
            self.image_label.image = None

        self.update_duplicate_list()

    def parse_csv_file(self, filename):
        deals = []
        try:
            with open(filename, "r", newline="") as csvfile:
                content = csvfile.read()
                lines = content.splitlines()

                header_indices = [
                    i
                    for i, line in enumerate(lines)
                    if "Group" in line and "Deal" in line
                ]

                for header_idx in header_indices:
                    header_line = lines[header_idx].strip()
                    header_parts = header_line.split(",")

                    if len(header_parts) < 4:  # Only require Group and Deal
                        continue

                    group = header_parts[1].strip().strip('"')
                    deal = header_parts[3].strip().strip('"')
                    dealer = (
                        header_parts[5].strip().strip('"')
                        if len(header_parts) > 5
                        else ""
                    )
                    vul = (
                        header_parts[7].strip().strip('"')
                        if len(header_parts) > 7
                        else ""
                    )
                    contract = (
                        header_parts[9].strip().strip('"')
                        if len(header_parts) > 9
                        else ""
                    )

                    is_high_numbered_deal = False
                    try:
                        if int(deal) >= 50:
                            is_high_numbered_deal = True
                    except:
                        pass

                    def parse_line(line_idx):
                        if line_idx >= len(lines):
                            return ["" for _ in range(13)]
                        line = lines[line_idx].strip()
                        if not line:
                            return ["" for _ in range(13)]
                        items = [
                            item.strip().strip('"')
                            for item in line.split(",")
                            if item.strip()
                        ]
                        return (
                            items + ["" for _ in range(13 - len(items))]
                            if len(items) < 13
                            else items[:13]
                        )

                    def expand_single_card(card):
                        if not card:
                            return []
                        return [card]

                    def map_card_seq(cards, seqs):
                        result = []
                        for j in range(13):  # Ensure exactly 13 cards
                            card = cards[j] if j < len(cards) else ""
                            seq = seqs[j] if j < len(seqs) else ""
                            result.append({"card": card, "sequence": seq})
                        return result

                    north_cards = parse_line(header_idx + 1)
                    north_seq = parse_line(header_idx + 2)
                    south_cards = parse_line(header_idx + 3)
                    south_seq = parse_line(header_idx + 4)
                    east_cards = parse_line(header_idx + 5)
                    east_seq = parse_line(header_idx + 6)
                    west_cards = parse_line(header_idx + 7)
                    west_seq = parse_line(header_idx + 8)

                    # Parse bidding (4 lines after hands: North, East, South, West)
                    north_bidding = parse_line(header_idx + 9)
                    east_bidding = parse_line(header_idx + 10)
                    south_bidding = parse_line(header_idx + 11)
                    west_bidding = parse_line(header_idx + 12)

                    if is_high_numbered_deal:
                        if len(north_cards) == 1:
                            north_cards = expand_single_card(north_cards[0])
                        if len(south_cards) == 1:
                            south_cards = expand_single_card(south_cards[0])
                        if len(east_cards) == 1:
                            east_cards = expand_single_card(east_cards[0])
                        if len(west_cards) == 1:
                            west_cards = expand_single_card(west_cards[0])

                    deal_obj = {
                        "info": {
                            "group": group,
                            "deal": deal,
                            "dealer": dealer,
                            "vul": vul,
                            "contract": contract,
                        },
                        "hands": {
                            "north": map_card_seq(north_cards, north_seq),
                            "south": map_card_seq(south_cards, south_seq),
                            "east": map_card_seq(east_cards, east_seq),
                            "west": map_card_seq(west_cards, west_seq),
                        },
                        "bidding": {
                            "north": north_bidding,
                            "east": east_bidding,
                            "south": south_bidding,
                            "west": west_bidding,
                        },
                    }

                    deals.append(deal_obj)

        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            messagebox.showerror("Error", f"Failed to read CSV file: {str(e)}")

        try:
            deals.sort(key=lambda x: int(x["info"]["deal"]))
        except:
            deals.sort(key=lambda x: x["info"]["deal"])

        return deals


if __name__ == "__main__":
    root = tk.Tk()
    app = BridgeHandEditor(root)
    root.mainloop()
