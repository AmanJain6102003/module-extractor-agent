import re
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
try:
    import trafilatura
except Exception:
    trafilatura = None

class Crawler:
    def __init__(self, session=None, timeout=10):
        self.session = session or requests.Session()
        self.timeout = timeout

    def validate_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http","https") and parsed.netloc != ''
        except Exception:
            return False

    def same_domain(self, base, url):
        return urlparse(base).netloc == urlparse(url).netloc

    def fetch(self, url: str):
        try:
            r = self.session.get(url, timeout=self.timeout, headers={"User-Agent":"pulse-module-extractor/1.0"})
            if r.status_code == 200:
                html = r.text
                title = BeautifulSoup(html, "html.parser").title
                title_text = title.text.strip() if title else url
                # Prefer trafilatura if available for robust main-content extraction,
                # otherwise fall back to a simple BeautifulSoup-based extractor.
                if trafilatura:
                    try:
                        text = trafilatura.extract(html) or ''
                    except Exception:
                        text = ''
                else:
                    # fallback: extract visible text while skipping scripts/styles
                    soup = BeautifulSoup(html, 'html.parser')
                    for tag in soup(['script', 'style', 'noscript']):
                        tag.decompose()
                    text = ' '.join(soup.stripped_strings)
                return {"url": url, "html": html, "title": title_text, "text": text}
        except Exception:
            return None

    def crawl(self, start_url: str, max_pages: int = 200, max_depth: int = 3, max_workers: int = 6, progress_callback=None):
        """Breadth-first crawl with parallel fetching per level.

        - max_pages: total pages to fetch across the crawl
        - max_depth: BFS depth from start_url (start_url depth=0)
        - max_workers: parallel fetch workers per level
        - progress_callback: optional callable(progress_float, message)
        """
        if not self.validate_url(start_url):
            raise ValueError(f"Invalid URL: {start_url}")

        from concurrent.futures import ThreadPoolExecutor, as_completed

        visited = set()
        frontier = {start_url}
        results = []
        depth = 0

        total_attempted = 0

        while frontier and len(visited) < max_pages and depth <= max_depth:
            # fetch frontier in parallel
            urls = list(frontier)
            frontier = set()
            if progress_callback:
                progress_callback(min(len(visited)/max_pages, 0.99), f"Fetching depth {depth}, {len(urls)} urls")

            with ThreadPoolExecutor(max_workers=max_workers) as exc:
                future_to_url = {exc.submit(self.fetch, u): u for u in urls if u not in visited}
                for fut in as_completed(future_to_url):
                    url = future_to_url[fut]
                    total_attempted += 1
                    try:
                        fetched = fut.result()
                    except Exception:
                        fetched = None

                    if not fetched:
                        continue

                    visited.add(url)
                    results.append(fetched)

                    # parse links and add same-domain links for next frontier
                    soup = BeautifulSoup(fetched['html'], 'html.parser')
                    for a in soup.find_all('a', href=True):
                        href = a['href'].split('#')[0]
                        if not href:
                            continue
                        joined = urljoin(url, href)
                        parsed = urlparse(joined)
                        if parsed.scheme not in ('http','https'):
                            continue
                        if self.same_domain(start_url, joined) and joined not in visited:
                            frontier.add(joined)

                    if len(visited) >= max_pages:
                        break

            depth += 1

        if progress_callback:
            progress_callback(1.0, f"Crawl finished: {len(results)} pages fetched")

        return results
