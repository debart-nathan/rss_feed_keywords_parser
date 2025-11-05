import os
import logging

def extract_existing_entries(file_path):
    guids = set()
    if not os.path.exists(file_path):
        return guids

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        logging.error(f"Failed to read {file_path}: {e}")
        return guids

    in_toc = False

    for line in lines:
        stripped = line.strip()

        # Detect start of TOC
        if stripped.startswith("## 📑 Table of Contents"):
            in_toc = True
            continue
        # Detect end of TOC
        if in_toc and stripped == "---":
            in_toc = False
            continue

        # Extract GUIDs only from TOC
        if in_toc and stripped.startswith("- 🆔 `") and stripped.endswith("`"):
            guid = stripped.split("`")[1].strip().lower()
            if guid:
                guids.add(guid)

    return guids