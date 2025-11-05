import feedparser
import html

class FeedParser:
    def __init__(self, feed_url, source_title="Unknown Source", max_items=5, filter_tree=None, verbose=False):
        self.feed_url = feed_url
        self.source_title = source_title
        self.max_items = max_items
        self.filter_tree = filter_tree
        self.verbose = verbose

    def match_filter_tree(self, entry, node):
        if not node or (not node.get("keyword") and not node.get("children")):
            return True

        title = entry.get('title', '') or entry.get('title_detail', {}).get('value', '')
        summary = (
            entry.get('summary', '') or
            entry.get('description', '') or
            entry.get('summary_detail', {}).get('value', '')
        )
        if not summary and 'content' in entry and isinstance(entry['content'], list):
            summary = entry['content'][0].get('value', '')

        content = f"{title} {summary}".lower()

        # Evaluate keyword match if present
        keyword_result = True
        if "keyword" in node and node["keyword"]:
            keyword = str(node["keyword"]).lower()
            keyword_result = keyword in content
            if self.verbose and keyword_result:
                print(f"[MATCH] Keyword: {keyword} → {keyword_result}")

        # Evaluate children if present
        children_result = True
        children = node.get("children", [])
        if children:
            logic = node.get("logic", "or").lower()
            child_results = [self.match_filter_tree(entry, child) for child in children]
            if self.verbose:
                print(f"[LOGIC] {logic.upper()} → {child_results}")
            if logic == "and":
                children_result = all(child_results)
            elif logic == "not":
                children_result = not any(child_results)
            else:  # default to "or"
                children_result = any(child_results)

        # Combine keyword and children results
        return keyword_result and children_result

    def parse(self):
        feed = feedparser.parse(self.feed_url)
        if feed.bozo:
            if self.verbose:
                print(f"[ERROR] Failed to parse feed: {feed.bozo_exception}")
            return []

        filtered_entries = []
        seen_guids = set()
        item_count = 0

        for entry in feed.entries:
            if self.verbose:
                print(f"[ENTRY] {entry.get('id')}")

            if isinstance(self.filter_tree, dict) and self.filter_tree:
                # If the tree is wrapped under a named key (e.g., "Passthrough" or "filters"), unwrap it
                if "filters" in self.filter_tree:
                    filter_node = self.filter_tree["filters"]
                else:
                    # Assume single-key wrapper (e.g., {"Passthrough": {"filters": {...}}})
                    _, wrapper = next(iter(self.filter_tree.items()))
                    filter_node = wrapper.get("filters", {})
                if not self.match_filter_tree(entry, filter_node):
                    continue

            title = entry.get('title', '') or entry.get('title_detail', {}).get('value', '')
            link = entry.get('link', '')
            if not link and 'links' in entry and isinstance(entry['links'], list):
                link = entry['links'][0].get('href', '')

            published = (
                entry.get('published') or
                entry.get('updated') or
                entry.get('dc:date') or
                entry.get('pubDate') or
                'Unknown date'
            )

            summary_raw = (
                entry.get('summary', '') or
                entry.get('description', '') or
                entry.get('summary_detail', {}).get('value', '')
            )
            if not summary_raw and 'content' in entry and isinstance(entry['content'], list):
                summary_raw = entry['content'][0].get('value', '')

            summary_clean = html.unescape(summary_raw).strip()
            author = entry.get('author', '') or entry.get('author_detail', {}).get('name', '')
            guid = entry.get('id', '') or entry.get('guid', '') or link

            if guid in seen_guids:
                continue
            seen_guids.add(guid)

            parsed_entry = {
                'title': title,
                'link': link,
                'published': published,
                'summary': summary_clean,
                'author': author,
                'guid': guid,
                'source': self.source_title
            }

            filtered_entries.append(parsed_entry)
            item_count += 1
            if item_count >= self.max_items:
                break

        if self.verbose and item_count < self.max_items:
            print(f"[INFO] Only {item_count} entries found (less than max_items={self.max_items})")

        return filtered_entries