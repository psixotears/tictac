"""Build items.json / spells.json from WH.Gatherer.addData blocks embedded in the raw profession pages (en/ru/cn)."""
import re, json, glob, os

LANGS = {'www': 'en', 'ru': 'ru', 'cn': 'cn', 'de': 'de', 'fr': 'fr', 'es': 'es', 'ko': 'ko'}
NAME_KEYS = {'en': ['name_enus', 'name'], 'ru': ['name_ruru', 'name'], 'cn': ['name_zhcn', 'name'], 'de': ['name_dede', 'name'], 'fr': ['name_frfr', 'name'], 'es': ['name_eses', 'name'], 'ko': ['name_kokr', 'name']}

items = {int(k): v for k, v in json.load(open('data/items.json')).items()} if os.path.exists('data/items.json') else {}   # keep node-product entries
spells = {}
for f in sorted(glob.glob('raw/*.html')):
    prof, sub = os.path.basename(f)[:-5].rsplit('_', 1)
    if sub not in LANGS or prof.startswith('obj_'):
        continue
    lang = LANGS[sub]
    h = open(f, encoding='utf-8').read()
    for m in re.finditer(r'WH\.Gatherer\.addData\((\d+),\s*(\d+),\s*(\{.*?\})\);\n', h, re.S):
        t, _, body = m.groups()
        if t not in ('3', '6'):
            continue
        try:
            d = json.loads(body)
        except Exception:
            continue
        store = items if t == '3' else spells
        for k, v in d.items():
            name = next((v[nk] for nk in NAME_KEYS[lang] if v.get(nk)), None)
            e = store.setdefault(int(k), {})
            if name:
                e['name_' + lang] = name
            if v.get('icon'):
                e['icon'] = v['icon']
            if 'quality' in v:
                e['quality'] = v['quality']
            je = v.get('jsonequip') or {}
            for key in ('sellprice', 'avgbuyout', 'buyprice'):
                if je.get(key):
                    e[key] = je[key]

json.dump(items, open('data/items.json', 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(spells, open('data/spells.json', 'w', encoding='utf-8'), ensure_ascii=False)
need = set()
for f in glob.glob('data/*_en.json'):
    for r in json.load(open(f)).get('recipes', []):
        if r.get('learnedat', 9999) <= 300:
            need.update(i for i, _ in r['reagents'])
            if r.get('creates'):
                need.add(r['creates'][0])
miss = {l: [i for i in need if not items.get(i, {}).get('name_' + l)] for l in ('en', 'ru', 'cn', 'de', 'fr', 'es', 'ko')}
print('items', len(items), 'spells', len(spells), 'needed', len(need), 'missing per lang', {l: len(v) for l, v in miss.items()})
print('missing en sample', sorted(miss['en'])[:15])
print('no icon among needed', sum(1 for i in need if not items.get(i, {}).get('icon')))
print('no avgbuyout among needed', sum(1 for i in need if not items.get(i, {}).get('avgbuyout')), 'no sellprice', sum(1 for i in need if not items.get(i, {}).get('sellprice')))
