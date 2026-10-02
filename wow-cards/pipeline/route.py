"""Compute a 1-300 leveling route for a crafting profession from Wowhead Forever data.

Greedy by expected material cost per skill point with a switching penalty (so the route
does not fragment) and a second pass that discounts intermediate crafts whose product the
route needs anyway (cured hides, bars, bolts...). Only trainer/vendor/auto-learned recipes.
Usage: python3 route.py <profession> [--json]
"""
import json, math, sys, os, re
from collections import defaultdict

ITEMS = {int(k): v for k, v in json.load(open('data/items.json')).items()}
SPELLS = {int(k): v for k, v in json.load(open('data/spells.json')).items()}
TRAINER, VENDOR, QUEST = 6, 5, 4
import re
ONCE = re.compile(r"Runed .* Rod|Camp Tent|Tanning Rack|Sewing Machine|Anvil|Forge$|Workbench|Alchemy Lab|Loom|Grindstone", re.I)
LANGS = ('en', 'ru', 'cn', 'de', 'fr', 'es', 'ko')
OTHER_PROF_PRODUCTS = {}
# manual fixes from guides/beta reports (spell id -> source, learnedat)
OVERRIDE_SRC = {7418: 'auto', 18629: 'quest', 14530: 'quest', 10841: 'quest', 22813: 'quest', 9980: 'quest', 7421: 'auto', 24801: 'quest'}
OVERRIDE_LEARN = {7418: 1}
EXCLUDE_IDS = {22813, 461692, 1230643}
EXCLUDE_REAGENTS = {18240, 14342}      # Ogre Tannin (dungeon-bound), Mooncloth (cooldown product)
# cooking: no fish (needs Fishing or AH) and no holiday reagents
FISH_RE = re.compile(r"^Raw |Lobster|Squid|Bass$|Salmon|Snapper|Mightfish|Yellowtail|Redgill|Cod$|Trout|Catfish|Mackerel|Smallfish|Sagefish|Deviate Fish|Frenzy|Albacore|Halibut|Armorfish|Whimsyfin|Holiday", re.I)
PROF_EXCLUDE_REAGENT_RE = {'cooking': FISH_RE}          # Gordok Ogre Suit (dungeon-bound tannin), Enchanted Lute (quest item)
COOLDOWN = set(json.load(open('data/cooldown_ids.json'))) if os.path.exists('data/cooldown_ids.json') else set()
SEASONAL = re.compile(r"Rocket Cluster|Cluster Launcher|Rocket Launcher|Snowball|Lovely|Winter Veil|Winter Clothes|Festive|Lunar|Brewfest|Hallow", re.I)
import os
SPELL_SRC = json.load(open('data/spell_sources.json')) if os.path.exists('data/spell_sources.json') else {}
CRAFTING = ['alchemy', 'blacksmithing', 'enchanting', 'engineering', 'leatherworking', 'tailoring', 'cooking', 'first-aid']


def load_products():
    import glob, os
    for f in glob.glob('data/*_en.json'):
        prof = os.path.basename(f)[:-8]
        if prof in ('mining', 'skinning', 'herbalism', 'fishing'):
            continue
        for r in json.load(open(f)).get('recipes', []):
            if r.get('creates'):
                OTHER_PROF_PRODUCTS.setdefault(r['creates'][0], set()).add(prof)
load_products()


def base_price(i):
    it = ITEMS.get(i)
    if not it or not it.get('name_en'):
        return 20000                      # unknown item: effectively avoid
    if it.get('avgbuyout'):
        return it['avgbuyout']
    if it.get('buyprice'):
        return it['buyprice']
    q = it.get('quality', 1)
    qf = 1 if q <= 1 else 4 if q == 2 else 15
    p = (it.get('sellprice') or 25) * 4 * qf
    if i > 200000:                        # new Forever item without AH data: assume rare drop
        p *= 8
    return p


