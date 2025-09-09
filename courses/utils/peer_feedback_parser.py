import re
from typing import Dict

# Robust parser to split a free-text blob into 3 canonical areas:
# highlights, suggestions, final. Recognizes English and Italian headers and
# common synonyms, case-insensitive, with/without ':' or line breaks.

AREA_HEADERS = {
    'highlights': [
        r'highlight(s)?', r'strength(s)?', r'punto di forza', r'punti di forza', r'forza',
        r'positive', r'what did the artist do well',
    ],
    'suggestions': [
        r'suggestion(s)?', r'improvement(s)?', r'suggeriment(i)?', r'suggerimento', r'improve',
        r'consigli', r'how could this work be improved',
    ],
    'final': [
        r'final( thoughts)?', r'conclusion(s)?', r'wrap(-| )?up', r'considerazioni finali', r'finali',
        r'finale', r'finale:', r'final:',
    ],
}

# Build a single regex to match any header and capture its name
HEADER_PATTERN_PARTS = []
for area, words in AREA_HEADERS.items():
    for w in words:
        HEADER_PATTERN_PARTS.append(rf'(?P<{area}>{w})')

# We won't use the combined named groups; instead we'll do per-area search with alternatives

# Helper: split_blob_into_areas

def parse_peer_review_blob(blob: str) -> Dict[str, str]:
    """Return a dict with keys 'highlights','suggestions','final'.

    Strategy:
    - Normalize whitespace.
    - Look for known headers (case-insensitive). If headers found, split by header positions.
    - If 3 headers present, map accordingly.
    - If fewer headers found, heuristics:
      * If two headers found, assign in-order and leave missing as ''
    - If no headers found: put entire blob into 'final'.
    """
    if not blob:
        return {'highlights': '', 'suggestions': '', 'final': ''}

    text = blob.strip()

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Build a list of header regexes with canonical area tag
    header_regexes = []
    for area, words in AREA_HEADERS.items():
        # join words into alternation
        alt = '|'.join(words)
        # match header lines like "Highlights:", "-- Highlights --", or "Highlights\n"
        rx = re.compile(rf'^(?:\s*[-*#\s]*)?(?:{alt})\s*[:\-]?\s*$|^(?:{alt})\s*[:\-]\s*', re.IGNORECASE | re.MULTILINE)
        header_regexes.append((area, rx))

    # find all header matches with positions
    matches = []
    for area, rx in header_regexes:
        for m in rx.finditer(text):
            matches.append({'area': area, 'start': m.start(), 'end': m.end(), 'match': m.group(0)})

    # If no matches, try looser inline headers (e.g., 'Highlights:' inside paragraph)
    if not matches:
        # generic in-text labels
        inline_rx = re.compile(r'(highlights|strengths|suggestions|improvements|final thoughts|final|suggerimenti|punti di forza|considerazioni finali)\s*[:\-]\s*', re.IGNORECASE)
        for m in inline_rx.finditer(text):
            label = m.group(1).lower()
            if 'highlight' in label or 'forza' in label or 'strength' in label:
                a = 'highlights'
            elif 'suggest' in label or 'improv' in label or 'sugger' in label or 'consigli' in label:
                a = 'suggestions'
            else:
                a = 'final'
            matches.append({'area': a, 'start': m.start(), 'end': m.end(), 'match': m.group(0)})

    # If still no matches, fallback: all to final
    if not matches:
        return {'highlights': '', 'suggestions': '', 'final': text}

    # sort matches by position
    matches = sorted(matches, key=lambda x: x['start'])

    # Build slices from header positions to next header
    parts = {}
    for idx, m in enumerate(matches):
        start_content = m['end']
        end_content = matches[idx + 1]['start'] if idx + 1 < len(matches) else len(text)
        content = text[start_content:end_content].strip()
        # assign to area
        if m['area'] in parts:
            # append if multiple headers of same type
            parts[m['area']] += '\n\n' + content
        else:
            parts[m['area']] = content

    # ensure keys exist and empty for missing
    result = {'highlights': '', 'suggestions': '', 'final': ''}
    for k, v in parts.items():
        if k in result:
            result[k] = v

    # Heuristic: if only one captured block and it looks long, put into final instead
    captured = [v for v in result.values() if v]
    if len(captured) == 1 and len(captured[0]) > 200:
        # prefer placing long single-block into final
        only = ''
        for k in result:
            if result[k]:
                only = result[k]
                result = {'highlights': '', 'suggestions': '', 'final': only}
                break

    return result
