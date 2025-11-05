import os
import logging
import re
from datetime import datetime
from parsers.md_parsers.parser import extract_existing_entries

def archive_removed_entries(file_path, archive_path, new_entries):
    # Normalize GUIDs from current file and new entries
    old_guids = {g.strip().lower() for g in extract_existing_entries(file_path)}
    new_guids = {e.get('guid', '').strip().lower() for e in new_entries if e.get('guid')}
    removed_guids = old_guids - new_guids

    if not removed_guids:
        return

    try:
        # Create archive file if missing
        if not os.path.exists(archive_path):
            with open(archive_path, "w", encoding="utf-8") as archive:
                archive.write(f"# Archive for {os.path.basename(file_path)}\n\n")

        # Read original file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Append archived entries
        with open(archive_path, "a", encoding="utf-8") as archive:
            archive.write(f"\n--- Archived on {datetime.now().isoformat()} ---\n")
            current_entry = []
            entry_guids = set()

            for line in lines:
                stripped = line.strip()

                # Start of a new entry
                if stripped.startswith("### [") and "](" in stripped:
                    # Archive previous entry if all GUIDs are removed
                    if entry_guids and entry_guids <= removed_guids:
                        archive.writelines(current_entry)
                        archive.write("\n")

                    # Start new entry
                    current_entry = [line]
                    entry_guids = set()

                elif stripped.startswith("- 🆔 `") and stripped.endswith("`"):
                    guid = stripped.split("`")[1].strip()
                    entry_guids.add(guid)
                    current_entry.append(line)

                elif stripped == "":
                    current_entry.append(line)
                    # Archive if all GUIDs are removed
                    if entry_guids and entry_guids <= removed_guids:
                        archive.writelines(current_entry)
                        archive.write("\n")
                    current_entry = []
                    entry_guids = set()

                else:
                    current_entry.append(line)

            # Final entry check
            if entry_guids and entry_guids <= removed_guids and current_entry:
                archive.writelines(current_entry)
                archive.write("\n")

    except Exception as e:
        logging.error(f"Archiving failed: {e}")