def chance(r, s):
    """Approximate Classic skill-up odds: orange/yellow ~1.0, green ~0.6 -> 0.1, grey 0."""
    o, y, g, gr = r['colors']
    if gr and s >= gr:
        return 0.0
    y = y or o
    g = g or y
    if s < y or not gr:
        return 1.0
    if s < g:
        return 1.0 - 0.4 * (s - y) / max(1, g - y)
    return max(0.05, 0.6 - 0.5 * (s - g) / max(1, gr - g))


def normalize_colors(r):
    """Wowhead Forever lacks thresholds for some recipes. [o,0,o,o] (vendor gear): Classic-like +5/+12/+20.
    [o,0,0,o] (leather/bolt conversions): short window +3/+6/+10."""
    o, y, g, gr = r['colors']
    base = o or y
    if not base:
        return
    if not y and not g and gr == o:
        r['colors'] = [o, o + 3, o + 6, o + 10]
        return
    if not y:
        y = base
    if not g or g <= y:
        g = y + 12
    if not gr or gr <= g:
        gr = max(g + 8, y + 20)
    r['colors'] = [o, y, g, gr]


def eligible(recipes, max_skill=300, prof=None):
    out = []
    bad_re = PROF_EXCLUDE_REAGENT_RE.get(prof)
    for r in recipes:
        if r.get('colors'):
            normalize_colors(r)
        if any(ITEMS.get(i, {}).get('quality', 1) >= 3 or not ITEMS.get(i, {}).get('name_en') for i, _ in r.get('reagents', [])):
            continue                  # rare (blue+) or unnamed reagents: never a leveling route
        if r['id'] in OVERRIDE_LEARN:
            r['learnedat'] = OVERRIDE_LEARN[r['id']]
        if r['id'] in OVERRIDE_SRC and OVERRIDE_SRC[r['id']] in ('quest',) and not r.get('source'):
            r['source'] = [QUEST]
        if SEASONAL.search(r['name']) or r['id'] in EXCLUDE_IDS or r['id'] in COOLDOWN or any(i in EXCLUDE_REAGENTS for i, _ in r['reagents']):
            continue
        if bad_re and any(bad_re.search(ITEMS.get(i, {}).get('name_en', '')) for i, _ in r['reagents']):
            continue
        if not r.get('source') and r['id'] > 100000 and r['id'] not in OVERRIDE_SRC:
            continue                  # new Forever recipe with no known source: unverifiable, skip
        if r.get('learnedat', 9999) > max_skill or not r.get('colors') or not r.get('reagents'):
            continue
        src = set(r.get('source', []))
        if src and not (src & {TRAINER, VENDOR, QUEST}):
            continue
        if r.get('specialization') or r.get('rank'):
            continue
        out.append(r)
    # duplicates (same name, one without a product): keep the one that has a product
    with_product = {r['name'] for r in out if r.get('creates')}
    out = [r for r in out if r.get('creates') or r['name'] not in with_product]
    return out


def matcost(r, price):
    c = sum(q * price[i] for i, q in r['reagents'])
    src = r.get('source') or []
    if not src and r.get('learnedat', 9999) > 1 and r['id'] not in OVERRIDE_SRC:
        c *= 2.2                      # unknown source (untested beta content): strongly prefer known recipes
    elif QUEST in src and not ({TRAINER, VENDOR} & set(src)):
        c *= 1.2
    return c


