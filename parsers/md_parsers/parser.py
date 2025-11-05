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

    toc_section = False

    for line in lines:
        stripped = line.strip()

        # Skip TOC section
        if stripped.startswith("## 📑 Table of Contents"):
            toc_section = True
            continue
        if toc_section and stripped == "---":
            toc_section = False
            continue
        if toc_section:
            continue

        # Extract GUIDs from entry body
        if stripped.startswith("- 🆔 `") and stripped.endswith("`"):
            guid = stripped.split("`")[1].strip()
            if guid:
                guids.add(guid)

    return guids