import os
import logging
from datetime import datetime

def update_index(index_path, entries, header=None, parents=[]):
    try:
        tags = ", ".join(parents)
        yaml_header = f"""---
tags: [{tags}]
created: {datetime.now().isoformat()}
---

"""
        if not os.path.exists(index_path) or os.path.getsize(index_path) == 0:
            with open(index_path, "w", encoding="utf-8") as idx:
                idx.write(yaml_header)
                idx.writelines(entries)
        else:
            with open(index_path, "r+", encoding="utf-8") as idx:
                content = idx.read()
                idx.seek(0, os.SEEK_END)
                for entry in entries:
                    if entry not in content:
                        idx.write(entry)
    except Exception:
        logging.exception(f"Failed to update index {index_path}")