"""
build_chord.py — Big Four risk CSV → chord matrix → inject into big4-mobile.html

Run after downloading data/big4_financial_risk_compliance.csv:
    python pipelines/build_chord.py
"""

import csv, json, re, pathlib
from collections import defaultdict

DATA    = pathlib.Path('data/big4_financial_risk_compliance.csv')
VIZ_SRC = pathlib.Path('viz/big4-mobile.html')
VIZ_OUT = pathlib.Path('viz/big4-mobile.html')

FIRMS     = ['KPMG', 'Deloitte', 'EY', 'PwC']
FIRM_NORM = {'Ernst & Young': 'EY'}


def load_rows():
    with open(DATA) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r['Firm_Name'] = FIRM_NORM.get(r['Firm_Name'], r['Firm_Name'])
    return rows


def compute_matrix(rows):
    """
    Aggregate high-risk audit cases by firm × industry.
    Pairwise overlap = sum over industries of min(firm_a, firm_b).
    """
    eng = defaultdict(lambda: defaultdict(int))
    for r in rows:
        eng[r['Firm_Name']][r['Industry_Affected']] += int(r['High_Risk_Cases'])

    industries = sorted({r['Industry_Affected'] for r in rows})
    n = len(FIRMS)
    mat = [[0] * n for _ in range(n)]
    for i, fa in enumerate(FIRMS):
        for j, fb in enumerate(FIRMS):
            if i != j:
                mat[i][j] = sum(
                    min(eng[fa].get(ind, 0), eng[fb].get(ind, 0))
                    for ind in industries
                )
    return mat, eng, industries


def compute_pairs(rows, eng, industries):
    """Build PAIR detail: each firm pair shows industries sorted by shared high-risk volume."""
    fraud      = defaultdict(int)
    violations = defaultdict(int)
    for r in rows:
        fraud[r['Firm_Name']]      += int(r['Fraud_Cases_Detected'])
        violations[r['Firm_Name']] += int(r['Compliance_Violations'])

    PAIR = {}
    for i, fa in enumerate(FIRMS):
        for j, fb in enumerate(FIRMS):
            if j <= i:
                continue
            k = f'{i}-{j}'
            items = []
            for ind in sorted(industries):
                a = eng[fa].get(ind, 0)
                b = eng[fb].get(ind, 0)
                if a and b:
                    items.append({
                        'name': ind,
                        'type': f'{min(a, b):,} shared high-risk cases',
                    })
            items.sort(key=lambda x: -int(x['type'].replace(',', '').split()[0]))
            PAIR[k] = {
                'label': f'{fa}  ↔  {fb}',
                'items': items,
            }
    return PAIR


def build_stats(rows):
    totals = defaultdict(lambda: {'engagements': 0, 'fraud': 0, 'n': 0})
    for r in rows:
        f = r['Firm_Name']
        totals[f]['engagements'] += int(r['Total_Audit_Engagements'])
        totals[f]['fraud']       += int(r['Fraud_Cases_Detected'])
        totals[f]['n']           += 1
    return totals


def inject(mat, PAIR, stats, n_rows):
    html = VIZ_SRC.read_text()

    # 1. Replace matrix
    mat_js = 'const matrix = ' + json.dumps(mat, separators=(',', ':')) + ';'
    html = re.sub(r'const matrix\s*=\s*\[[\s\S]*?\];', lambda _: mat_js, html)

    # 2. Replace PAIR (ends with \n}; on its own line)
    pair_js = 'const PAIR = ' + json.dumps(PAIR, separators=(',', ':')) + ';'
    html = re.sub(r'const PAIR\s*=\s*\{[\s\S]*?\n\};', lambda _: pair_js, html)

    # 3. Update stats row: Leaders → Engagements(k), Contexts → Fraud Cases, Firm Pairs stays
    total_eng   = sum(s['engagements'] for s in stats.values()) // 1000
    total_fraud = sum(s['fraud'] for s in stats.values())
    html = re.sub(r'(<div class="stt-n">)\d+(</div><div class="stt-l">Leaders</div>)',
                  f'\\g<1>{total_eng}k\\2', html)
    html = re.sub(r'(<div class="stt-n">)\d+(</div><div class="stt-l">Contexts</div>)',
                  f'\\g<1>{total_fraud}\\2', html)
    html = html.replace('<div class="stt-l">Leaders</div>',  '<div class="stt-l">Engagements</div>')
    html = html.replace('<div class="stt-l">Contexts</div>', '<div class="stt-l">Fraud Cases</div>')

    # 4. Update the hint text
    industries = sorted({item['name'] for p in PAIR.values() for item in p['items']})
    most_contested = max(
        industries,
        key=lambda ind: sum(
            int(p['items'][i]['type'].replace(',','').split()[0])
            for p in PAIR.values()
            for i, item in enumerate(p['items']) if item['name'] == ind
        )
    )
    new_hint = (
        f'Tap a <b style="color:#00A3E0">chord</b> to see shared high-risk audit sectors.<br><br>'
        f'Tap an <b style="color:#00A3E0">arc segment</b> to see all sectors a firm covers.<br><br>'
        f'<b style="color:#00A3E0">{most_contested}</b> has the highest shared risk volume across all four firms.'
    )
    html = re.sub(
        r'Tap a <b style="color:#00A3E0">chord</b>[\s\S]*?all four firms\.',
        lambda _: new_hint,
        html,
    )

    # 5. Update watermark
    html = html.replace(
        'Illustrative / Representative Data',
        f'Big Four Audit Risk 2020–2025 · {n_rows} observations · Kaggle CC0',
    )

    VIZ_OUT.write_text(html)
    print(f'Written chord matrix + PAIR data → {VIZ_OUT}')


def print_stats(mat, PAIR, stats):
    print('\n── Chord stats ──────────────────────')
    print('  Matrix (high-risk overlap):')
    for i, f in enumerate(FIRMS):
        print(f'    {f}: {mat[i]}')
    print(f'  Firm pairs: {len(PAIR)}')
    for f, s in stats.items():
        print(f'  {f}: {s["engagements"]:,} engagements, {s["fraud"]} fraud cases ({s["n"]} obs)')
    print('─────────────────────────────────────\n')


if __name__ == '__main__':
    print('Loading data...')
    rows = load_rows()
    print(f'  {len(rows)} rows, firms: {sorted({r["Firm_Name"] for r in rows})}')

    mat, eng, industries = compute_matrix(rows)
    PAIR  = compute_pairs(rows, eng, industries)
    stats = build_stats(rows)
    print_stats(mat, PAIR, stats)

    inject(mat, PAIR, stats, len(rows))
    print('Done.')
