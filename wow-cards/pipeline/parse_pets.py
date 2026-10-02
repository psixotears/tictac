"""Build data/pets.json from Wowhead Forever /forever/pets pages (raw/pets/pets_<sub>.html)."""
import re, json, os, html as H

SUB = {'en': 'www', 'ru': 'ru', 'cn': 'cn', 'de': 'de', 'fr': 'fr', 'es': 'es', 'ko': 'ko'}
NK = {'en': 'enus', 'ru': 'ruru', 'cn': 'zhcn', 'de': 'dede', 'fr': 'frfr', 'es': 'eses', 'ko': 'kokr'}
COMMON = {17261: 'bite', 3009: 'claw', 23110: 'dash', 23148: 'dive'}
PASSIVE = {415429, 409365, 1278934, 444831}

h = open('raw/pets/pets_www.html', encoding='utf-8').read()
i = h.index("id: 'pets'")
seg = h[i:]
arr, _ = json.JSONDecoder().raw_decode(seg[seg.index('data:[') + 5:])
fam = {}
for a in arr:
    fam[a['id']] = {'id': a['id'], 'icon': a['icon'], 'type': a['type'], 'dietmask': a['diet'], 'spells': a['spells'],
                    'common': sorted(COMMON[s] for s in a['spells'] if s in COMMON),
                    'unique': [s for s in a['spells'] if s not in COMMON and s not in PASSIVE],
                    'name': {}, 'diet': {}, 'typename': {}, 'popularity': a.get('popularity', 0)}
spells = {}
langs_ok = []
for lang, sub in SUB.items():
    f = f'raw/pets/pets_{sub}.html'
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        continue
    langs_ok.append(lang)
    hl = open(f, encoding='utf-8').read()
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', hl, re.S):
        if 'min-width: 110px' not in r:
            continue
        m = re.search(r'href="[^"]*/forever/(?:[a-z]{2}/)?pet=(\d+)[^"]*"[^>]*>([^<]+)</a>', r)
        tds = [H.unescape(re.sub(r'<[^>]+>', '', t)).strip() for t in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
        if not m or int(m.group(1)) not in fam:
            continue
        e = fam[int(m.group(1))]
        e['name'][lang] = H.unescape(m.group(2))
        e['diet'][lang] = tds[5]
        e['typename'][lang] = tds[6]
    for m in re.finditer(r'WH\.Gatherer\.addData\(6,\s*\d+,\s*(\{.*?\})\);\n', hl, re.S):
        for sid, v in json.loads(m.group(1)).items():
            e = spells.setdefault(int(sid), {'icon': v.get('icon'), 'name': {}, 'desc': {}, 'rank': {}})
            if v.get('name_' + NK[lang]):
                e['name'][lang] = v['name_' + NK[lang]]
            d = v.get('description_' + NK[lang]) or ''
            d = re.sub(r'<!--.*?-->', '', d).strip()
            if d:
                e['desc'][lang] = d
            if v.get('rank_' + NK[lang]):
                e['rank'][lang] = v['rank_' + NK[lang]]
            if v.get('icon'):
                e['icon'] = v['icon']

qf = json.load(open('data/petspells_www.json')) if os.path.exists('data/petspells_www.json') else {}
for sid, r in qf.items():
    t = (r.get('tooltip') or '').replace('\n', ' ')
    e = spells.setdefault(int(sid), {'icon': None, 'name': {}, 'desc': {}, 'rank': {}})
    m = re.search(r'(\d+) Focus', t); e['focus'] = int(m.group(1)) if m else None
    m = re.search(r'([\d.]+ (?:sec|min)) cooldown', t); e['cd'] = m.group(1) if m else None
out = {'families': sorted(fam.values(), key=lambda e: -e['popularity']), 'spells': {str(k): v for k, v in spells.items()}, 'langs': langs_ok}
json.dump(out, open('data/pets.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for e in out['families']:
    print(e['id'], e['name'].get('en'), e['typename'].get('en'), e['common'], [(s, spells.get(s, {}).get('name', {}).get('en')) for s in e['unique']], '|', e['diet'].get('en'))
print('langs', langs_ok, 'spells', len(spells))