def greedy(recipes, price, max_skill, cost_fn=None, switch_penalty=0.4, min_run=10):
    cost_fn = cost_fn or (lambda r, p, made: matcost(r, p))
    s, cur, steps = 1, None, []
    made = defaultdict(float)
    while s < max_skill:
        cands = [r for r in recipes if r['learnedat'] <= s and chance(r, s) > 0 and not (ONCE.search(r['name']) and made[r['id']] >= 1)]
        good = [r for r in cands if chance(r, s) >= 0.5]
        if good:
            cands = good
        if not cands:
            steps.append({'from': s, 'to': s + 1, 'recipe': None, 'crafts': 0.0})
            s += 1
            continue

        def cpp(r, at):
            return cost_fn(r, price, made) / chance(r, at)
        best = min(cands, key=lambda r: (cpp(r, s), -r['colors'][3]))
        if cur and chance(cur, s) >= 0.5:
            # stay with current recipe unless the new one is clearly cheaper and usable for a while
            run = sum(1 for t in range(s, min(max_skill, s + min_run)) if chance(best, t) > 0)
            if cpp(best, s) >= cpp(cur, s) * (1 - switch_penalty) or run < min_run:
                best = cur
        cur = best
        exp = 1 / chance(best, s)
        made[best['id']] += exp
        if best.get('creates'):
            made[best['creates'][0]] += exp * best['creates'][1]
        if steps and steps[-1]['recipe'] is best:
            steps[-1]['to'] = s + 1
            steps[-1]['crafts'] += exp
        else:
            steps.append({'from': s, 'to': s + 1, 'recipe': best, 'crafts': exp})
        s += 1
    steps = merge_small(steps, max_skill)
    for st in steps:
        st['crafts'] = math.ceil(st['crafts'] - 1e-9)
    return steps


def merge_small(steps, max_skill, tiny=5):
    """Fold steps of <= tiny points into a neighbour whose recipe still skills up there."""
    changed = True
    while changed:
        changed = False
        for k, st in enumerate(steps):
            if not st['recipe'] or st['to'] - st['from'] > tiny:
                continue
            for nb in ([steps[k - 1]] if k > 0 else []) + ([steps[k + 1]] if k + 1 < len(steps) else []):
                r = nb['recipe']
                if r and r['learnedat'] <= st['from'] and all(chance(r, t) > 0 for t in range(st['from'], st['to'])):
                    added = sum(1 / chance(r, t) for t in range(st['from'], st['to']))
                    if added > st['crafts'] * 1.5 + 2:
                        continue          # neighbour is nearly grey here: merging would explode craft counts
                    nb['crafts'] += added
                    nb['from'] = min(nb['from'], st['from']); nb['to'] = max(nb['to'], st['to'])
                    steps.pop(k); changed = True
                    break
            if changed:
                break
    return steps


def tally(steps):
    produced, needed = defaultdict(int), defaultdict(int)
    for st in steps:
        r = st['recipe']
        if not r:
            continue
        for i, q in r['reagents']:
            needed[i] += q * st['crafts']
        if r.get('creates'):
            produced[r['creates'][0]] += r['creates'][1] * st['crafts']
    return produced, needed


