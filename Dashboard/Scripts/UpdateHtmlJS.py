import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import re
from datetime import datetime
import traceback
import sys
import urllib.request
import json
import argparse


class ShowStopper(Exception):
    """Critical error to show immediately on front screen."""

    pass


class MultiFileGroupUpdater:
    def __init__(self):
        self.target_directory = None
        self.target_files = [
            "handlinks.js",
            "handviewer.html",
            "bidding.js",
            "bidding.html",
            "summary.html",
            "summary.js",
            "handviewer.js",
        ]

    def choose_directory(self):
        self.target_directory = filedialog.askdirectory(title="Choose Target Directory")
        return self.target_directory

    def backup_file(self, file_path: Path):
        try:
            backup_dir = Path(self.target_directory) / "Backup"
            if not backup_dir.exists():
                msg = f"Backup directory {backup_dir} does not exist"
                print(f"[ERROR] {msg}")
                raise ShowStopper(msg)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamped_backup = (
                backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            )
            shutil.copy2(file_path, timestamped_backup)

            latest_backup = backup_dir / file_path.name
            shutil.copy2(file_path, latest_backup)

            print(
                f"[BACKUP] {file_path.name} backed up as "
                f"{timestamped_backup.name} and {latest_backup.name}"
            )
            return True

        except ShowStopper:
            raise
        except Exception as e:
            print(f"[BACKUP ERROR] Error backing up {file_path.name}: {e}")
            traceback.print_exc()
            raise ShowStopper(f"Backup error in {file_path.name}: {e}") from e

    def insert_line_in_ordered_cluster(
        self, lines, pattern, group_number, insert_line_template
    ):
        insertions = 0
        i = 0

        while i < len(lines):
            if pattern.match(lines[i].strip()):
                cluster_start = i
                cluster_groups = []

                j = i
                while j < len(lines) and pattern.match(lines[j].strip()):
                    m = pattern.match(lines[j].strip())
                    gnum = int(m.group(1))
                    cluster_groups.append((gnum, j))
                    j += 1

                cluster_end = j
                group_nums = [g for g, idx in cluster_groups]

                if group_number in group_nums:
                    i = cluster_end
                    continue

                pos = 0
                while pos < len(group_nums) and group_nums[pos] < group_number:
                    pos += 1

                if pos == len(group_nums):
                    insert_at = cluster_groups[-1][1] + 1
                else:
                    insert_at = cluster_groups[pos][1]

                if insert_at < len(lines):
                    indent = lines[insert_at][
                        : len(lines[insert_at]) - len(lines[insert_at].lstrip())
                    ]
                else:
                    last_idx = cluster_groups[-1][1]
                    indent = lines[last_idx][
                        : len(lines[last_idx]) - len(lines[last_idx].lstrip())
                    ]

                new_line = (
                    indent + insert_line_template.format(group_num=group_number) + "\n"
                )
                lines.insert(insert_at, new_line)
                insertions += 1

                i = cluster_end + 1
            else:
                i += 1

        return insertions

    def process_handviewer_html_group_select(self, group_number):
        """
        Ensure the <select id="group-select"> has an <option> for this group.
        - If option already exists, do nothing.
        - If its 'pair' (N-1 or N+1) exists, reuse that description.
        - Otherwise, prompt the user for a base description.
        The option text is: "<Base description> - Part 1" for odd, "Part 2" for even.
        """
        filename = "handviewer.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the <select id="group-select"> block
        select_start = None
        select_end = None
        for i, line in enumerate(lines):
            if 'id="group-select"' in line:
                select_start = i
                break

        if select_start is None:
            print(f'[ERROR] {filename}: <select id="group-select"> not found')
            return False

        # Find closing </select> from select_start
        for j in range(select_start + 1, len(lines)):
            if "</select>" in lines[j]:
                select_end = j
                break

        if select_end is None:
            print(f"[ERROR] {filename}: closing </select> for group-select not found")
            return False

        # Work only within the select block
        option_lines = lines[select_start : select_end + 1]

        # Regex for option lines: <option value="N">Some Text</option>
        option_pattern = re.compile(r'<option value="(\d+)">(.*?)</option>')

        existing_groups = {}
        for idx, line in enumerate(option_lines):
            m = option_pattern.search(line)
            if m:
                gnum = int(m.group(1))
                text = m.group(2).strip()
                # store index relative to whole file
                global_index = select_start + idx
                existing_groups[gnum] = (global_index, text)

        # If this group already exists, do nothing
        if group_number in existing_groups:
            print(
                f"[SKIP] {filename}: group {group_number} already present in <select>"
            )
            return False

        # Determine pair group
        if group_number % 2 == 0:
            pair_group = group_number - 1
            this_part_suffix = "Part 2"
            pair_part_suffix = "Part 1"
        else:
            pair_group = group_number + 1
            this_part_suffix = "Part 1"
            pair_part_suffix = "Part 2"

        base_description = None

        # Try to get base description from pair, if present
        if pair_group in existing_groups:
            _, pair_text = existing_groups[pair_group]

            # If pair text ends with " - Part 1" or " - Part 2", strip that to get base
            suffixes = [" - Part 1", " - Part 2"]
            base_description = pair_text
            for suf in suffixes:
                if base_description.endswith(suf):
                    base_description = base_description[: -len(suf)]
                    break

            print(
                f"[INFO] {filename}: Using base description from group {pair_group}: '{base_description}'"
            )
        else:
            # Prompt user for base description
            from tkinter import simpledialog

            base_description = simpledialog.askstring(
                "Group Description",
                f"Enter description for group {group_number} (e.g. 'Squeeze Plays'): ",
            )
            if not base_description:
                print(
                    f"[CANCEL] No description entered for group {group_number}, skipping."
                )
                return False

        # Build final option text
        option_text = f"{base_description} - {this_part_suffix}"

        # Determine insertion position (keep numeric order among options)
        all_group_nums_sorted = (
            sorted(existing_groups.keys() + [group_number])
            if hasattr(existing_groups.keys(), "__iter__")
            else sorted(list(existing_groups.keys()) + [group_number])
        )

        # Find where this new group goes in the sorted list
        insert_pos_in_sorted = all_group_nums_sorted.index(group_number)

        # We want to insert in the actual lines near the correct numeric neighbor
        # Strategy: find the neighbor group in existing_groups nearest above, else below
        neighbor_index = None
        # Try next higher group
        higher_groups = [
            g
            for g in all_group_nums_sorted
            if g > group_number and g in existing_groups
        ]
        if higher_groups:
            neighbor_group = min(higher_groups)
            neighbor_index = existing_groups[neighbor_group][0]
        else:
            # fallback: previous lower group
            lower_groups = [
                g
                for g in all_group_nums_sorted
                if g < group_number and g in existing_groups
            ]
            if lower_groups:
                neighbor_group = max(lower_groups)
                neighbor_index = existing_groups[neighbor_group][0] + 1

        if neighbor_index is None:
            # No other numeric options, insert just before </select>
            neighbor_index = select_end

        # Determine indentation from neighbor_index line
        if neighbor_index < len(lines):
            base_line = lines[neighbor_index]
        else:
            base_line = lines[select_end]

        indent = base_line[: len(base_line) - len(base_line.lstrip())]
        new_line = f'{indent}<option value="{group_number}">{option_text}</option>\n'

        # Insert and backup
        lines.insert(neighbor_index, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(
            f"[SUCCESS] {filename}: Inserted option for group {group_number}: {option_text}"
        )
        return True

    def process_file_with_cluster(
        self, filename, pattern, insert_line_template, group_number
    ):
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = insert_line_template.format(group_num=group_number)
        if any(line.strip() == target_line for line in lines):
            print(f"[SKIP] {filename}: Line for group {group_number} already present")
            return False

        insertions = self.insert_line_in_ordered_cluster(
            lines, pattern, group_number, insert_line_template
        )

        if insertions == 0:
            print(f"[ERROR] {filename}: No matching cluster found or no insertion made")
            return False

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted line for group {group_number}")
        return True

    # ---------- JS FILES ----------

    def process_handlinks_js(self, group_number):
        pattern = re.compile(
            r"if \(typeof group(\d+)Data !== 'undefined'\) groupData\['\1'\] = group\1Data;"
        )
        insert_line_template = (
            "if (typeof group{group_num}Data !== 'undefined') "
            "groupData['{group_num}'] = group{group_num}Data;"
        )
        return self.process_file_with_cluster(
            "handlinks.js", pattern, insert_line_template, group_number
        )

    def process_bidding_js(self, group_number):
        pattern = re.compile(
            r"if \(typeof group(\d+)Data !== 'undefined'\) groupData\['\1'\] = group\1Data;"
        )
        insert_line_template = (
            "if (typeof group{group_num}Data !== 'undefined') "
            "groupData['{group_num}'] = group{group_num}Data;"
        )
        return self.process_file_with_cluster(
            "bidding.js", pattern, insert_line_template, group_number
        )

    def process_summary_js(self, group_number):
        pattern = re.compile(
            r"if \(typeof group(\d+)Data !== 'undefined'\) groupData\['\1'\] = group\1Data;"
        )
        insert_line_template = (
            "if (typeof group{group_num}Data !== 'undefined') "
            "groupData['{group_num}'] = group{group_num}Data;"
        )
        return self.process_file_with_cluster(
            "summary.js", pattern, insert_line_template, group_number
        )

    def _get_group_display_name(self, group_number, existing_groups_for_select):
        if group_number % 2 == 0:
            pair_group = group_number - 1
            this_part_suffix = "Part 2"
        else:
            pair_group = group_number + 1
            this_part_suffix = "Part 1"

        base_description = None

        # FIX: Check if this group itself is already in the select (just inserted)
        if group_number in existing_groups_for_select:
            own_text = existing_groups_for_select[group_number]
            base_description = own_text
            for suf in (" - Part 1", " - Part 2"):
                if base_description.endswith(suf):
                    base_description = base_description[: -len(suf)]
                    break

        # Otherwise try the pair group
        elif pair_group in existing_groups_for_select:
            pair_text = existing_groups_for_select[pair_group]
            base_description = pair_text
            for suf in (" - Part 1", " - Part 2"):
                if base_description.endswith(suf):
                    base_description = base_description[: -len(suf)]
                    break
        else:
            from tkinter import simpledialog

            base_description = simpledialog.askstring(
                "Group Description",
                f"Enter description for group {group_number} (e.g. 'Squeeze Plays'): ",
            )
            if not base_description:
                print(
                    f"[CANCEL] No description entered for group {group_number}, skipping."
                )
                return None

        return f"{base_description} - {this_part_suffix}"

    def process_handlinks_html_group_config(self, group_number):
        """
        Ensure handlinks.html has a line for this group in the groupConfig object, e.g.:
            '37': { name: 'End Plays - Part 1', dealStart: 1, dealEnd: 32 },
        or for even:
            '38': { name: 'End Plays - Part 2', dealStart: 33, dealEnd: 64 },
        It skips if an entry for this group already exists.
        """
        filename = "handlinks.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Locate groupConfig block
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if "const groupConfig = {" in line:
                start_idx = i
                break

        if start_idx is None:
            print(f"[ERROR] {filename}: const groupConfig = {{ not found")
            return False

        for j in range(start_idx + 1, len(lines)):
            if "};" in lines[j]:
                end_idx = j
                break

        if end_idx is None:
            print(f"[ERROR] {filename}: closing '}};' for groupConfig not found")

            return False

        # Collect existing config entries
        entry_pattern = re.compile(r"'(\d+)'\s*:\s*\{.*?\},\s*$")
        existing_entries = {}  # group_num -> (line_index, full_line)
        for idx in range(start_idx + 1, end_idx):
            line = lines[idx]
            m = entry_pattern.search(line.strip())
            if m:
                gnum = int(m.group(1))
                existing_entries[gnum] = (idx, line)

        # Skip if this group already has an entry
        if group_number in existing_entries:
            print(
                f"[SKIP] {filename}: groupConfig already has entry for group {group_number}"
            )
            return False

        # Build a map of existing names used in the <select> (for reuse)
        select_groups = {}
        select_start = None
        select_end = None
        for i, line in enumerate(lines):
            if 'id="group-select"' in line:
                select_start = i
                break
        if select_start is not None:
            for j in range(select_start + 1, len(lines)):
                if "</select>" in lines[j]:
                    select_end = j
                    break

        option_pattern = re.compile(r'<option value="(\d+)">(.*?)</option>')
        if select_start is not None and select_end is not None:
            for idx in range(select_start, select_end + 1):
                m = option_pattern.search(lines[idx])
                if m:
                    gnum = int(m.group(1))
                    text = m.group(2).strip()
                    select_groups[gnum] = text

        # Determine display name (e.g. "End Plays - Part 1")
        display_name = self._get_group_display_name(group_number, select_groups)
        if not display_name:
            # User cancelled
            return False

        # Determine dealStart/dealEnd based on Part
        if group_number % 2 == 0:
            deal_start = 33
            deal_end = 64
        else:
            deal_start = 1
            deal_end = 32

        # Prepare new config line
        # Use indentation similar to existing entries if any, else from start line
        if existing_entries:
            any_idx = next(iter(existing_entries.values()))[0]
            base_line = lines[any_idx]
        else:
            base_line = lines[start_idx + 1]

        indent = base_line[: len(base_line) - len(base_line.lstrip())]
        new_line = (
            f"{indent}'{group_number}': "
            f"{{ name: '{display_name}', dealStart: {deal_start}, dealEnd: {deal_end} }},\n"
        )

        # Decide where to insert (keep numeric order by key)
        all_group_nums_sorted = sorted(list(existing_entries.keys()) + [group_number])

        insert_index_in_sorted = all_group_nums_sorted.index(group_number)

        # Find the neighbor in the actual block
        if insert_index_in_sorted < len(all_group_nums_sorted) - 1:
            # Insert before the next higher group if it exists
            higher_group = all_group_nums_sorted[insert_index_in_sorted + 1]
            if higher_group in existing_entries:
                insert_at = existing_entries[higher_group][0]
            else:
                insert_at = end_idx
        else:
            # No higher group: insert before the closing "};"
            insert_at = end_idx

        # Insert the new line
        lines.insert(insert_at, new_line)

        # Backup and write back
        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(
            f"[SUCCESS] {filename}: Inserted groupConfig entry for group {group_number}"
        )
        return True

    def process_handviewer_js(self, group_number):
        pattern = re.compile(
            r"if \(typeof group(\d+)Data !== 'undefined'\) groupData\['\1'\] = group\1Data;"
        )
        insert_line_template = (
            "if (typeof group{group_num}Data !== 'undefined') "
            "groupData['{group_num}'] = group{group_num}Data;"
        )
        return self.process_file_with_cluster(
            "handviewer.js", pattern, insert_line_template, group_number
        )

    # ---------- COPY groupN.js & dealsN.js ----------

    def copy_group_and_deals_js(self, group_number):
        """
        Copy groupN.js and dealsN.js from the Sheets directory located one level above
        the target directory, into the target directory.
        """
        try:
            target_path = Path(self.target_directory)
            project_root = target_path.parent
            sheets_folder = project_root / "Sheets"

            group_folder = f"Group{group_number}"

            src_group_js = (
                sheets_folder / group_folder / "lin" / f"group{group_number}.js"
            )
            src_deals_js = (
                sheets_folder
                / group_folder
                / "Booklet"
                / "Deals"
                / f"deals{group_number}.js"
            )

            if not src_group_js.exists():
                raise ShowStopper(f"Required group JS file not found: {src_group_js}")

            if not src_deals_js.exists():
                raise ShowStopper(f"Required deals JS file not found: {src_deals_js}")

            dst_group_js = target_path / f"group{group_number}.js"
            dst_deals_js = target_path / f"deals{group_number}.js"

            shutil.copy2(src_group_js, dst_group_js)
            print(f"[COPY] {src_group_js} -> {dst_group_js}")

            shutil.copy2(src_deals_js, dst_deals_js)
            print(f"[COPY] {src_deals_js} -> {dst_deals_js}")

        except ShowStopper:
            raise
        except Exception as e:
            traceback.print_exc()
            raise ShowStopper(f"Error copying group/deals JS files: {e}")

    # ---------- HTML: handlinks.html ----------

    def process_handlinks_html_group_select(self, group_number):
        """
        Ensure the <select id="group-select"> has an <option> for this group in handlinks.html.
        - If option already exists, do nothing.
        - If its 'pair' (N-1 or N+1) exists, reuse that description.
        - Otherwise, prompt the user for a base description.
        The option text is: "<Base description> - Part 1" for odd, "Part 2" for even.
        """
        filename = "handlinks.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the <select id="group-select"> block
        select_start = None
        select_end = None
        for i, line in enumerate(lines):
            if 'id="group-select"' in line:
                select_start = i
                break

        if select_start is None:
            print(f'[ERROR] {filename}: <select id="group-select"> not found')
            return False

        # Find closing </select> from select_start
        for j in range(select_start + 1, len(lines)):
            if "</select>" in lines[j]:
                select_end = j
                break

        if select_end is None:
            print(f"[ERROR] {filename}: closing </select> for group-select not found")
            return False

        # Work only within the select block
        option_lines = lines[select_start : select_end + 1]

        # Regex for option lines: <option value="N">Some Text</option>
        option_pattern = re.compile(r'<option value="(\d+)">(.*?)</option>')

        existing_groups = {}
        for idx, line in enumerate(option_lines):
            m = option_pattern.search(line)
            if m:
                gnum = int(m.group(1))
                text = m.group(2).strip()
                # store index relative to whole file
                global_index = select_start + idx
                existing_groups[gnum] = (global_index, text)

        # If this group already exists, do nothing
        if group_number in existing_groups:
            print(
                f"[SKIP] {filename}: group {group_number} already present in <select>"
            )
            return False

        # Determine pair group
        if group_number % 2 == 0:
            pair_group = group_number - 1
            this_part_suffix = "Part 2"
            pair_part_suffix = "Part 1"
        else:
            pair_group = group_number + 1
            this_part_suffix = "Part 1"
            pair_part_suffix = "Part 2"

        base_description = None

        # Try to get base description from pair, if present
        if pair_group in existing_groups:
            _, pair_text = existing_groups[pair_group]

            # If pair text ends with " - Part 1" or " - Part 2", strip that to get base
            suffixes = [" - Part 1", " - Part 2"]
            base_description = pair_text
            for suf in suffixes:
                if base_description.endswith(suf):
                    base_description = base_description[: -len(suf)]
                    break

            print(
                f"[INFO] {filename}: Using base description from group {pair_group}: '{base_description}'"
            )
        else:
            # Prompt user for base description
            from tkinter import simpledialog

            base_description = simpledialog.askstring(
                "Group Description",
                f"Enter description for group {group_number} (e.g. 'Squeeze Plays'): ",
            )
            if not base_description:
                print(
                    f"[CANCEL] No description entered for group {group_number}, skipping."
                )
                return False

        # Build final option text
        option_text = f"{base_description} - {this_part_suffix}"

        # Determine insertion position (keep numeric order among options)
        all_group_nums_sorted = sorted(list(existing_groups.keys()) + [group_number])

        # Find where this new group goes in the sorted list
        insert_pos_in_sorted = all_group_nums_sorted.index(group_number)

        # We want to insert in the actual lines near the correct numeric neighbor
        # Strategy: find the neighbor group in existing_groups nearest above, else below
        neighbor_index = None
        # Try next higher group
        higher_groups = [
            g
            for g in all_group_nums_sorted
            if g > group_number and g in existing_groups
        ]
        if higher_groups:
            neighbor_group = min(higher_groups)
            neighbor_index = existing_groups[neighbor_group][0]
        else:
            # fallback: previous lower group
            lower_groups = [
                g
                for g in all_group_nums_sorted
                if g < group_number and g in existing_groups
            ]
            if lower_groups:
                neighbor_group = max(lower_groups)
                neighbor_index = existing_groups[neighbor_group][0] + 1

        if neighbor_index is None:
            # No other numeric options, insert just before </select>
            neighbor_index = select_end

        # Determine indentation from neighbor_index line
        if neighbor_index < len(lines):
            base_line = lines[neighbor_index]
        else:
            base_line = lines[select_end]

        indent = base_line[: len(base_line) - len(base_line.lstrip())]
        new_line = f'{indent}<option value="{group_number}">{option_text}</option>\n'

        # Insert and backup
        lines.insert(neighbor_index, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(
            f"[SUCCESS] {filename}: Inserted option for group {group_number}: {option_text}"
        )
        return True

    def process_handlinks_html_group_script(self, group_number):
        """
        Ensure <script src="groupN.js"></script> exists in handlinks.html
        in the correct numeric position among other group*.js script tags.
        """
        filename = "handlinks.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = f'<script src="group{group_number}.js"></script>'

        if any(line.strip() == target_line for line in lines):
            print(
                f"[SKIP] {filename}: group script for group {group_number} already present"
            )
            return False

        pattern = re.compile(r'<script src="group(\d+)\.js"></script>')

        cluster_groups = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                gnum = int(m.group(1))
                cluster_groups.append((gnum, idx))

        if not cluster_groups:
            print(f"[ERROR] {filename}: No existing group*.js script cluster found")
            return False

        group_nums = [g for g, _ in cluster_groups]
        if group_number in group_nums:
            print(
                f"[SKIP] {filename}: group script for group {group_number} already in cluster"
            )
            return False

        pos = 0
        while pos < len(group_nums) and group_nums[pos] < group_number:
            pos += 1

        if pos == len(cluster_groups):
            insert_at = cluster_groups[-1][1] + 1
        else:
            insert_at = cluster_groups[pos][1]

        if insert_at < len(lines):
            indent = lines[insert_at][
                : len(lines[insert_at]) - len(lines[insert_at].lstrip())
            ]
        else:
            last_idx = cluster_groups[-1][1]
            indent = lines[last_idx][
                : len(lines[last_idx]) - len(lines[last_idx].lstrip())
            ]

        new_line = indent + target_line + "\n"
        lines.insert(insert_at, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted group script for group {group_number}")
        return True

    def process_handlinks_html_groupdata_line(self, group_number):
        """
        Ensure
            if (typeof groupNData !== 'undefined') groupData['N'] = groupNData;
        exists in handlinks.html in correct numeric position among similar lines.
        """
        filename = "handlinks.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = (
            f"if (typeof group{group_number}Data !== 'undefined') "
            f"groupData['{group_number}'] = group{group_number}Data;"
        )

        if any(line.strip() == target_line for line in lines):
            print(
                f"[SKIP] {filename}: groupData line for group {group_number} already present"
            )
            return False

        pattern = re.compile(
            r"if \(typeof group(\d+)Data !== 'undefined'\) groupData\['\1'\] = group\1Data;"
        )

        cluster_groups = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                gnum = int(m.group(1))
                cluster_groups.append((gnum, idx))

        if not cluster_groups:
            print(f"[ERROR] {filename}: No existing groupData cluster found")
            return False

        group_nums = [g for g, _ in cluster_groups]
        if group_number in group_nums:
            print(
                f"[SKIP] {filename}: groupData line for group {group_number} already in cluster"
            )
            return False

        pos = 0
        while pos < len(group_nums) and group_nums[pos] < group_number:
            pos += 1

        if pos == len(cluster_groups):
            insert_at = cluster_groups[-1][1] + 1
        else:
            insert_at = cluster_groups[pos][1]

        if insert_at < len(lines):
            indent = lines[insert_at][
                : len(lines[insert_at]) - len(lines[insert_at].lstrip())
            ]
        else:
            last_idx = cluster_groups[-1][1]
            indent = lines[last_idx][
                : len(lines[last_idx]) - len(lines[last_idx].lstrip())
            ]

        new_line = indent + target_line + "\n"
        lines.insert(insert_at, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted groupData line for group {group_number}")
        return True

    def process_handviewer_html_group_script(self, group_number):
        """
        Ensure <script src="groupN.js"></script> exists in handviewer.html
        in the correct numeric position among other group*.js script tags.
        """
        filename = "handviewer.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = f'<script src="group{group_number}.js"></script>'

        # Skip if exact line already exists
        if any(line.strip() == target_line for line in lines):
            print(
                f"[SKIP] {filename}: group script for group {group_number} already present"
            )
            return False

        # Match existing group script tags
        pattern = re.compile(r'<script src="group(\d+)\.js"></script>')

        cluster_groups = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                gnum = int(m.group(1))
                cluster_groups.append((gnum, idx))

        if not cluster_groups:
            print(f"[ERROR] {filename}: No existing group*.js script cluster found")
            return False

        group_nums = [g for g, _ in cluster_groups]
        if group_number in group_nums:
            print(
                f"[SKIP] {filename}: group script for group {group_number} already in cluster"
            )
            return False

        # Find numeric insertion position
        pos = 0
        while pos < len(group_nums) and group_nums[pos] < group_number:
            pos += 1

        if pos == len(cluster_groups):
            insert_at = cluster_groups[-1][1] + 1
        else:
            insert_at = cluster_groups[pos][1]

        # Preserve indentation
        if insert_at < len(lines):
            indent = lines[insert_at][
                : len(lines[insert_at]) - len(lines[insert_at].lstrip())
            ]
        else:
            last_idx = cluster_groups[-1][1]
            indent = lines[last_idx][
                : len(lines[last_idx]) - len(lines[last_idx].lstrip())
            ]

        new_line = indent + target_line + "\n"
        lines.insert(insert_at, new_line)

        # Backup and write
        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted group script for group {group_number}")
        return True

    def process_handlinks_html_group_select(self, group_number):
        """
        Ensure the <select id="group-select"> has an <option> for this group in handlinks.html.
        - If option already exists, do nothing.
        - If its 'pair' (N-1 or N+1) exists, reuse that description.
        - Otherwise, prompt the user for a base description.
        The option text is: "<Base description> - Part 1" for odd, "Part 2" for even.
        """
        filename = "handlinks.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find the <select id="group-select"> block
        select_start = None
        select_end = None
        for i, line in enumerate(lines):
            if 'id="group-select"' in line:
                select_start = i
                break

        if select_start is None:
            print(f'[ERROR] {filename}: <select id="group-select"> not found')
            return False

        # Find closing </select> from select_start
        for j in range(select_start + 1, len(lines)):
            if "</select>" in lines[j]:
                select_end = j
                break

        if select_end is None:
            print(f"[ERROR] {filename}: closing </select> for group-select not found")
            return False

        # Work only within the select block
        option_lines = lines[select_start : select_end + 1]

        # Regex for option lines: <option value="N">Some Text</option>
        option_pattern = re.compile(r'<option value="(\d+)">(.*?)</option>')

        existing_groups = {}
        for idx, line in enumerate(option_lines):
            m = option_pattern.search(line)
            if m:
                gnum = int(m.group(1))
                text = m.group(2).strip()
                # store index relative to whole file
                global_index = select_start + idx
                existing_groups[gnum] = (global_index, text)

        # If this group already exists, do nothing
        if group_number in existing_groups:
            print(
                f"[SKIP] {filename}: group {group_number} already present in <select>"
            )
            return False

        # Determine pair group
        if group_number % 2 == 0:
            pair_group = group_number - 1
            this_part_suffix = "Part 2"
            pair_part_suffix = "Part 1"
        else:
            pair_group = group_number + 1
            this_part_suffix = "Part 1"
            pair_part_suffix = "Part 2"

        base_description = None

        # Try to get base description from pair, if present
        if pair_group in existing_groups:
            _, pair_text = existing_groups[pair_group]

            # If pair text ends with " - Part 1" or " - Part 2", strip that to get base
            suffixes = [" - Part 1", " - Part 2"]
            base_description = pair_text
            for suf in suffixes:
                if base_description.endswith(suf):
                    base_description = base_description[: -len(suf)]
                    break

            print(
                f"[INFO] {filename}: Using base description from group {pair_group}: '{base_description}'"
            )
        else:
            # Prompt user for base description
            from tkinter import simpledialog

            base_description = simpledialog.askstring(
                "Group Description",
                f"Enter description for group {group_number} (e.g. 'Squeeze Plays'): ",
            )
            if not base_description:
                print(
                    f"[CANCEL] No description entered for group {group_number}, skipping."
                )
                return False

        # Build final option text
        option_text = f"{base_description} - {this_part_suffix}"

        # Determine insertion position (keep numeric order among options)
        all_group_nums_sorted = sorted(list(existing_groups.keys()) + [group_number])

        # Find where this new group goes in the sorted list
        insert_pos_in_sorted = all_group_nums_sorted.index(group_number)

        # We want to insert in the actual lines near the correct numeric neighbor
        # Strategy: find the neighbor group in existing_groups nearest above, else below
        neighbor_index = None
        # Try next higher group
        higher_groups = [
            g
            for g in all_group_nums_sorted
            if g > group_number and g in existing_groups
        ]
        if higher_groups:
            neighbor_group = min(higher_groups)
            neighbor_index = existing_groups[neighbor_group][0]
        else:
            # fallback: previous lower group
            lower_groups = [
                g
                for g in all_group_nums_sorted
                if g < group_number and g in existing_groups
            ]
            if lower_groups:
                neighbor_group = max(lower_groups)
                neighbor_index = existing_groups[neighbor_group][0] + 1

        if neighbor_index is None:
            # No other numeric options, insert just before </select>
            neighbor_index = select_end

        # Determine indentation from neighbor_index line
        if neighbor_index < len(lines):
            base_line = lines[neighbor_index]
        else:
            base_line = lines[select_end]

        indent = base_line[: len(base_line) - len(base_line.lstrip())]
        new_line = f'{indent}<option value="{group_number}">{option_text}</option>\n'

        # Insert and backup
        lines.insert(neighbor_index, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(
            f"[SUCCESS] {filename}: Inserted option for group {group_number}: {option_text}"
        )
        return True

    def process_handlinks_html_groupdata_line(self, group_number):
        """
        Ensure:
            if (typeof groupNData !== 'undefined') groupData['N'] = groupNData;
        exists in handlinks.html in correct numeric position among similar lines.
        """
        filename = "handlinks.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = (
            f"if (typeof group{group_number}Data !== 'undefined') "
            f"groupData['{group_number}'] = group{group_number}Data;"
        )

        if any(line.strip() == target_line for line in lines):
            print(
                f"[SKIP] {filename}: groupData line for group {group_number} already present"
            )
            return False

        pattern = re.compile(
            r"if \(typeof group(\d+)Data !== 'undefined'\) groupData\['\1'\] = group\1Data;"
        )

        cluster_groups = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                gnum = int(m.group(1))
                cluster_groups.append((gnum, idx))

        if not cluster_groups:
            print(f"[ERROR] {filename}: No existing groupData cluster found")
            return False

        group_nums = [g for g, _ in cluster_groups]
        if group_number in group_nums:
            print(
                f"[SKIP] {filename}: groupData line for group {group_number} already in cluster"
            )
            return False

        pos = 0
        while pos < len(group_nums) and group_nums[pos] < group_number:
            pos += 1

        if pos == len(cluster_groups):
            insert_at = cluster_groups[-1][1] + 1
        else:
            insert_at = cluster_groups[pos][1]

        if insert_at < len(lines):
            indent = lines[insert_at][
                : len(lines[insert_at]) - len(lines[insert_at].lstrip())
            ]
        else:
            last_idx = cluster_groups[-1][1]
            indent = lines[last_idx][
                : len(lines[last_idx]) - len(lines[last_idx].lstrip())
            ]

        new_line = indent + target_line + "\n"
        lines.insert(insert_at, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted groupData line for group {group_number}")
        return True

    # ---------- HTML: summary.html ----------

    def process_summary_html_group_script(self, group_number):
        """
        Ensure <script src="groupN.js" defer></script> exists in summary.html
        in the correct numeric position among other group*.js script tags.
        """
        filename = "summary.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = f'<script src="group{group_number}.js" defer></script>'

        if any(line.strip() == target_line for line in lines):
            print(
                f"[SKIP] {filename}: group script for group {group_number} already present"
            )
            return False

        pattern = re.compile(r'<script src="group(\d+)\.js" defer></script>')

        cluster_groups = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                gnum = int(m.group(1))
                cluster_groups.append((gnum, idx))

        if not cluster_groups:
            print(f"[ERROR] {filename}: No existing group*.js script cluster found")
            return False

        group_nums = [g for g, _ in cluster_groups]
        if group_number in group_nums:
            print(
                f"[SKIP] {filename}: group script for group {group_number} already in cluster"
            )
            return False

        pos = 0
        while pos < len(group_nums) and group_nums[pos] < group_number:
            pos += 1

        if pos == len(cluster_groups):
            insert_at = cluster_groups[-1][1] + 1
        else:
            insert_at = cluster_groups[pos][1]

        if insert_at < len(lines):
            indent = lines[insert_at][
                : len(lines[insert_at]) - len(lines[insert_at].lstrip())
            ]
        else:
            last_idx = cluster_groups[-1][1]
            indent = lines[last_idx][
                : len(lines[last_idx]) - len(lines[last_idx].lstrip())
            ]

        new_line = indent + target_line + "\n"
        lines.insert(insert_at, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted group script for group {group_number}")
        return True

    def process_summary_html_deals_script(self, group_number):
        """
        Ensure <script src="dealsN.js" defer></script> exists in summary.html
        in the correct numeric position among other deals*.js script tags.
        N is the group number.
        """
        filename = "summary.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = f'<script src="deals{group_number}.js" defer></script>'

        if any(line.strip() == target_line for line in lines):
            print(
                f"[SKIP] {filename}: deals script for group {group_number} already present"
            )
            return False

        pattern = re.compile(r'<script src="deals(\d+)\.js" defer></script>')

        cluster_groups = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                gnum = int(m.group(1))
                cluster_groups.append((gnum, idx))

        if not cluster_groups:
            print(f"[ERROR] {filename}: No existing deals*.js script cluster found")
            return False

        group_nums = [g for g, _ in cluster_groups]
        if group_number in group_nums:
            print(
                f"[SKIP] {filename}: deals script for group {group_number} already in cluster"
            )
            return False

        pos = 0
        while pos < len(group_nums) and group_nums[pos] < group_number:
            pos += 1

        if pos == len(cluster_groups):
            insert_at = cluster_groups[-1][1] + 1
        else:
            insert_at = cluster_groups[pos][1]

        if insert_at < len(lines):
            indent = lines[insert_at][
                : len(lines[insert_at]) - len(lines[insert_at].lstrip())
            ]
        else:
            last_idx = cluster_groups[-1][1]
            indent = lines[last_idx][
                : len(lines[last_idx]) - len(lines[last_idx].lstrip())
            ]

        new_line = indent + target_line + "\n"
        lines.insert(insert_at, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted deals script for group {group_number}")
        return True

    # ---------- HTML: bidding.html ----------

    def process_bidding_html_group_script(self, group_number):
        """
        Ensure <script src="groupN.js" defer></script> exists in bidding.html
        in the correct numeric position among other group*.js script tags.
        """
        filename = "bidding.html"
        file_path = Path(self.target_directory) / filename

        if not file_path.exists():
            msg = f"{filename} not found"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        target_line = f'<script src="group{group_number}.js" defer></script>'

        if any(line.strip() == target_line for line in lines):
            print(
                f"[SKIP] {filename}: group script for group {group_number} already present"
            )
            return False

        pattern = re.compile(r'<script src="group(\d+)\.js" defer></script>')

        cluster_groups = []
        for idx, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                gnum = int(m.group(1))
                cluster_groups.append((gnum, idx))

        if not cluster_groups:
            print(f"[ERROR] {filename}: No existing group*.js script cluster found")
            return False

        group_nums = [g for g, _ in cluster_groups]
        if group_number in group_nums:
            print(
                f"[SKIP] {filename}: group script for group {group_number} already in cluster"
            )
            return False

        pos = 0
        while pos < len(group_nums) and group_nums[pos] < group_number:
            pos += 1

        if pos == len(cluster_groups):
            insert_at = cluster_groups[-1][1] + 1
        else:
            insert_at = cluster_groups[pos][1]

        if insert_at < len(lines):
            indent = lines[insert_at][
                : len(lines[insert_at]) - len(lines[insert_at].lstrip())
            ]
        else:
            last_idx = cluster_groups[-1][1]
            indent = lines[last_idx][
                : len(lines[last_idx]) - len(lines[last_idx].lstrip())
            ]

        new_line = indent + target_line + "\n"
        lines.insert(insert_at, new_line)

        if not self.backup_file(file_path):
            msg = f"{filename}: Backup failed"
            print(f"[ERROR] {msg}")
            raise ShowStopper(msg)

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"[SUCCESS] {filename}: Inserted group script for group {group_number}")
        return True

    # ---------- ORCHESTRATION ----------

    def process_all(self, group_number):
        try:
            # JS updates
            self.process_handlinks_js(group_number)
            self.process_bidding_js(group_number)
            self.process_summary_js(group_number)
            self.process_handviewer_js(group_number)

            # Copy group/deals JS
            self.copy_group_and_deals_js(group_number)

            # HTML: summary.html
            self.process_summary_html_group_script(group_number)
            self.process_summary_html_deals_script(group_number)

            # HTML: handlinks.html (scripts, groupData, dropdown)
            self.process_handlinks_html_group_script(group_number)
            self.process_handlinks_html_groupdata_line(group_number)
            self.process_handlinks_html_group_select(group_number)

            # NEW: groupConfig entry in handlinks.html
            self.process_handlinks_html_group_config(group_number)

            # HTML: bidding.html
            self.process_bidding_html_group_script(group_number)

            # HTML: handviewer.html
            self.process_handviewer_html_group_script(group_number)

            print(
                f"[DONE] Completed processing and copying files for group {group_number}"
            )
            messagebox.showinfo(
                "Success",
                f"Processed all files and copied JS/HTML references for group {group_number}",
            )
        except ShowStopper as ss:
            messagebox.showerror("Error", str(ss))
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Unexpected Error", str(e))


# Default FullVersion target directory
DEFAULT_FULLVERSION_DIR = Path(
    r"C:\Users\maxuk\OneDrive\Software\Projects\Handviewer\Autobridge\FullVersion"
)


def fetch_current_group_from_dashboard():
    # Read the current group from the dashboard via /api/current_group.
    # Falls back to 11 if the server is unreachable.
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:5000/api/current_group", timeout=2
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return int(data["group"])
    except Exception:
        return 11


class GroupNumberApp(tk.Tk):
    def __init__(self, updater, initial_group=None):
        super().__init__()
        self.title("Go Live changes")

        self.updater = updater
        self.target_directory = None

        self.group_label = tk.Label(self, text="Enter Group Number:")
        self.group_entry = tk.Entry(self)

        # Pre-fill: use --group arg passed by Flask, else ask the dashboard
        group_num = initial_group or fetch_current_group_from_dashboard()
        self.group_entry.insert(0, str(group_num))
        self.group_entry.focus_set()

        self.dir_btn = tk.Button(
            self, text="Select Target Directory", command=self.select_directory
        )
        self.dir_label = tk.Label(self, text="No directory selected", fg="red")

        self.process_btn = tk.Button(
            self, text="Process Files", command=self.process_files
        )

        self.group_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.group_entry.grid(row=0, column=1, padx=10, pady=10, sticky="we")
        self.dir_btn.grid(row=1, column=0, padx=10, pady=10, sticky="we")
        self.dir_label.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.process_btn.grid(row=2, column=0, columnspan=2, pady=20)

        self.columnconfigure(1, weight=1)

        # Pre-select FullVersion directory if it exists on disk
        if DEFAULT_FULLVERSION_DIR.exists():
            self.target_directory = DEFAULT_FULLVERSION_DIR
            self.updater.target_directory = DEFAULT_FULLVERSION_DIR
            self.dir_label.config(text=str(DEFAULT_FULLVERSION_DIR), fg="green")

    def select_directory(self):
        directory = filedialog.askdirectory(
            title="Choose Target Directory",
            initialdir=str(self.target_directory) if self.target_directory else "/",
        )
        if directory:
            self.target_directory = Path(directory)
            self.dir_label.config(text=str(self.target_directory), fg="green")
            self.updater.target_directory = self.target_directory
        # If user cancels, keep existing selection unchanged

    def process_files(self):
        group_str = self.group_entry.get().strip()
        if not group_str.isdecimal():
            messagebox.showerror(
                "Invalid Input", "Please enter a valid numeric group number."
            )
            self.group_entry.focus_set()
            return

        if not self.target_directory:
            messagebox.showerror(
                "No Target Directory", "Please select a target directory first."
            )
            return

        group_number = int(group_str)
        try:
            self.updater.process_all(group_number)
        except Exception as e:
            messagebox.showerror("Processing Error", f"An error occurred:\n{e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--group", type=int, default=None, help="Group number passed by the dashboard"
    )
    args, _ = parser.parse_known_args()

    updater = MultiFileGroupUpdater()
    app = GroupNumberApp(updater, initial_group=args.group)
    app.mainloop()


if __name__ == "__main__":
    main()
