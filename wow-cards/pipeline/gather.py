"""Build data/gather_<prof>.json for mining / herbalism / skinning / fishing from Wowhead Forever object + zone listings."""
import json, re, math, collections

LANGS = ['en', 'ru', 'de', 'fr', 'es', 'ko', 'cn']
SUB = {'en': 'www', 'ru': 'ru', 'de': 'de', 'fr': 'fr', 'es': 'es', 'ko': 'ko', 'cn': 'cn'}
ITEMS = {int(k): v for k, v in json.load(open('data/items.json')).items()}
BYNAME = {v['name_en']: k for k, v in ITEMS.items() if v.get('name_en')}


def load(key):
    per = {}
    for l in LANGS:
        try:
            per[l] = json.load(open(f'data/obj/{key}_{SUB[l]}.json', encoding='utf-8'))[0]['data']
        except FileNotFoundError:
            per[l] = []
    return per


zones = load('zones')
ZONE = {}
for l in LANGS:
    for z in zones[l]:
        e = ZONE.setdefault(z['id'], {'minlevel': z.get('minlevel', 0), 'maxlevel': z.get('maxlevel', 0), 'category': z.get('category'), 'instance': z.get('instance')})
        e['name_' + l] = z['name']
OUTDOOR = {zid for zid, z in ZONE.items() if not z.get('instance') and z['category'] in (0, 1, -1)}


def zone_list(ids, n=4):
    pool = [i for i in ids if i in ZONE and i in OUTDOOR] or [i for i in ids if i in ZONE and ZONE[i]['category'] in (2, 3)]
    pool = sorted(set(pool), key=lambda i: (ZONE[i]['minlevel'] or 99, ZONE[i]['maxlevel']))
    out, seen = [], set()
    for i in pool:
        nm = ZONE[i].get('name_en')
        if nm in seen:
            continue
        seen.add(nm); out.append(i)
    return out[:n]


import os
OVERRIDE = json.load(open('data/node_items.json')) if os.path.exists('data/node_items.json') else {}


def item_for(node_name):
    if node_name in OVERRIDE:
        return OVERRIDE[node_name]
    stem = re.sub(r"^(Ooze Covered |Rich |Small |Large |Lesser |Greater |Hakkari )", '', node_name)
    cands = [stem, stem.replace(' Mineral Vein', ' Ore').replace(' Vein', ' Ore').replace(' Deposit', ' Ore').replace(' Formation', '').replace(' Chunk', '')]
    for c in cands:
        if c in BYNAME:
            return BYNAME[c]
    stem2 = cands[-1].split(' ')[0]
    for name, i in BYNAME.items():
        if name.startswith(stem2 + ' ') and ITEMS[i].get('quality', 1) <= 3 and i < 200000:
            return i
    return None


OOZE_RE = re.compile(r"^(Ooze Covered |Покрыт(?:ая|ые|ое|ый) слизью |Schleimbedeckte[sr]? |Schleimüberzogene[sr]? |진흙 덮인 |被软泥覆盖的|软泥覆盖的)|( couvert[e]? de vase| recouvert[e]? de vase| cubiert[oa] de moco| cubiert[oa] de limo)$", re.I)