def compute(prof, max_skill=300):
    d = json.load(open(f'data/{prof}_en.json'))
    recipes = eligible(d['recipes'], max_skill, prof)
    price = defaultdict(lambda: 20000)
    for i in {i for r in recipes for i, _ in r['reagents']} | {r['creates'][0] for r in recipes if r.get('creates')}:
        price[i] = base_price(i)
        if OTHER_PROF_PRODUCTS.get(i) and prof not in OTHER_PROF_PRODUCTS[i]:
            price[i] *= 1.5           # made by another crafting profession (potions, dust, bolts...)
        elif not OTHER_PROF_PRODUCTS.get(i) and ITEMS.get(i, {}).get('quality', 1) >= 2:
            price[i] *= 2.5           # uncommon+ raw reagent (gems, pearls, rare drops): thin supply
    # intermediates: price of a product crafted here is at most its material cost
    for _ in range(3):
        for r in recipes:
            if r.get('creates'):
                c = matcost(r, price) / max(1, r['creates'][1])
                price[r['creates'][0]] = min(price[r['creates'][0]], c)

    steps = greedy(recipes, price, max_skill)
    # pass 2: crafting an intermediate that the route needs anyway is nearly free
    produced, needed = tally(steps)
    disc = {}
    for r in recipes:
        if r.get('creates') and needed.get(r['creates'][0]):
            disc[r['id']] = price[r['creates'][0]] * r['creates'][1]

    def dmatcost(r, p, made):
        prod = r['creates'][0] if r.get('creates') else None
        if prod and disc.get(r['id']) and made[prod] < needed.get(prod, 0) - produced.get(prod, 0) + made[prod] * 0:
            return max(1, matcost(r, p) - disc[r['id']])
        return matcost(r, p)
    steps = greedy(recipes, price, max_skill, cost_fn=dmatcost)
    produced, needed = tally(steps)
    shopping = {i: q - produced.get(i, 0) for i, q in needed.items() if q - produced.get(i, 0) > 0}
    # intermediates we can craft ourselves (cured hides, bolts, bars for BS from ore are mining -> not here)
    by_product = {}
    for r in recipes:
        if r.get('creates') and r['learnedat'] <= max_skill:
            p = r['creates'][0]
            if p not in by_product or matcost(r, price) < matcost(by_product[p], price):
                by_product[p] = r
    extras = []
    for _ in range(4):
        again = False
        for i, q in list(shopping.items()):
            r = by_product.get(i)
            if not r or matcost(r, price) / max(1, r['creates'][1]) > price[i] * 0.7:
                continue                      # cheaper to buy than to craft
            n = math.ceil(q / max(1, r['creates'][1]))
            extras.append({'from': r['learnedat'], 'to': None, 'recipe': r, 'crafts': n, 'extra': True})
            del shopping[i]
            for ri, rq in r['reagents']:
                shopping[ri] = shopping.get(ri, 0) + rq * n
            again = True
        if not again:
            break
    # merge duplicate extras and slot them before the first step that needs their product
    merged = {}
    for e in extras:
        k = e['recipe']['id']
        if k in merged:
            merged[k]['crafts'] += e['crafts']
        else:
            merged[k] = e
    ROD = re.compile(r"Runed .* Rod", re.I)
    for r in recipes:
        if ROD.search(r['name']) and r.get('creates') and not any(st['recipe'] is r for st in steps) and r['id'] not in merged:
            merged[r['id']] = {'from': r['learnedat'], 'to': None, 'recipe': r, 'crafts': 1, 'extra': True}
            for ri, rq in r['reagents']:
                shopping[ri] = shopping.get(ri, 0) + rq
    for e in list(merged.values()):
        same = next((st for st in steps if st['recipe'] is e['recipe'] and not st.get('extra')), None)
        if same:
            same['crafts'] += e['crafts']
            continue
        p = e['recipe']['creates'][0]
        consumer = next((k for k, st in enumerate(steps) if st['recipe'] and any(i == p for i, _ in st['recipe']['reagents'])), None)
        learn_at = next((k for k, st in enumerate(steps) if st['to'] and st['to'] > e['recipe']['learnedat']), len(steps))
        idx = learn_at if consumer is None else max(consumer, learn_at) if consumer > learn_at else consumer
        idx = min(idx, consumer) if consumer is not None else idx
        steps.insert(idx, e)
    return steps, shopping, produced, needed


def alternatives(prof, steps, max_skill=300, n=2):
    d = json.load(open(f'data/{prof}_en.json'))
    recipes = eligible(d['recipes'], max_skill, prof)
    price = defaultdict(lambda: 20000)
    for i in {i for r in recipes for i, _ in r['reagents']}:
        price[i] = base_price(i)
    out = {}
    for st in steps:
        r0 = st['recipe']
        if not r0 or not st.get('to'):
            continue
        s0, s1 = st['from'], st['to'] - 1
        cands = [r for r in recipes if r is not r0 and r['learnedat'] <= s0 and chance(r, s1) > 0 and r['name'] != r0['name']]
        cands.sort(key=lambda r: matcost(r, price) / max(chance(r, s0), 1e-6))
        out[id(st)] = cands[:n]
    return out


