import os
import logging
from writers.md_writer import MarkdownWriter
from writers.obsidian_markdown_writer import ObsidianMarkdownWriter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)



class RssNoteRouter:
    def __init__(self, output_dir="vault", mode="standard"):
        self.output_dir = output_dir
        self.mode = mode

        if mode == "standard":
            self.writer = MarkdownWriter(output_dir=output_dir)
        elif mode == "obsidian":
            self.writer = ObsidianMarkdownWriter(output_dir=output_dir)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    def write_subject_note(self, subject, sub_subject, source_title, categorized_entries):
        # Just delegate — no business logic here
        return self.writer.write_subject_note(subject, sub_subject, source_title, categorized_entries)
