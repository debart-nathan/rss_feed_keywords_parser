# RSS Reader with Markdown / Obsidian Output

This project is a Python application that parses RSS feeds defined in a YAML configuration file (`feeds.yml`) and writes notes in either **standard Markdown** or **Obsidian‑flavored Markdown**.

## Features

- Flexible feed configuration via `feeds.yml` (supports filters, categories, limits).
- Two output modes:
  - **Standard Markdown**: archive + index structure.
  - **Obsidian Markdown**: atomic notes per entry, tags in frontmatter, `_authors` folder at subject root.
- CLI arguments to select groups, process all feeds, choose mode, and set output directory.

## Requirements

Dependencies are listed in `requirements.txt`.

Install them with:

```bash
pip install -r requirements.txt
```

## Usage

Run the main script:

```bash
python main.py --group <subject> --mode <standard|obsidian> --base-dir <output_dir>
```

### Arguments

- `--group <subject>`: Process a specific group from `feeds.yml`.
- `--all`: Process all groups defined in `feeds.yml`.
- `--mode`: Choose output mode:
  - `standard` → Markdown with archives and indexes.
  - `obsidian` → Obsidian‑style notes with tags and `_authors`.
- `--base-dir`: Relative base directory for destination notes (default: `vaultRSS`).
- `-vvv`: Enable verbose debug output.

### Example

Process all feeds into an Obsidian vault named `MyVault`:

```bash
python main.py --all --mode obsidian --base-dir MyVault
```

Process only the `AI` group in standard Markdown mode:

```bash
python main.py --group AI --mode standard
```

## Project Structure

- `core/` → main logic (router, dispatcher, yaml loader).
- `writers/` → output writers:
  - `md_writer.py` → Standard Markdown writer.
  - `obsidian_markdown_writer.py` → Obsidian Markdown writer.
- `feeds.yml` → feed configuration.

## Notes

- In **Obsidian mode**, each entry is an individual file under `subject/sub_subject/source_title/`.
- Authors are stored in `subject/_authors/` and referenced in note frontmatter.
- Tags are normalized to snake_case and prefixed with `#`.