def export(prof, steps, shopping):
    """Localized JSON for the renderer."""
    names = {l: {r['id']: r['name'] for r in json.load(open(f'data/{prof}_{l}.json'))['recipes']} for l in LANGS}
    def item(i, qty):
        it = ITEMS.get(i, {})
        return {'id': i, 'qty': qty, 'icon': it.get('icon', 'inv_misc_questionmark'), 'quality': it.get('quality', 1),
                'name': {l: it.get('name_' + l, f'#{i}') for l in LANGS}}
    out = {'profession': prof, 'steps': [], 'shopping': []}
    alts = alternatives(prof, steps)
    for st in steps:
        r = st['recipe']
        if not r:
            if out['steps'] and out['steps'][-1].get('missing'):
                out['steps'][-1]['to'] = st['to']
            else:
                out['steps'].append({'from': st['from'], 'to': st['to'], 'missing': True})
            continue
        product = ITEMS.get(r['creates'][0], {}) if r.get('creates') else {}
        out['steps'].append({
            'from': st['from'], 'to': st['to'], 'crafts': st['crafts'], 'spell_id': r['id'], 'extra': bool(st.get('extra')),
            'name': {l: (product.get('name_' + l) or names[l].get(r['id'], r['name'])) for l in LANGS},
            'icon': product.get('icon') or SPELLS.get(r['id'], {}).get('icon', 'inv_misc_questionmark'),
            'quality': r.get('quality', product.get('quality', 1)),
            'colors': r['colors'], 'learnedat': r['learnedat'],
            'source': ('trainer' if TRAINER in r.get('source', []) else 'vendor' if VENDOR in r.get('source', []) else 'quest' if QUEST in r.get('source', [])
                       else OVERRIDE_SRC.get(r['id']) or ('auto' if r['learnedat'] <= 1 else SPELL_SRC.get(str(r['id']), 'unknown'))),
            'reagents': [item(i, q * st['crafts']) for i, q in r['reagents']],
            'alts': [{'name': {l: ((ITEMS.get(a['creates'][0], {}) if a.get('creates') else {}).get('name_' + l) or names[l].get(a['id'], a['name'])) for l in LANGS}, 'icon': (ITEMS.get(a['creates'][0], {}) if a.get('creates') else {}).get('icon') or SPELLS.get(a['id'], {}).get('icon', 'inv_misc_questionmark'),
                      'quality': a.get('quality', 1), 'reagents': [{'name': {l: ITEMS.get(i, {}).get('name_' + l, f'#{i}') for l in LANGS}, 'icon': ITEMS.get(i, {}).get('icon', 'inv_misc_questionmark'), 'qty': q} for i, q in a['reagents']]}
                     for a in alts.get(id(st), [])],
        })
    for i, q in sorted(shopping.items(), key=lambda t: -t[1]):
        out['shopping'].append(item(i, q))
    return out


def name(i, lang='en'):
    return ITEMS.get(i, {}).get('name_' + lang) or f'#{i}'


if __name__ == '__main__':
    profs = [a for a in sys.argv[1:] if not a.startswith('--')] or CRAFTING
    for prof in profs:
        steps, shopping, produced, needed = compute(prof)
        print(f'\n===== {prof.upper()}  ({len(steps)} steps, {len(shopping)} shopping items)')
        for st in steps:
            r = st['recipe']
            if not r:
                print(f"{st['from']}-{st['to']}  ??? no recipe")
                continue
            mats = ', '.join(f"{name(i)} x{q * st['crafts']}" for i, q in r['reagents'])
            rng = f"{st['from']:>3}-{st['to']:<3}" if st['to'] else f"  +{st['from']:<4}"
            print(f"{rng} {r['name']:<34} x{st['crafts']:<4} {r['colors']}  [{mats}]")
        print('  SHOPPING:', '; '.join(f"{name(i)} {q}" for i, q in sorted(shopping.items(), key=lambda t: -t[1])))
        if '--json' in sys.argv:
            json.dump(export(prof, steps, shopping), open(f'data/route_{prof}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
