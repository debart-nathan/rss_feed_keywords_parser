from core.yaml_loader import load_feeds
from core.dispatcher import dispatch_parser
from core.rss_note_writer import RssNoteRouter   # import the router class now
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="RSS Feed Parser")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--group", help="Target a specific group from feeds.yml")
    group.add_argument("--all", action="store_true", help="Process all groups in feeds.yml")

    parser.add_argument("--mode", choices=["standard", "obsidian"], default="standard",
                        help="Choose output mode: standard Markdown or Obsidian Markdown")

    parser.add_argument("--base-dir", default="vaultRSS",
                        help="Relative base directory for destination notes (default: vaultRSS)")

    parser.add_argument("-vvv", action="store_true", help="Enable verbose debug output")
    return parser.parse_args()

def flatten_group_feeds(group_name, group_config):
    max_feeds = group_config.get('max_feeds', None)
    subgroups = group_config.get('feeds', {})

    flat = []
    count = 0
    for sub_subject, config in subgroups.items():
        if isinstance(config, list):  # Legacy format
            feeds = config
            categories = {}  # No categories defined
        elif isinstance(config, dict):  # New format
            feeds = config.get('feeds', [])
            categories = config.get('categories', {})
        else:
            continue

        for feed in feeds:
            if max_feeds is not None and count >= max_feeds:
                break
            flat.append((group_name, sub_subject, feed, categories, max_feeds))
            count += 1
    return flat

def main():
    args = parse_args()
    feed_tree = load_feeds("feeds.yml")

    # instantiate the router once with chosen mode
    
    writer = RssNoteRouter(output_dir=args.base_dir, mode=args.mode)


    groups_to_process = []
    if args.all:
        groups_to_process = list(feed_tree.keys())
    elif args.group:
        if args.group not in feed_tree:
            print(f"Group '{args.group}' not found in feeds.yml")
            return
        groups_to_process = [args.group]

    for group_name in groups_to_process:
        group_config = feed_tree[group_name]
        flat_feeds = flatten_group_feeds(group_name, group_config)

        for subject, sub_subject, feed, filter_tree, max_items in flat_feeds:
            source_title = feed.get('title', 'Unknown Source')

            # Passthrough ONLY if no category block was defined (legacy format)
            if filter_tree == {}:
                if args.vvv:
                    print(f"[INFO] Legacy feed detected — enabling passthrough for '{source_title}'")
                filter_tree = {
                    "Passthrough": {
                        "filters": {
                            "logic": "or",
                            "children": []
                        }
                    }
                }
            max_items = max_items if max_items is not None else 5

            categorized_entries = dispatch_parser(
                subject,
                feed,
                sub_subject=sub_subject,
                source_title=source_title,
                max_items=max_items,
                filter_tree=filter_tree,
                verbose=args.vvv
            )

            # delegate to the router
            writer.write_subject_note(
                subject,
                sub_subject,
                source_title,
                categorized_entries
            )

if __name__ == "__main__":
    main()