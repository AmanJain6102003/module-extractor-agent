from bs4 import BeautifulSoup, NavigableString, Tag
from typing import List, Dict
import re

def _text(node):
    return ' '.join(node.stripped_strings)

def extract_sections_from_html(html: str, source_url: str = '') -> List[Dict]:
    """Extract headings and their associated content from HTML.

    Returns list of dicts: {heading, level, content, url}
    """
    soup = BeautifulSoup(html, 'html.parser')

    # remove likely noise
    for sel in ['header', 'footer', 'nav', 'script', 'style', 'aside', 'form']:
        for el in soup.select(sel):
            el.decompose()

    headings = soup.find_all(re.compile('^h[1-4]$'))
    sections = []

    for idx, h in enumerate(headings):
        level = int(h.name[1])
        title = _text(h)
        # gather siblings until next heading of same or higher level
        content_parts = []
        for sib in h.next_siblings:
            if isinstance(sib, Tag) and sib.name and re.match('^h[1-4]$', sib.name):
                # stop at next heading of any level
                break
            if isinstance(sib, (Tag, NavigableString)):
                text = _text(sib) if isinstance(sib, Tag) else str(sib).strip()
                if text:
                    content_parts.append(text)

        content = '\n'.join(content_parts).strip()
        if not content:
            # also try paragraphs inside heading parent
            p = h.find_next('p')
            content = _text(p) if p else ''

        sections.append({
            'heading': title,
            'level': level,
            'content': content,
            'url': source_url,
        })

    return sections
