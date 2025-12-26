import os
from typing import List, Callable
from crawler.crawler import Crawler
from utils.cleaner import extract_sections_from_html
from agent.reasoner import infer_modules
from models.schema import validate_modules

DEFAULT_MAX_PAGES = 200

def extract_from_urls(urls: List[str], progress_callback: Callable[[float,str],None]=None, max_pages:int=200, max_depth:int=2, max_workers:int=6):
    def _report(p, msg):
        if progress_callback:
            progress_callback(p, msg)

    c = Crawler()
    all_pages = []
    for i, url in enumerate(urls):
        _report(i/len(urls), f"Crawling {url}")
        pages = c.crawl(url, max_pages=max_pages, max_depth=max_depth, max_workers=max_workers, progress_callback=lambda p, msg: _report(0.3 + p*0.4, msg))
        all_pages.extend(pages)

    _report(0.5, "Extracting sections from pages")
    sections = []
    for p in all_pages:
        segs = extract_sections_from_html(p.get('html',''), p.get('url',''))
        sections.extend(segs)

    _report(0.7, "Inferring modules and submodules")
    modules = infer_modules(sections)

    _report(0.95, "Validating output schema")
    validate_modules(modules)

    _report(1.0, "Done")
    return modules

if __name__ == "__main__":
    import sys
    urls = sys.argv[1:]
    if not urls:
        print("Usage: python module_extractor.py <url1> <url2> ...")
    else:
        out = extract_from_urls(urls)
        import json
        print(json.dumps(out, indent=2))
