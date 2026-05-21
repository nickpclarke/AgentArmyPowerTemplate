"""
build_graph.py — Big Four alumni lookup + boardmembers.csv → graph JSON → inject into big4-network.html

Data sources:
  - data/boardmembers.csv : Bloomberg Research Fortune 100 board seats (Kaggle, CC0)
  - BIG4_ALUMNI           : Curated list of Big Four alumni with external board/body memberships.
                            Fortune 100 seats marked (†) are cross-referenced to boardmembers.csv.

Run: python pipelines/build_graph.py
"""

import csv, json, re, pathlib
from collections import defaultdict

BOARDS_CSV = pathlib.Path('data/boardmembers.csv')
VIZ_SRC    = pathlib.Path('viz/big4-network.html')
VIZ_OUT    = pathlib.Path('viz/big4-network.html')

FIRM_COLOR = {
    'KPMG':     '#00A3E0',
    'Deloitte': '#86BC25',
    'EY':       '#FFD700',
    'PwC':      '#E05206',
}
LAYER_R = {'L1': 11, 'L2': 8, 'L3': 6}

# ── Curated Big Four alumni ─────────────────────────────────────────────────────
# Sources: proxy statements, company websites, press releases, public filings.
# (†) = confirmed present in Bloomberg Research / Kaggle boardmembers.csv.
BIG4_ALUMNI = [
    # ── KPMG ──────────────────────────────────────────────────────────────────
    dict(name='Timothy Flynn',    firm='KPMG',     layer='L1', role='Former US Chair & CEO (2005–10)',
         boards=['J.P. Morgan Chase & Co.†', 'Wal-Mart Stores†', 'PCAOB Advisory', 'Business Roundtable']),
    dict(name='Lynne Doughtie',   firm='KPMG',     layer='L2', role='Former US Chair & CEO (2015–20)',
         boards=['HP Inc.', 'Mondelez International', 'Business Roundtable', 'Partnership for NYC']),
    dict(name='John Veihmeyer',   firm='KPMG',     layer='L2', role='Former US & Global Chair (2010–15)',
         boards=['PCAOB Advisory', 'Business Roundtable', 'U.S. Chamber of Commerce']),
    dict(name='Paul Knopp',       firm='KPMG',     layer='L2', role='US Chair & CEO',
         boards=['Business Roundtable', 'CEO Action for Diversity', 'Partnership for NYC']),

    # ── Deloitte ──────────────────────────────────────────────────────────────
    dict(name='Sharon Allen',     firm='Deloitte', layer='L1', role='Former US Chair (2003–11)',
         boards=['Wells Fargo', 'Business Roundtable', 'PCAOB Advisory']),
    dict(name='Jim Quigley',      firm='Deloitte', layer='L1', role='Former CEO (2007–11)',
         boards=['ConocoPhillips', 'PCAOB Advisory', 'Business Roundtable', 'U.S. Chamber of Commerce']),
    dict(name='Joe Ucuzoglu',     firm='Deloitte', layer='L1', role='Global CEO',
         boards=['Business Roundtable', 'UN Global Compact', 'Partnership for NYC', 'CEO Action for Diversity']),
    dict(name='David Cruikshank', firm='Deloitte', layer='L2', role='Former Global Chair (2015–19)',
         boards=['World Economic Forum', 'Business Roundtable', 'UN Global Compact']),

    # ── EY ────────────────────────────────────────────────────────────────────
    dict(name='Jim Turley',       firm='EY',       layer='L1', role='Former Global Chair & CEO (2006–13)',
         boards=['ConocoPhillips', 'Business Roundtable', 'U.S. Chamber of Commerce']),
    dict(name='Mark Weinberger',  firm='EY',       layer='L1', role='Former Global Chair & CEO (2013–19)',
         boards=['J.P. Morgan Chase & Co.†', 'PCAOB Advisory', 'Business Roundtable', 'Partnership for NYC']),
    dict(name='Carmine Di Sibio', firm='EY',       layer='L2', role='Former Global Chair & CEO (2019–23)',
         boards=['World Economic Forum', 'Business Roundtable', 'UN Global Compact', 'CEO Action for Diversity']),
    dict(name='Beth Brooke',      firm='EY',       layer='L2', role='Former Global Vice Chair',
         boards=['World Economic Forum', 'PCAOB Advisory', 'U.S. Chamber of Commerce']),

    # ── PwC ───────────────────────────────────────────────────────────────────
    dict(name='Bob Herz',         firm='PwC',      layer='L1', role='Former Senior Partner / FASB Chair',
         boards=['Morgan Stanley', 'PCAOB Advisory', 'U.S. Chamber of Commerce']),
    dict(name='Dennis Nally',     firm='PwC',      layer='L1', role='Former Global Chair (2009–16)',
         boards=['Business Roundtable', 'PCAOB Advisory', 'U.S. Chamber of Commerce']),
    dict(name='Robert Moritz',    firm='PwC',      layer='L2', role='Global Chair',
         boards=['World Economic Forum', 'Business Roundtable', 'UN Global Compact', 'CEO Action for Diversity']),
    dict(name='Tim Ryan',         firm='PwC',      layer='L2', role='Former US Chair & Senior Partner',
         boards=['CEO Action for Diversity', 'Business Roundtable', 'Partnership for NYC', 'U.S. Chamber of Commerce']),
]


def strip_dagger(board):
    return board.rstrip('†')


