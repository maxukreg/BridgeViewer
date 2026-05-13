import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import re
import json
import threading
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import socket

# Configuration
BASE_HTML_FILE_PATH = r"C:\Users\maxuk\OneDrive\Software\Projects\Handviewer\Autobridge\FullVersion\summary.html"
# The directory from which all files will be served by the HTTP server
# and where BookletTester.py will look for groupXX.js (navigation) files.
SERVING_DIRECTORY = os.path.dirname(BASE_HTML_FILE_PATH)

HTTP_PORT = 8080  # You can change this if needed

current_group_num = None
current_deal_num = None
current_group_deals_data = []  # This stores data from groupXX.js (navigation data)
http_server = None
server_thread = None


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVING_DIRECTORY, **kwargs)

    def do_GET(self):
        print(
            f"HTTP Server: do_GET received request for: {self.path}"
        )  # Log every request
        try:
            if (
                self.path.endswith(".js")
                or self.path.endswith(".html")
                or self.path.endswith(".css")
            ):
                # These headers are sent *before* the response body is determined by super().do_GET()
                # This is generally okay, but if super().do_GET() itself fails and sends an error response,
                # these might conflict or be irrelevant.
                pass  # Let's defer sending these until after we know super().do_GET() won't send its own error

            # Call the parent class's do_GET to handle file serving
            super().do_GET()

            # If super().do_GET() was successful (didn't raise an exception that sent an error response),
            # then we can try to add our cache headers.
            # However, SimpleHTTPRequestHandler.do_GET already calls end_headers().
            # Modifying headers after super().do_GET() is tricky and often not possible
            # as headers might have already been sent.
            # For now, let's focus on whether super().do_GET() itself throws an error for deals12.js

        except ConnectionResetError:
            print(f"HTTP Server: Connection reset by peer for {self.path}")
        except BrokenPipeError:
            print(f"HTTP Server: Broken pipe for {self.path}")
        except Exception as e:
            print(f"--- HTTP SERVER ERROR in do_GET for path: {self.path} ---")
            import traceback

            traceback.print_exc()
            print(f"--- END HTTP SERVER ERROR ---")
            # Try to send a generic error response if one wasn't already sent
            try:
                if (
                    not self.wfile.closed
                ):  # Check if headers might have already been sent
                    self.send_error(500, f"Server error processing {self.path}: {e}")
            except Exception as e2:
                print(f"HTTP Server: Error sending 500 response: {e2}")
        # else:
        # If no exception, and if we wanted to add headers *after* knowing it's a success
        # (this is complex with SimpleHTTPRequestHandler as it manages headers internally)
        # For now, the cache control in the initial if block (if re-enabled) is a simpler approach,
        # though it applies headers even if the file isn't found by super().do_GET().
        # The default SimpleHTTPRequestHandler already sends appropriate Content-Type.

    def log_message(self, format, *args):
        # print(f"HTTP Request Log: {self.path}") # Keep this for seeing requests
        pass  # Suppress default logging to reduce noise


def find_free_port(start_port=8080):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    return None


def start_http_server():
    """Start the local HTTP server in a separate thread"""
    global http_server, server_thread, HTTP_PORT

    if http_server is not None:
        print("HTTP server already running.")
        return True

    try:
        free_port = find_free_port(HTTP_PORT)
        if free_port is None:
            messagebox.showerror(
                "Server Error", "Could not find a free port for HTTP server"
            )
            return False

        HTTP_PORT = free_port

        # Ensure the handler serves from the correct directory
        # The directory is passed to the handler's __init__
        http_server = socketserver.TCPServer(
            ("localhost", HTTP_PORT), CustomHTTPRequestHandler
        )

        server_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
        server_thread.start()

        print(
            f"HTTP server started on http://localhost:{HTTP_PORT}, serving from: {SERVING_DIRECTORY}"
        )
        status_label.config(text=f"HTTP server running on port {HTTP_PORT}")
        return True

    except Exception as e:
        messagebox.showerror("Server Error", f"Failed to start HTTP server: {e}")
        print(f"Server error: {e}")
        return False


def stop_http_server():
    """Stop the HTTP server"""
    global http_server, server_thread

    if http_server is not None:
        print("Attempting to stop HTTP server...")
        http_server.shutdown()
        http_server.server_close()
        http_server = None
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=2)  # Wait for thread to finish
        if server_thread and server_thread.is_alive():
            print("Warning: Server thread did not terminate cleanly.")
        else:
            print("HTTP server stopped.")
        status_label.config(text="HTTP server stopped.")
    else:
        print("HTTP server not running.")


