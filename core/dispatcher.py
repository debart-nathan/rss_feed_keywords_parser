import importlib
from core.feed_parser import FeedParser

def dispatch_parser(
    subject: str,
    feed: dict,
    sub_subject: str = None,
    source_title: str = "Unknown Source",
    max_items: int = 5,
    filter_tree: dict = None,
    verbose: bool = False
) -> dict:
    import importlib
    from core.feed_parser import FeedParser

    parser_name = feed.get("parser")
    feed_url = feed.get("url")

    if not feed_url:
        return {}

    def try_parse(module):
        try:
            return module.parse(feed_url, source_title=source_title, max_items=max_items)
        except TypeError:
            return module.parse(feed_url, source_title=source_title)

    if parser_name:
        try:
            if sub_subject:
                module = importlib.import_module(f"parsers.rss_parsers.{subject}.{sub_subject}.{parser_name}")
            else:
                module = importlib.import_module(f"parsers.rss_parsers.{subject}.{parser_name}")
            all_entries = try_parse(module)
        except ModuleNotFoundError:
            all_entries = []
    else:
        try:
            if sub_subject:
                module = importlib.import_module(f"parsers.rss_parsers.{subject}.{sub_subject}.general")
            else:
                module = importlib.import_module(f"parsers.rss_parsers.{subject}.general")
            all_entries = try_parse(module)
        except ModuleNotFoundError:
            parser = FeedParser(feed_url, source_title=source_title, max_items=max_items, verbose=verbose)
            all_entries = parser.parse()

    parser = FeedParser(feed_url, source_title=source_title, max_items=max_items, verbose=verbose)

    if isinstance(filter_tree, dict):
        categorized = {}
        for category_name, category_config in filter_tree.items():
            cat_filter = category_config.get("filters", {})
            matched = [e for e in all_entries if parser.match_filter_tree(e, cat_filter)]
            if matched:
                categorized[category_name] = matched
        return categorized

    return {"General": all_entries}