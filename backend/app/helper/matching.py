import re
from datetime import date

STOPWORDS = {}

def split_compound(token: str, other_tokens: list[str]) -> list[str]:
    """
    Split token if it contains other known tokens as substrings
    """
    parts = []
    remaining = token

    for ot in sorted(other_tokens, key=len, reverse=True):
        if ot in remaining and len(ot) >= 3:
            parts.append(ot)
            remaining = remaining.replace(ot, " ")

    leftovers = remaining.split()
    return parts + leftovers

def normalize_name(name: str) -> list[str]:
    if not name:
        return []
    name = name.lower()
    name = re.sub(r"[^a-z\s]", " ", name)
    tokens = name.split()
    return [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]

def approx_match_score(t1: str, t2: str) -> float:
    if t1 == t2:
        return 1.0

    if len(t1) >= 5 and len(t2) >= 5 and t1[:5] == t2[:5]:
        return 0.9

    if t1[:4] == t2[:4]:
        return 0.6

    if abs(len(t1) - len(t2)) <= 1:
        mismatches = sum(c1 != c2 for c1, c2 in zip(t1, t2))
        mismatches += abs(len(t1) - len(t2))
        if mismatches <= 1:
            return 0.7

    return 0.0

def name_similarity(tokens1, tokens2) -> float:
    if not tokens1 or not tokens2:
        return 0.0

    # 🔥 NEW: expand compound tokens
    expanded1 = []
    for t in tokens1:
        expanded1.extend(split_compound(t, tokens2))

    expanded2 = []
    for t in tokens2:
        expanded2.extend(split_compound(t, tokens1))

    matched = 0.0
    used = set()

    for t1 in expanded1:
        best = 0.0
        best_t2 = None

        for t2 in expanded2:
            if t2 in used:
                continue

            s = approx_match_score(t1, t2)
            if s > best:
                best = s
                best_t2 = t2

        if best > 0:
            matched += best
            if best_t2:
                used.add(best_t2)

    return matched / max(len(expanded1), len(expanded2))


def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )