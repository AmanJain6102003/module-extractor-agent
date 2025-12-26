from typing import List, Dict, Tuple
import re
from collections import defaultdict, Counter

def _tokenize(s: str):
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [t for t in s.split() if len(t) > 2]
    return set(tokens)

def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def cluster_headings(headings: List[str], threshold: float = 0.5):
    clusters: List[List[str]] = []
    tokens_list = [ _tokenize(h) for h in headings ]
    for i, h in enumerate(headings):
        placed = False
        for c in clusters:
            # compare with cluster representative (first)
            if _jaccard(_tokenize(c[0]), tokens_list[i]) >= threshold:
                c.append(h)
                placed = True
                break
        if not placed:
            clusters.append([h])
    return clusters

def infer_modules(sections: List[Dict]) -> List[Dict]:
    # Collect candidate headings (levels 1-2 as modules)
    module_candidates = []
    submodule_map = defaultdict(list)
    contents = defaultdict(list)

    for s in sections:
        h = s.get('heading','').strip()
        if not h:
            continue
        lvl = s.get('level', 3)
        if lvl <= 2:
            module_candidates.append(h)
            contents[h].append(s.get('content',''))
        else:
            # treat as submodule tied to nearest ancestor heading
            submodule_map[h].append(s.get('content',''))

    # cluster module candidates conservatively
    clusters = cluster_headings(module_candidates, threshold=0.5)

    modules_out = []
    for cl in clusters:
        # choose canonical name as most common heading in cluster
        name = Counter(cl).most_common(1)[0][0]
        # gather contents for cluster
        agg_content = []
        for h in cl:
            agg_content.extend(contents.get(h, []))

        # find submodules whose heading tokens overlap with module tokens
        module_tokens = _tokenize(name)
        submods = {}
        for sub_h, cnts in submodule_map.items():
            if _jaccard(module_tokens, _tokenize(sub_h)) >= 0.3:
                # pick conservative description: top sentences from content
                desc = ' '.join([c for c in cnts if c])[:1000].strip()
                if desc:
                    submods[sub_h] = desc

        # module description: select sentences from agg_content that include module tokens
        desc_sentences = []
        for c in agg_content:
            for sent in re.split(r"(?<=[.!?])\\s+", c):
                if any(tok in sent.lower() for tok in module_tokens):
                    desc_sentences.append(sent.strip())
                    if len(desc_sentences) >= 3:
                        break
            if len(desc_sentences) >= 3:
                break

        description = ' '.join(desc_sentences).strip()
        if not description:
            # fallback to first available content snippet
            for c in agg_content:
                if c:
                    description = c.strip()[:1000]
                    break

        modules_out.append({
            'module': name,
            'Description': description or '',
            'Submodules': submods or {},
        })

    return modules_out
