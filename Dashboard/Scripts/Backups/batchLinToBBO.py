from urllib.parse import quote
import pyperclip
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
import webbrowser
import json

class LinToBboConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("LIN to BBO URL Converter - Folder Browser")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        self.base_url = "https://www.bridgebase.com/tools/handviewer.html?bbo=y&lin="
        self.board_urls = []  # List to store board URLs
        self.initial_dir = "C://Users/maxuk/OneDrive/Software/Projects/Handviewer/Autobridge/Sheets"
        self.current_folder = ""
        
        # Create a directory for saved URL files if it doesn't exist
        self.saved_urls_dir = os.path.join(os.path.expanduser("~"), "BridgeURLs")
        os.makedirs(self.saved_urls_dir, exist_ok=True)
        
        self.create_widgets()

    def extract_board_entries_from_js(self, file_path):
        """Extract board entries from a JavaScript data file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find all query strings in the JavaScript data
        pattern = r'"query":\s*"([^"]+)"'
        matches = re.findall(pattern, content)
        
        # Process each query string
        board_entries = []
        for match in matches:
            # Replace HTML entities
            decoded = match.replace('&amp;', '&')
            
            # The query is already a full BBO URL query string
            # Extract just the LIN part (after "bbo=y&lin=")
            if 'bbo=y&lin=' in decoded:
                lin_part = decoded.split('bbo=y&lin=', 1)[1]
                # URL decode the LIN part
                from urllib.parse import unquote
                try:
                    decoded_lin = unquote(lin_part)
                    board_entries.append(decoded_lin)
                except Exception as e:
                    print(f"Warning: Failed to decode LIN part: {e}")
                    continue
            else:
                # If it doesn't contain the expected format, skip it
                print(f"Warning: Unexpected query format: {decoded[:50]}...")
                continue
        
        return board_entries



    def determine_declarer_from_bidding(organized_bids, dealer_pos_char):
        """
        Determines the declarer by finding the first player of the winning partnership 
        to bid the trump suit of the final contract.
        Partnerships: North-South vs East-West
        """
        # Map dealer to position index (0=North, 1=East, 2=South, 3=West)  
        dealer_map = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        position_names = ['North', 'East', 'South', 'West']
        
        # Define partnerships
        ns_partnership = {'North', 'South'}
        ew_partnership = {'East', 'West'}
        
        dealer_idx = dealer_map.get(dealer_pos_char.upper(), 0)
        
        if not organized_bids:
            return 'South'  # Default fallback
            
        # Find the final contract (last non-pass bid)
        final_contract = None
        final_bidder_idx = -1
        
        current_player_idx = dealer_idx
        for i, bid in enumerate(organized_bids):
            if bid.upper() not in ['P', 'X', 'XX']:
                final_contract = bid.upper()
                final_bidder_idx = current_player_idx
            current_player_idx = (current_player_idx + 1) % 4
        
        if not final_contract or final_bidder_idx == -1:
            return 'South'  # Default fallback
            
        # Determine which partnership won the contract
        final_bidder = position_names[final_bidder_idx]
        if final_bidder in ns_partnership:
            winning_partnership = ns_partnership
        else:
            winning_partnership = ew_partnership
        
        # Extract trump suit from final contract
        trump_suit = None
        if final_contract.endswith('N') or 'NT' in final_contract:
            trump_suit = 'N'  # No Trump
        else:
            for suit in ['C', 'D', 'H', 'S']:
                if suit in final_contract:
                    trump_suit = suit
                    break
        
        if not trump_suit:
            return 'South'  # Default fallback
        
        # Find first player of winning partnership to bid this trump suit
        current_player_idx = dealer_idx
        for bid in organized_bids:
            current_player = position_names[current_player_idx]
            
            # Only check bids from the winning partnership
            if current_player in winning_partnership:
                if bid.upper() not in ['P', 'X', 'XX']:
                    # Check if this bid mentions the trump suit
                    if trump_suit == 'N' and ('N' in bid.upper()):
                        return current_player
                    elif trump_suit != 'N' and trump_suit in bid.upper():
                        return current_player
            
            # Move to next player clockwise
            current_player_idx = (current_player_idx + 1) % 4
        
        return 'South'  # Default fallback


    def create_widgets(self):
        # Main menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select New Folder", command=self.browse_folder)
        file_menu.add_command(label="Load Saved URLs", command=self.load_saved_urls)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Frame for folder selection
        folder_frame = ttk.Frame(self.root, padding="10")
        folder_frame.pack(fill=tk.X)
        
        ttk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.folder_path_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=60)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_folder_btn = ttk.Button(folder_frame, text="Browse Folder", command=self.browse_folder)
        browse_folder_btn.pack(side=tk.LEFT)

        # Current data label
        self.current_data_label = ttk.Label(self.root, text="No folder selected", font=("", 10, "italic"))
        self.current_data_label.pack(anchor=tk.W, padx=10, pady=(5, 0))

        # Frame for deal list
        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for deals
        self.deal_tree = ttk.Treeview(list_frame, columns=("group", "deal_num"), show="headings")
        self.deal_tree.heading("group", text="Group")
        self.deal_tree.heading("deal_num", text="Deal #")
        self.deal_tree.column("group", width=400)
        self.deal_tree.column("deal_num", width=100, anchor=tk.CENTER)
        self.deal_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.deal_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.deal_tree.configure(yscrollcommand=scrollbar.set)
        
        # Double-click event binding
        self.deal_tree.bind("<Double-1>", self.on_deal_double_click)

        # Frame for action buttons
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        open_btn = ttk.Button(button_frame, text="Open in Browser", command=self.open_in_browser)
        open_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        copy_btn = ttk.Button(button_frame, text="Copy URL", command=self.copy_to_clipboard)
        copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_all_btn = ttk.Button(button_frame, text="Save URLs", command=self.save_urls)
        save_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_as_btn = ttk.Button(button_frame, text="Save URLs As...", command=self.save_urls_as)
        save_as_btn.pack(side=tk.LEFT)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_folder(self):
        folder_path = filedialog.askdirectory(
            title="Select folder containing LIN files",
            initialdir=self.initial_dir
        )
        
        if folder_path:
            self.folder_path_var.set(folder_path)
            self.current_folder = folder_path
            self.load_all_deals_from_folder(folder_path)

    def load_all_deals_from_folder(self, folder_path):
        """Load all deals from all LIN and JS files in the selected folder"""
        try:
            # Clear previous data
            self.board_urls = []
            
            # Clear treeview
            for item in self.deal_tree.get_children():
                self.deal_tree.delete(item)

            # Find all LIN and JS files in the folder
            file_paths = []
            for file in os.listdir(folder_path):
                if file.lower().endswith(('.lin', '.js')):
                    file_paths.append(os.path.join(folder_path, file))

            if not file_paths:
                messagebox.showinfo("Information", "No LIN or JS files found in the selected folder.")
                return

            total_deals = 0
            all_deals = []

            # Process each file and collect all deals
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                group_name = os.path.splitext(filename)[0]

                try:
                    # Choose extraction method based on file extension
                    if file_path.lower().endswith('.js'):
                        board_entries = self.extract_board_entries_from_js(file_path)
                    else:
                        board_entries = self.extract_board_entries(file_path)

                    for i, entry in enumerate(board_entries):
                        try:
                            # Extract board number from the entry
                            board_match = re.search(r'ah\|Board (\d+)\|', entry)
                            if board_match:
                                deal_number = board_match.group(1)
                            else:
                                deal_number = str(i + 1)

                            # URL-encode the entry
                            encoded_string = quote(entry)
                            full_url = self.base_url + encoded_string

                            # Add to temporary list with all info - using .get() for safety
                            deal_dict = {
                                "group_name": group_name,
                                "deal_number": deal_number,
                                "board_number": deal_number,
                                "url": full_url
                            }
                            all_deals.append(deal_dict)
                            
                        except Exception as e:
                            print(f"Error processing deal {i+1} from {filename}: {e}")
                            continue

                except Exception as e:
                    print(f"Error processing file {filename}: {e}")
                    messagebox.showwarning("Warning", f"Could not process file {filename}: {str(e)}")
                    continue

            if not all_deals:
                messagebox.showinfo("Information", "No valid deals found in any files.")
                return

            # Sort deals numerically by deal number
            try:
                all_deals.sort(key=lambda deal: int(deal.get("deal_number", "0")))
            except ValueError:
                # If deal numbers aren't all numeric, sort as strings
                all_deals.sort(key=lambda deal: deal.get("deal_number", "0"))

            # Now populate the main list and treeview with sorted deals
            for deal in all_deals:
                try:
                    # Use .get() with defaults to prevent KeyErrors
                    board_number = deal.get("board_number", deal.get("deal_number", "Unknown"))
                    url = deal.get("url", "")
                    group_name = deal.get("group_name", "Unknown")
                    deal_number = deal.get("deal_number", "Unknown")

                    # Only add deals with valid URLs
                    if url:
                        self.board_urls.append({
                            "board_number": board_number,
                            "url": url
                        })

                        # Add to treeview
                        self.deal_tree.insert("", "end",
                                            values=(group_name, deal_number),
                                            iid=len(self.board_urls) - 1)
                        total_deals += 1
                    else:
                        print(f"Skipping deal with empty URL: {deal}")

                except Exception as e:
                    print(f"Error adding deal to list: {e}")
                    continue

            # Update status
            if total_deals > 0:
                self.current_data_label.config(text=f"Folder: {os.path.basename(folder_path)} ({len(file_paths)} files, {total_deals} deals)")
                self.status_var.set(f"Loaded {total_deals} deals from {len(file_paths)} files")
            else:
                self.current_data_label.config(text=f"Folder: {os.path.basename(folder_path)} (No valid deals found)")
                self.status_var.set("No valid deals found in selected files")

        except Exception as e:
            error_msg = f"An error occurred while loading the folder: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)



    def extract_board_entries(self, file_path):
        """Extract board entries from a LIN file"""
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Regular expression to match board entries
        pattern = r'(qx\|o\d+\|.*?(?=qx\|o\d+\||$))'
        board_entries = re.findall(pattern, content, re.DOTALL)
        
        return board_entries

    def get_selected_url(self):
        """Get URL of the selected deal"""
        selection = self.deal_tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Please select a deal from the list.")
            return None
        
        try:
            selected_idx = int(selection[0])
            if 0 <= selected_idx < len(self.board_urls):
                return self.board_urls[selected_idx]["url"]
            else:
                messagebox.showinfo("Information", "Invalid deal selection. Please try again.")
                return None
        except (ValueError, IndexError):
            messagebox.showinfo("Information", "Please select a valid deal from the list.")
            return None

    def on_deal_double_click(self, event):
        """Handle double-click on a deal"""
        self.open_in_browser()

    def open_in_browser(self):
        """Open the selected deal in browser"""
        url = self.get_selected_url()
        if url:
            webbrowser.open(url)
            self.status_var.set("Opened deal in browser")

    def copy_to_clipboard(self):
        """Copy the selected deal URL to clipboard"""
        url = self.get_selected_url()
        if url:
            pyperclip.copy(url)
            self.status_var.set("URL copied to clipboard")

    def save_urls(self):
        """Save all URLs"""
        if not self.board_urls:
            messagebox.showinfo("Information", "No deals to save.")
            return
        
        folder_name = os.path.basename(self.current_folder) if self.current_folder else "mixed_deals"
        save_path = os.path.join(self.saved_urls_dir, f"{folder_name}.json")
        
        if os.path.exists(save_path):
            if not messagebox.askyesno("Confirm Save", f"File {folder_name}.json already exists. Overwrite?"):
                return
        
        self.save_urls_to_file(save_path, folder_name)

    def save_urls_as(self):
        """Save URLs with a custom filename"""
        if not self.board_urls:
            messagebox.showinfo("Information", "No deals to save.")
            return
        
        initial_file = os.path.basename(self.current_folder) if self.current_folder else "mixed_deals"
        
        file_path = filedialog.asksaveasfilename(
            title="Save URLs",
            initialdir=self.saved_urls_dir,
            initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            group_name = os.path.splitext(os.path.basename(file_path))[0]
            self.save_urls_to_file(file_path, group_name)

    def save_urls_to_file(self, file_path, group_name):
        """Save URLs to the specified file"""
        try:
            with open(file_path, 'w') as f:
                data = {
                    "group_name": group_name,
                    "deal_count": len(self.board_urls),
                    "deals": self.board_urls
                }
                json.dump(data, f, indent=2)
            
            filename = os.path.basename(file_path)
            self.status_var.set(f"Saved {len(self.board_urls)} URLs to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save URLs: {str(e)}")

    def load_saved_urls(self):
        """Load previously saved URLs"""
        file_path = filedialog.askopenfilename(
            title="Load Saved URLs",
            initialdir=self.saved_urls_dir,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Clear current data
            self.board_urls = []
            for item in self.deal_tree.get_children():
                self.deal_tree.delete(item)
            
            # Load the deals
            if "deals" in data and isinstance(data["deals"], list):
                self.board_urls = data["deals"]
                group_name = data.get("group_name", "Loaded Data")
                
                # Populate the deal tree
                for i, deal in enumerate(self.board_urls):
                    deal_num = deal.get("board_number", f"{i+1}")
                    self.deal_tree.insert("", "end", values=(group_name, deal_num), iid=i)
                
                self.status_var.set(f"Loaded {len(self.board_urls)} deals from {os.path.basename(file_path)}")
            else:
                raise ValueError("Invalid data format in the file")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load URLs: {str(e)}")


# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = LinToBboConverter(root)
    root.mainloop()