def parse_js_data_file(file_path):
    """Parses the groupXX.js file for navigation data."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # This regex assumes groupXX.js defines an array like: const groupXXData = [ ... ];
        match = re.search(
            r"const\s+group\d+Data\s*=\s*(\[.*?\]);", content, re.DOTALL | re.IGNORECASE
        )
        if match:
            json_array_string = match.group(1)
            # Replace single quotes with double quotes for valid JSON, if necessary
            # Be careful with this if your strings can contain escaped single quotes
            # json_array_string = json_array_string.replace("'", '"') # Only if strictly needed and safe
            data = json.loads(json_array_string)
            return data
        else:
            messagebox.showerror(
                "Parsing Error",
                f"Could not find deal data array (e.g., groupXXData) in {file_path}",
            )
            return None
    except FileNotFoundError:
        messagebox.showerror(
            "File Not Found", f"Navigation data file not found: {file_path}"
        )
        return None
    except json.JSONDecodeError as je:
        messagebox.showerror(
            "JSON Error",
            f"Error decoding JSON from {file_path}.\nCheck file format.\nDetails: {je}",
        )
        return None
    except Exception as e:
        messagebox.showerror(
            "Error", f"An error occurred while parsing {file_path}:\n{e}"
        )
        return None


def find_deal_query(deals_data, group_num_str, deal_num_int):  # group_num is now string
    target_id = f"Group{group_num_str}Deal{deal_num_int}"
    for deal_obj in deals_data:
        if deal_obj.get("id") == target_id:
            return deal_obj.get("query")
    return None


def launch_url_in_browser(url_to_launch):
    print("-" * 60)
    print(f"Launching URL: {url_to_launch}")
    print(f"URL length: {len(url_to_launch)}")
    print("-" * 60)

    try:
        opened = webbrowser.open(
            url_to_launch, new=0
        )  # new=2 tries to open in a new tab

        if opened:
            print("Browser launch successful via HTTP server")
            return True
        else:
            print(
                "webbrowser.open() returned False. The URL might be invalid or browser blocked."
            )
            messagebox.showwarning(
                "Browser Launch",
                "Browser launch may have failed. Please check the console for the URL and try opening it manually.",
            )
            return False

    except Exception as e:
        messagebox.showerror("Browser Error", f"Exception during browser launch:\n{e}")
        print(f"Exception: {e}")
        return False


def launch_deal():
    global current_group_num, current_deal_num, current_group_deals_data
    if not start_http_server():  # Ensure server is running
        return

    group_str = group_entry.get()
    deal_str = deal_entry.get()
    if not group_str.strip().isdigit() or not deal_str.strip().isdigit():
        messagebox.showerror(
            "Invalid Input", "Group and Deal numbers must be integers."
        )
        return

    # group_num is used as a string for consistency with file naming and IDs
    group_num_str = group_str.strip()
    deal_num_int = int(deal_str.strip())

    # All data files (groupXX.js for navigation) are expected in SERVING_DIRECTORY
    group_data_filename = f"group{group_num_str}.js"
    group_data_filepath = os.path.join(SERVING_DIRECTORY, group_data_filename)

    reload_data = False
    if current_group_num != group_num_str:  # Compare with string version
        reload_data = True
    elif not current_group_deals_data:
        reload_data = True

    if reload_data:
        print(
            f"Loading navigation data for Group {group_num_str} from: {group_data_filepath}"
        )
        deals_data = parse_js_data_file(group_data_filepath)
        if not deals_data:
            next_deal_button.config(state=tk.DISABLED)
            current_group_deals_data = []
            current_group_num = None
            current_deal_num = None
            status_label.config(
                text=f"Failed to load navigation data for Group {group_num_str}"
            )
            return
        current_group_deals_data = deals_data
        current_group_num = group_num_str  # Store as string
        print(
            f"Successfully loaded {len(current_group_deals_data)} navigation entries for Group {group_num_str}."
        )

    query_string = find_deal_query(
        current_group_deals_data, group_num_str, deal_num_int
    )
    if query_string:
        # --- MODIFIED: Add mode=tester for summary.html ---
        http_url = (
            f"http://localhost:{HTTP_PORT}/summary.html?{query_string}&mode=tester"
        )
        print(f"Constructed HTTP URL: {http_url}")
        if launch_url_in_browser(http_url):
            current_deal_num = deal_num_int
            next_deal_button.config(state=tk.NORMAL)
            status_label.config(
                text=f"Launched: Group {current_group_num}, Deal {current_deal_num}"
            )
        else:
            status_label.config(
                text=f"Attempted launch for Group {current_group_num}, Deal {current_deal_num}. Check browser."
            )
    else:
        messagebox.showwarning(
            "Deal Not Found",
            f"Deal {deal_num_int} not found in Group {group_num_str} navigation data.",
        )
        next_deal_button.config(state=tk.DISABLED)
        status_label.config(
            text=f"Deal {deal_num_int} not found in Group {group_num_str}"
        )


def launch_next_deal():
    global current_group_num, current_deal_num, current_group_deals_data
    if current_deal_num is None or current_group_num is None:
        messagebox.showinfo("No Deal Loaded", "Please load a deal first.")
        return

    if not start_http_server():  # Ensure server is running
        return

    next_deal_num_int = current_deal_num + 1
    # current_group_num is already a string
    query_string = find_deal_query(
        current_group_deals_data, current_group_num, next_deal_num_int
    )
    if query_string:
        # --- MODIFIED: Add mode=tester for summary.html ---
        http_url = (
            f"http://localhost:{HTTP_PORT}/summary.html?{query_string}&mode=tester"
        )
        if launch_url_in_browser(http_url):
            current_deal_num = next_deal_num_int
            deal_entry.delete(0, tk.END)
            deal_entry.insert(0, str(current_deal_num))
            status_label.config(
                text=f"Launched: Group {current_group_num}, Deal {current_deal_num}"
            )
        else:
            messagebox.showinfo(
                "End of Group",
                f"No more deals found in Group {current_group_num} after Deal {current_deal_num}.",
            )
            next_deal_button.config(state=tk.DISABLED)
            status_label.config(text=f"End of Group {current_group_num}")
    else:
        messagebox.showinfo(
            "End of Group",
            f"No more deals found in Group {current_group_num} after Deal {current_deal_num}.",
        )
        next_deal_button.config(state=tk.DISABLED)
        status_label.config(text=f"End of Group {current_group_num}")


def copy_url_to_clipboard():
    """Helper function to copy the current URL to clipboard"""
    global current_group_num, current_deal_num, current_group_deals_data, HTTP_PORT

    if current_deal_num is None or current_group_num is None:
        messagebox.showinfo("No Deal Loaded", "Please load a deal first.")
        return

    query_string = find_deal_query(
        current_group_deals_data, current_group_num, current_deal_num
    )
    if query_string:
        http_url = f"http://localhost:{HTTP_PORT}/summary.html?{query_string}"
        try:
            root.clipboard_clear()
            root.clipboard_append(http_url)
            messagebox.showinfo("URL Copied", "HTTP URL copied to clipboard.")
        except tk.TclError:
            messagebox.showwarning("Clipboard Error", "Could not access the clipboard.")


def on_closing():
    """Handle application closing"""
    stop_http_server()
    root.destroy()


# --- GUI Setup ---
root = tk.Tk()
root.title("Bridge Deal Tester (HTTP Server)")
root.protocol("WM_DELETE_WINDOW", on_closing)

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Group Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
group_entry = ttk.Entry(frame, width=10)
group_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
group_entry.insert(0, "12")  # Default to Group 12

ttk.Label(frame, text="Deal Number:").grid(row=1, column=0, sticky=tk.W, pady=5)
deal_entry = ttk.Entry(frame, width=10)
deal_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
deal_entry.insert(0, "33")  # Default to Deal 33

load_deal_button = ttk.Button(frame, text="Load Deal", command=launch_deal)
load_deal_button.grid(row=2, column=0, columnspan=2, pady=10)

next_deal_button = ttk.Button(
    frame, text="Next Deal", command=launch_next_deal, state=tk.DISABLED
)
next_deal_button.grid(row=3, column=0, columnspan=2, pady=5)

server_frame = ttk.LabelFrame(
    frame, text="HTTP Server Control"
)  # Changed to LabelFrame
server_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=tk.EW)

start_server_button = ttk.Button(
    server_frame, text="Start Server", command=start_http_server
)
start_server_button.pack(
    side=tk.LEFT, padx=5, pady=5
)  # Use pack for simpler layout within frame

stop_server_button = ttk.Button(
    server_frame, text="Stop Server", command=stop_http_server
)
stop_server_button.pack(side=tk.LEFT, padx=5, pady=5)

copy_url_button = ttk.Button(
    frame, text="Copy URL to Clipboard", command=copy_url_to_clipboard
)
copy_url_button.grid(row=5, column=0, columnspan=2, pady=5)

status_label = ttk.Label(
    frame, text="Enter Group/Deal, then 'Load Deal'. Server starts automatically."
)
status_label.grid(row=6, column=0, columnspan=2, pady=10)

frame.columnconfigure(1, weight=1)

print("Bridge Deal Tester started.")
root.mainloop()
