import os
import html
import logging
import re
import unicodedata
import hashlib
from datetime import datetime
from parsers.md_parsers.parser import extract_existing_entries
from archivers.archiver import archive_removed_entries
from core.indexer import update_index

MAX_FILENAME_LEN = 100  # Safe filename length for Windows

class MarkdownWriter:
    def __init__(self, output_dir="vault"):
        self.output_dir = output_dir

    @staticmethod
    def slugify(text):
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s/]+", "_", text)
        return text.strip("_")

    @staticmethod
    def safe_filename(text):
        slug = MarkdownWriter.slugify(text)
        if len(slug) > MAX_FILENAME_LEN:
            return hashlib.md5(text.encode()).hexdigest()
        return slug

    @staticmethod
    def anchor_slug(text):
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^\w\s-]", "", text)
        return text.strip().replace(" ", "-").lower()

    def write_author_note(self, author_name, subject, source_title, article_title):
        author_folder = os.path.join(self.output_dir, subject, "_authors")
        os.makedirs(author_folder, exist_ok=True)

        safe_author = self.safe_filename(author_name)
        safe_source = self.safe_filename(source_title)
        safe_article = self.safe_filename(article_title)
        author_path = os.path.join(author_folder, f"{safe_author}.md")

        if len(author_path) > 255:
            logging.warning(f"Author path too long: {author_path}")
            return

        try:
            if not os.path.exists(author_path):
                with open(author_path, "w", encoding="utf-8") as f:
                    f.write(f"""---
name: {author_name}
subject: {subject}
tags: [author]
created: {datetime.now().isoformat()}
---\n""")
                    f.write(f"# [{author_name}]({safe_author}.md)\n\n")
                    f.write(f"- ✍️ Articles from [{source_title}]({safe_source}.md)\n")

            with open(author_path, "r+", encoding="utf-8") as f:
                content = f.read()
                backlink = f"- [{article_title}]({safe_article}.md)\n"
                if backlink not in content:
                    f.write(backlink)
        except Exception as e:
            logging.error(f"Failed to update author note for {author_name}: {e}")

    def write_feed_note(self, file_path, source_title, subject, sub_subject, categorized_entries):
        safe_source = self.safe_filename(source_title)
        archive_name = f"{safe_source}_archive"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # YAML frontmatter
                f.write(f"""---
title: {source_title}
subject: {subject}
sub_subject: {sub_subject or ''}
source: RSS
tags: [rss, {subject.lower()}]
created: {datetime.now().isoformat()}
archive: [[{archive_name}]]
---\n""")

                # Title
                f.write(f"# [{source_title}]({safe_source}.md)\n\n")

                # Table of Contents
                f.write("## 📑 Table of Contents\n\n")
                for category, entries in categorized_entries.items():
                    f.write(f"### [{category}](#{self.anchor_slug(category)})\n")
                    for entry in entries:
                        guid = entry.get('guid', '').strip().lower()
                        if guid:
                            f.write(f"- 🆔 `{guid}`\n")
                    f.write("\n")
                f.write("---\n\n")

                # Entries
                for category, entries in categorized_entries.items():
                    f.write(f"## {category}\n\n")
                    for entry in entries:
                        title = entry.get('title', 'No title')
                        safe_title = self.safe_filename(title)
                        link = entry.get('link', '')
                        published = entry.get('published', 'Unknown date')
                        summary = html.unescape(entry.get('summary', '')).strip()
                        author_field = entry.get('author', '')
                        guid = entry.get('guid', '').strip().lower()

                        f.write(f"### [{title}]({safe_title}.md)\n")
                        f.write(f"- 📅 **Published:** {published}\n")
                        f.write(f"- 🔗 [Read more]({link})\n")

                        # Authors
                        if author_field:
                            authors = [a.strip() for a in re.split(r",| and ", author_field) if a.strip()]
                            if authors:
                                f.write("- 👤 **Authors:** " + ", ".join(
                                    f"[{a}]({self.safe_filename(a)}.md)" for a in authors
                                ) + "\n")
                                for author in authors:
                                    self.write_author_note(author, subject, source_title, title)

                        # Summary
                        if summary:
                            escaped_summary = summary.replace("#", "\\#")
                            f.write(f"- 📝 **Summary:** {escaped_summary}\n")

                        # GUID
                        if guid:
                            f.write(f"- 🆔 `{guid}`\n")

                        f.write("\n")
        except Exception as e:
            logging.error(f"Failed to write feed note to {file_path}: {e}")

    def write_subject_note(self, subject, sub_subject, source_title, categorized_entries):
        """
        Full orchestration for standard mode: filtering, archiving, writing, indexing.
        """
        sub_folder = os.path.join(self.output_dir, subject, sub_subject or "General")
        os.makedirs(sub_folder, exist_ok=True)

        safe_title = source_title.replace(" ", "_").replace("/", "_")
        file_path = os.path.join(sub_folder, f"{safe_title}.md")
        archive_path = os.path.join(sub_folder, f"{safe_title}_archive.md")

        existing_guids = {g.strip().lower() for g in extract_existing_entries(file_path)}

        filtered_by_category = {}
        for category, entries in categorized_entries.items():
            filtered = [
                e for e in entries
                if e.get('guid', '').strip().lower() not in existing_guids
            ]
            if filtered:
                filtered_by_category[category] = filtered

        all_entries = [e for entries in categorized_entries.values() for e in entries if e.get('guid')]
        archive_removed_entries(file_path, archive_path, all_entries)

        self.write_feed_note(file_path, source_title, subject, sub_subject, categorized_entries)

        sub_index_path = os.path.join(sub_folder, f"{sub_subject or 'General'}.md")
        sub_index_entries = [f"- [{source_title}]({safe_title}.md)\n"]
        update_index(sub_index_path, sub_index_entries, f"# {sub_subject or 'General'} Feeds", [subject, sub_subject])

        subject_index_path = os.path.join(self.output_dir, subject, f"{subject}.md")
        subject_index_entry = [f"- [{sub_subject or 'General'}]({sub_subject.replace(' ', '_') if sub_subject else 'General'}.md)\n"]
        update_index(subject_index_path, subject_index_entry, f"# {subject} Index", [subject])

        new_total = sum(len(v) for v in filtered_by_category.values())
        logging.info(f"{new_total} new entries for '{subject}/{sub_subject or 'General'}/{source_title}'")