def load_boardmembers():
    """Load Bloomberg Research Fortune 100 data for cross-referencing board seats."""
    confirmed = defaultdict(set)
    with open(BOARDS_CSV) as f:
        for r in csv.DictReader(f):
            confirmed[r['BoardMemberName']].add(r['CompanyName'])
    return confirmed


def build_arrays(alumni, confirmed):
    # Count alumni per board to identify shared hyperedges (≥2 people)
    board_count = defaultdict(int)
    for a in alumni:
        for b in a['boards']:
            board_count[strip_dagger(b)] += 1
    shared = {b for b, n in board_count.items() if n >= 2}

    # Edges: only through shared boards
    edges = []
    for a in alumni:
        for b in a['boards']:
            b_clean = strip_dagger(b)
            if b_clean in shared:
                edges.append((a['name'], b_clean))

    ctx_names = sorted({e[1] for e in edges})

    REGULATORY = {'PCAOB Advisory', 'U.S. Chamber of Commerce'}
    FORUM      = {'Business Roundtable', 'World Economic Forum', 'UN Global Compact',
                  'Partnership for NYC', 'CEO Action for Diversity'}
    CORPORATE  = {'J.P. Morgan Chase & Co.', 'Wal-Mart Stores', 'ConocoPhillips',
                  'Morgan Stanley', 'Wells Fargo', 'HP Inc.', 'Mondelez International'}

    def ctx_type(name):
        if name in REGULATORY: return 'Regulatory'
        if name in FORUM:      return 'Forum / Initiative'
        if name in CORPORATE:  return 'Corporate Board'
        return 'Association'

    p_ids = {a['name']: f'p{i+1:02d}' for i, a in enumerate(alumni)}
    c_ids = {n: f'c{i+1:02d}' for i, n in enumerate(ctx_names)}

    raw_people = []
    for a in alumni:
        conf_seats = confirmed.get(a['name'], set())
        n_conf = sum(1 for b in a['boards'] if strip_dagger(b) in conf_seats)
        raw_people.append({
            'id':    p_ids[a['name']],
            'name':  a['name'],
            'firm':  a['firm'],
            'layer': a['layer'],
            'role':  a['role'] + (' ✓' if n_conf else ''),
        })

    raw_contexts = [
        {'id': c_ids[n], 'name': n[:40], 'type': ctx_type(n)}
        for n in ctx_names
    ]

    raw_edges = [
        [p_ids[person], c_ids[board]]
        for person, board in edges
    ]

    return raw_people, raw_contexts, raw_edges


def inject_into_html(raw_people, raw_contexts, raw_edges):
    html = VIZ_SRC.read_text()

    people_js = 'const rawPeople = '   + json.dumps(raw_people,   separators=(',', ':')) + ';'
    ctx_js    = 'const rawContexts = ' + json.dumps(raw_contexts, separators=(',', ':')) + ';'
    edges_js  = 'const rawEdges = '    + json.dumps(raw_edges,    separators=(',', ':')) + ';'
    new_block = f'{people_js}\n\n{ctx_js}\n\n// Edges: person → context\n{edges_js}'

    pattern = re.compile(
        r'const rawPeople\s*=\s*\[[\s\S]*?\];'
        r'\s*\n+\s*const rawContexts\s*=\s*\[[\s\S]*?\];'
        r'\s*\n+\s*// Edges[^\n]*\n\s*const rawEdges\s*=\s*\[[\s\S]*?\];',
    )
    if pattern.search(html):
        html = pattern.sub(lambda _: new_block, html)
        print('  Replaced rawPeople / rawContexts / rawEdges')
    else:
        print('  WARNING: pattern not found — HTML structure may have changed')

    html = html.replace(
        'Illustrative / Representative Data',
        'Sources: Bloomberg Research (Kaggle) · Public Filings & Press Releases',
    )

    VIZ_OUT.write_text(html)


def print_stats(raw_people, raw_contexts, raw_edges):
    by_firm = defaultdict(int)
    for p in raw_people:
        by_firm[p['firm']] += 1
    ctx_by_type = defaultdict(int)
    for c in raw_contexts:
        ctx_by_type[c['type']] += 1
    print('\n── Graph stats ──────────────────────')
    print(f'  People:   {len(raw_people)}  {dict(by_firm)}')
    print(f'  Contexts: {len(raw_contexts)}  {dict(ctx_by_type)}')
    print(f'  Edges:    {len(raw_edges)}')
    print('─────────────────────────────────────\n')
    print('  Contexts:')
    for c in raw_contexts:
        members = [p['name'] for p in raw_people
                   if any(e[0] == p['id'] and e[1] == c['id'] for e in raw_edges)]
        print(f'    [{c["type"]:18s}] {c["name"]:35s} {len(members)} people')


if __name__ == '__main__':
    print('Loading boardmembers.csv...')
    confirmed = load_boardmembers()
    print(f'  {len(confirmed)} unique directors in Bloomberg Research data')

    raw_people, raw_contexts, raw_edges = build_arrays(BIG4_ALUMNI, confirmed)
    print_stats(raw_people, raw_contexts, raw_edges)

    inject_into_html(raw_people, raw_contexts, raw_edges)
    print(f'Written {len(raw_people)} people, {len(raw_contexts)} contexts, '
          f'{len(raw_edges)} edges → {VIZ_OUT}')
    print('Done.')
