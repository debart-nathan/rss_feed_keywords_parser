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
        # Treat empty node as passthrough
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

        if "keyword" in node:
            keyword = str(node["keyword"]).lower()
            if self.verbose:
                print(f"[MATCH] Keyword: {keyword} → {keyword in content}")
            return keyword in content

        logic = node.get("logic", "or").lower()
        children = node.get("children", [])
        results = [self.match_filter_tree(entry, child) for child in children]
        if self.verbose:
            print(f"[LOGIC] {logic} → {results}")
        return all(results) if logic == "and" else any(results)

    def parse(self):
        feed = feedparser.parse(self.feed_url)
        filtered_entries = []
        item_count = 0

        for entry in feed.entries:
            if self.verbose:
                print(f"[ENTRY] {entry.get('id')}")

            # Only apply filtering if filter_tree is a non-empty dict
            if isinstance(self.filter_tree, dict) and self.filter_tree:
                filter_result = self.match_filter_tree(entry, self.filter_tree)
                if self.verbose:
                    print(f"[FILTER] Result: {filter_result}")
                if not filter_result:
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

        return filtered_entries