def build_nodes(prof, key, fallback_icon):
    per = load(key)
    en = per['en']
    if key == 'fishing':
        en = [o for o in en if o.get('skill', 0) > 0 and re.search(r'School|Wreckage|Debris|Pool', o['name'])]
    groups = collections.OrderedDict()
    for o in en:
        base = re.sub(r'^Ooze Covered ', '', o['name'])
        g = groups.setdefault(base, {'skill': o['skill'], 'locs': [], 'ids': set(), 'variants': set()})
        g['skill'] = min(g['skill'], o['skill'])
        g['locs'] += [x for x in o.get('location', []) if x > 0]
        g['ids'].add(o['id'])
        g['variants'].add(o['name'])
    # localized node names by object id
    names = {l: {o['id']: o['name'] for o in per[l]} for l in LANGS}
    rows = []
    for base, g in sorted(groups.items(), key=lambda t: (t[1]['skill'], t[0])):
        if g['skill'] > 300:
            continue
        oid = next((i for i in g['ids'] if names['en'].get(i) == base), next(iter(g['ids'])))
        item = item_for(base)
        rows.append({
            'skill': g['skill'],
            'name': {l: (lambda t: t[:1].upper() + t[1:])(OOZE_RE.sub('', names[l].get(oid, base)).strip()) for l in LANGS},
            'icon': (ITEMS.get(item, {}) or {}).get('icon') or fallback_icon,
            'zones': [{'id': z, 'name': {l: ZONE[z].get('name_' + l, ZONE[z].get('name_en')) for l in LANGS}, 'lvl': [ZONE[z]['minlevel'], ZONE[z]['maxlevel']]} for z in zone_list(g['locs'], 3 if key == 'herbs' else 4)],
            'ooze': any(v.startswith('Ooze Covered') for v in g['variants']),
        })
    return rows


def skinning_rows():
    """Required skill from mob level: (lvl-10)*10 up to level 20, then lvl*5."""
    rows = []
    for lvl_lo, lvl_hi in [(1, 10), (11, 15), (16, 20), (21, 30), (31, 40), (41, 50), (51, 60)]:
        req = max(1, (lvl_lo - 10) * 10) if lvl_lo <= 20 else lvl_lo * 5
        req_hi = max(1, (lvl_hi - 10) * 10) if lvl_hi <= 20 else lvl_hi * 5
        zs = [zid for zid, z in ZONE.items() if zid in OUTDOOR and z['minlevel'] and lvl_lo <= z['minlevel'] <= lvl_hi]
        zs = sorted(zs, key=lambda i: (ZONE[i]['minlevel'], ZONE[i]['maxlevel']))[:6]
        rows.append({'skill': req, 'skill_hi': req_hi, 'mob': [lvl_lo, lvl_hi],
                     'zones': [{'id': z, 'name': {l: ZONE[z].get('name_' + l, ZONE[z].get('name_en')) for l in LANGS}, 'lvl': [ZONE[z]['minlevel'], ZONE[z]['maxlevel']]} for z in zs]})
    return rows


def band(rows, max_per=4, gap=20):
    """Merge adjacent node rows into bands (same/near skill) so dense lists fit one card."""
    bands = []
    for r in rows:
        if bands and len(bands[-1]['nodes']) < max_per and r['skill'] - bands[-1]['skill_hi'] <= gap and (r['skill'] == bands[-1]['skill'] or len(rows) > 24):
            b = bands[-1]
            b['nodes'].append(r); b['skill_hi'] = r['skill']
            seen = {z['id'] for z in b['zones']}
            b['zones'] += [z for z in r['zones'] if z['id'] not in seen]
        else:
            bands.append({'skill': r['skill'], 'skill_hi': r['skill'], 'nodes': [r], 'zones': list(r['zones'])})
    for b in bands:
        b['zones'] = sorted(b['zones'], key=lambda z: (z['lvl'][0] or 99))[:4]
    return bands


if __name__ == '__main__':
    out = {
        'mining': {'kind': 'bands', 'rows': band(build_nodes('mining', 'veins', 'inv_ore_copper_01'))},
        'herbalism': {'kind': 'bands', 'rows': band(build_nodes('herbalism', 'herbs', 'inv_misc_herb_01'))},
        'skinning': {'kind': 'skinning', 'rows': skinning_rows()},
    }
    for prof, d in out.items():
        json.dump({'profession': prof, **d}, open(f'data/gather_{prof}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'== {prof}: {len(d["rows"])} rows')
        for r in d['rows']:
            zs = ', '.join(f"{z['name']['en']} ({z['lvl'][0]}-{z['lvl'][1]})" for z in r['zones'])
            nm = ' + '.join(n['name']['en'] for n in r['nodes']) if 'nodes' in r else str(r.get('mob'))
            print(f"  {r['skill']:>3}-{r.get('skill_hi', r['skill']):<3} {nm:<60} {zs}")
