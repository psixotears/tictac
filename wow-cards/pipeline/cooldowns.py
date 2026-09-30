"""Fetch Wowhead spell pages for every recipe used in current routes, record ones with a cooldown >= 1h."""
import json, glob, re, os, subprocess
from concurrent.futures import ThreadPoolExecutor
os.makedirs('spellpages', exist_ok=True)
cd = set(json.load(open('data/cooldown_ids.json'))) if os.path.exists('data/cooldown_ids.json') else set()
ids = set()
for f in glob.glob('data/route_*.json'):
    for st in json.load(open(f))['steps']:
        if st.get('spell_id'): ids.add(st['spell_id'])
def check(i):
    p = f'spellpages/{i}.html'
    if not os.path.exists(p) or os.path.getsize(p) < 5000:
        subprocess.run(['curl', '-sS', '-L', '-A', 'Mozilla/5.0', '--max-time', '60', '-o', p, f'https://www.wowhead.com/forever/spell={i}'])
    h = open(p, encoding='utf-8', errors='ignore').read()
    m = re.search(r'printHtml\("(\[ul\].*?ul\])"', h, re.S); qf = m.group(1) if m else ''
    # the recipe tooltip carries "cooldown":"2 days" in envChange; quick facts rarely do -> look at both
    cdm = re.search(r'\\?"cooldown\\?":\\?"([^"\\]+)', h)
    txt = (cdm.group(1) if cdm else '') + ' ' + qf
    mm = re.search(r'(\d+)\s*(day|hour|hr)', txt, re.I)
    return i, (mm.group(0) if mm else None)
with ThreadPoolExecutor(6) as ex: res = list(ex.map(check, sorted(ids)))
new = [i for i, c in res if c]
for i, c in res:
    if c: print('cooldown', i, c)
cd |= set(new)
json.dump(sorted(cd), open('data/cooldown_ids.json', 'w'))
print('checked', len(ids), 'with cooldown total', len(cd))
