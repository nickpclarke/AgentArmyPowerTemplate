"""
dlt pipeline: Fortune 500 DEF 14A proxy filings → DuckDB

Extracts directors with Big Four affiliation and their cross-board memberships.
Run: python pipelines/edgar_big4.py
"""

import dlt, re, time, json
from edgar import Company, set_identity

# ── Big Four patterns ──────────────────────────────────────────────────────

BIG4 = {
    'KPMG':     r'\bKPMG\b',
    'Deloitte': r'\bDeloitte\b',
    'EY':       r'\bErnst\s*[&]\s*Young\b|\bEY\s+LLP\b|\bErnst and Young\b',
    'PwC':      r'\bPricewaterhouseCoopers\b|\bPwC\b|\bPrice\s+Waterhouse\b',
}

EMPLOYER_CTX = re.compile(
    r'(?:partner|principal|managing|chair|head|president|officer|'
    r'served|worked|joined|career|practice|role|prior|former|alumnu)',
    re.I
)

OTHER_BOARDS = re.compile(
    r'(?:director|trustee|board member|member of the board)\s+of\s+'
    r'([A-Z][A-Za-z0-9\s&\.,]{3,55}?'
    r'(?:Inc\.?|Corp\.?|Ltd\.?|LLC|Co\.?|Company|plc|LP|LLP|Group|Holdings|Trust|Fund|Bancorp)?)'
    r'(?:\s*[,;.]|\s+and\b)',
    re.I
)

# Name pattern: 2-4 capitalised words, possibly followed by age indicator
NAME_PAT = re.compile(
    r'(?:^|\n)([A-Z][A-Z][A-Z\s\.\-\']{4,38})\n'   # ALL CAPS name
    r'|(?:^|\n)((?:[A-Z][a-z\.\-\']+\s+){1,3}[A-Z][a-z\.\-\']+)'  # Title Case
    r'(?:\n|,\s*(?:age\s*)?\d{2})',
    re.M
)

# ── Section finder ─────────────────────────────────────────────────────────

SEC_HEADINGS = re.compile(
    r'(?:DIRECTOR(?:\s+BIOGRAPH|\s+NOMINEE|\s+CANDIDATE)'
    r'|INFORMATION ABOUT (?:OUR |THE )?DIRECTOR'
    r'|NOMINEES? FOR DIRECTOR'
    r'|BOARD OF DIRECTORS)',
    re.I
)

def bio_section(text):
    m = SEC_HEADINGS.search(text)
    start = m.start() if m else 0
    # Cap at ~40k chars — enough for a full director section
    return text[start: start + 40_000]


def detect_big4_employer(chunk):
    """Return Big4 firm key if mentioned in an employment context."""
    for firm, pat in BIG4.items():
        hit = re.search(pat, chunk, re.I)
        if not hit:
            continue
        # Look for employer-context words within 200 chars of the match
        window_start = max(0, hit.start() - 200)
        window_end   = min(len(chunk), hit.end() + 200)
        window = chunk[window_start:window_end]
        if EMPLOYER_CTX.search(window):
            return firm
    return None


def extract_other_boards(chunk):
    boards = []
    for m in OTHER_BOARDS.finditer(chunk):
        name = m.group(1).strip().rstrip('.,; ')
        if 4 < len(name) < 60 and not re.search(r'\b(?:our|the|its|this|his|her)\b', name, re.I):
            boards.append(name)
    return list(dict.fromkeys(boards))  # dedup, preserve order


def split_bios(section):
    """Split proxy section into per-director text blocks."""
    chunks, positions = [], []
    for m in NAME_PAT.finditer(section):
        name = (m.group(1) or m.group(2) or '').strip()
        # Filter noise: skip if name looks like a heading or is too short
        words = name.split()
        if len(words) < 2 or len(words) > 5:
            continue
        positions.append((m.start(), name))

    for i, (pos, name) in enumerate(positions):
        end = positions[i+1][0] if i+1 < len(positions) else pos + 3000
        text = section[pos:end]
        yield name, text


# ── dlt resources ──────────────────────────────────────────────────────────

@dlt.resource(name='directors', write_disposition='replace', primary_key=['ticker', 'name'])
def directors_resource(tickers):
    set_identity('nick@livecreative.com')

    for ticker in tickers:
        try:
            c = Company(ticker)
            filing = c.get_filings(form='DEF 14A').latest(1)
            text   = filing.document.text()
            section = bio_section(text)

            found = 0
            for name, bio in split_bios(section):
                firm = detect_big4_employer(bio)
                if not firm:
                    continue
                boards = extract_other_boards(bio)
                yield {
                    'ticker':       ticker,
                    'name':         name.title(),
                    'big4_firm':    firm,
                    'bio_snippet':  bio[:600],
                    'other_boards': json.dumps(boards),
                }
                found += 1

            print(f'  {ticker}: {found} Big Four director(s) found')
            time.sleep(0.15)

        except Exception as exc:
            print(f'  {ticker}: ERROR — {exc}')


@dlt.source(name='edgar_big4')
def edgar_source(tickers):
    yield directors_resource(tickers)


# ── Run ────────────────────────────────────────────────────────────────────

FORTUNE_100 = [
    'WMT','AMZN','AAPL','UNH','BRK-B','CVS','XOM','MSFT','MCK','ABC',
    'ACI','ANTM','CAH','CI','HUM','JPM','BAC','WFC','GS','MS',
    'JNJ','PFE','ABT','MRK','BMY','CVX','COP','SLB','EOG','PXD',
    'GE','HON','MMM','CAT','DE','BA','LMT','RTX','NOC','GD',
    'VZ','T','CMCSA','NFLX','DIS','META','GOOGL','TSLA','NVDA','AMD',
]

if __name__ == '__main__':
    pipeline = dlt.pipeline(
        pipeline_name='edgar_big4',
        destination='duckdb',
        dataset_name='big4_network',
        pipelines_dir='pipelines/.dlt_state',
    )
    load_info = pipeline.run(edgar_source(tickers=FORTUNE_100))
    print(load_info)
    print(f'\nRows loaded: {load_info.load_packages[0].jobs}')
