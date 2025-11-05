import os
import logging
from parsers.md_parsers.parser import extract_existing_entries
from archivers.archiver import archive_removed_entries
from writers.md_writer import write_feed_note
from .indexer import update_index

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

def write_subject_note(subject, sub_subject, source_title, categorized_entries, output_dir="vault"):
    sub_folder = os.path.join(output_dir, subject, sub_subject or "General")
    os.makedirs(sub_folder, exist_ok=True)

    safe_title = source_title.replace(" ", "_").replace("/", "_")
    file_path = os.path.join(sub_folder, f"{safe_title}.md")
    archive_path = os.path.join(sub_folder, f"{safe_title}_archive.md")

    existing_keys = extract_existing_entries(file_path)

    filtered_by_category = {}
    for category, entries in categorized_entries.items():
        filtered = [
            e for e in entries
            if (e.get('title', 'No title'), e.get('published', 'Unknown date')) not in existing_keys
        ]
        if filtered:
            filtered_by_category[category] = filtered

    all_entries = [e for entries in categorized_entries.values() for e in entries]
    archive_removed_entries(file_path, archive_path, all_entries)
    write_feed_note(file_path, source_title, subject, sub_subject, filtered_by_category, output_dir)

    sub_index_path = os.path.join(sub_folder, f"{sub_subject or 'General'}.md")
    sub_index_entries = [f"- [{source_title}]({safe_title}.md)\n"]
    update_index(sub_index_path, sub_index_entries, f"# {sub_subject or 'General'} Feeds", [subject, sub_subject])

    subject_index_path = os.path.join(output_dir, subject, f"{subject}.md")
    subject_index_entry = [f"- [{sub_subject or 'General'}]({sub_subject.replace(' ', '_') if sub_subject else 'General'}.md)\n"]
    update_index(subject_index_path, subject_index_entry, f"# {subject} Index", [subject])

    new_total = sum(len(v) for v in filtered_by_category.values())
    logging.info(f"{new_total} new entries for '{subject}/{sub_subject or 'General'}/{source_title}'")