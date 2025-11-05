import os
import logging
import re
from datetime import datetime
from parsers.md_parsers.parser import extract_existing_entries

def archive_removed_entries(file_path, archive_path, new_entries):
    old_entries = extract_existing_entries(file_path)
    new_keys = {(e.get('title', 'No title'), e.get('published', 'Unknown date')) for e in new_entries}
    removed = old_entries - new_keys

    if not removed:
        return

    try:
        if not os.path.exists(archive_path):
            with open(archive_path, "w", encoding="utf-8") as archive:
                archive.write(f"# Archive for {os.path.basename(file_path)}\n\n")

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(archive_path, "a", encoding="utf-8") as archive:
            archive.write(f"\n--- Archived on {datetime.now().isoformat()} ---\n")
            writing = False
            title_pattern = re.compile(r"^### \[(.+?)\]\(.+?\)")  # Updated to match ### headings
            current_entry = []

            for line in lines:
                match = title_pattern.match(line.strip())
                if match:
                    if writing and current_entry:
                        archive.writelines(current_entry)
                        archive.write("\n")
                    title = match.group(1)
                    writing = any(title == r[0] for r in removed)
                    current_entry = [line] if writing else []
                elif writing:
                    current_entry.append(line)
                    if line.strip() == "":
                        archive.writelines(current_entry)
                        archive.write("\n")
                        writing = False
                        current_entry = []

            # Catch any trailing entry
            if writing and current_entry:
                archive.writelines(current_entry)
                archive.write("\n")

    except Exception as e:
        logging.error(f"Archiving failed: {e}")