import os
import logging
import re
from datetime import datetime

class ObsidianMarkdownWriter:
    def __init__(self, output_dir="vault"):
        self.output_dir = output_dir

    @staticmethod
    def sanitize_filename(name: str) -> str:
        # Keep spaces and capitalization, only strip invalid filesystem chars
        return "".join(c for c in name if c not in r'\/:*?"<>|').strip()

    @staticmethod
    def format_tag(tag: str) -> str:
        """
        Convert a tag to snake_case and prefix with '#'.
        """
        snake = re.sub(r"\s+", "_", tag.strip().lower())
        return f"#{snake}"

    def write_author_note(self, author_name, subject, source_title, article_title):
        author_folder = os.path.join(self.output_dir, self.sanitize_filename(subject), "_authors")
        os.makedirs(author_folder, exist_ok=True)

        safe_author = self.sanitize_filename(author_name)
        safe_source = self.sanitize_filename(source_title)
        safe_article = self.sanitize_filename(article_title)
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
tags: [#author]
created: {datetime.now().isoformat()}
---\n""")
                    f.write(f"# {author_name}\n\n")
                    f.write(f"- ✍️ Articles from [[{source_title}]]\n")

            with open(author_path, "r+", encoding="utf-8") as f:
                content = f.read()
                backlink = f"- [[{article_title}]]\n"
                if backlink not in content:
                    f.write(backlink)
        except Exception as e:
            logging.error(f"Failed to update author note for {author_name}: {e}")

    def write_entry_note(self, subject, sub_subject, source_title, entry, category):
        folder = os.path.join(
            self.output_dir,
            self.sanitize_filename(subject),
            self.sanitize_filename(sub_subject or "General"),
            self.sanitize_filename(source_title)
        )
        os.makedirs(folder, exist_ok=True)

        title = self.sanitize_filename(entry.get("title", "Untitled"))
        date = entry.get("published", datetime.now().isoformat())
        file_path = os.path.join(folder, f"{title}.md")

        if os.path.exists(file_path):
            return  # skip duplicates

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"title: {entry.get('title', 'Untitled')}\n")
            f.write(f"source: {source_title}\n")
            f.write(f"subject: {subject}\n")
            f.write(f"sub_subject: {sub_subject or 'General'}\n")
            f.write(f"date: {date}\n")
            f.write(f"tags: [{self.format_tag(category)}]\n")

            # Authors referenced in properties
            author_field = entry.get("author", "")
            if author_field:
                authors = [a.strip() for a in author_field.split(",") if a.strip()]
                if authors:
                    f.write("authors: [" + ", ".join(f"[[{a}]]" for a in authors) + "]\n")
            f.write("---\n\n")

            f.write(f"# {entry.get('title', 'Untitled')}\n\n")
            f.write(f"**Source:** {source_title}\n\n")
            f.write(f"{entry.get('summary', '')}\n\n")
            if entry.get("link"):
                f.write(f"[Read more]({entry['link']})\n")

        # Update author notes at subject/_authors
        if author_field:
            for author in [a.strip() for a in author_field.split(",") if a.strip()]:
                self.write_author_note(author, subject, source_title, entry.get("title", "Untitled"))

    def write_feed_notes(self, subject, sub_subject, source_title, categorized_entries):
        new_total = 0
        for category, entries in categorized_entries.items():
            for entry in entries:
                self.write_entry_note(subject, sub_subject, source_title, entry, category)
                new_total += 1
        logging.info(f"{new_total} new Obsidian entries for '{subject}/{sub_subject or 'General'}/{source_title}'")

    def write_subject_note(self, subject, sub_subject, source_title, categorized_entries):
        """
        Full orchestration for Obsidian mode: atomic notes, author notes at subject/_authors.
        """
        self.write_feed_notes(subject, sub_subject, source_title, categorized_entries)