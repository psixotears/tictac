import json, glob, os, subprocess
icons = set(json.load(open('data/skill_icons.json')).values()) | {'spell_holy_sealofsacrifice', 'trade_fishing', 'trade_mining'}
for f in glob.glob('data/route_*.json'):
    d = json.load(open(f))
    for st in d['steps']:
        if st.get('missing'): continue
        icons.add(st['icon']); icons.update(r['icon'] for r in st['reagents'])
        for a in st.get('alts', []): icons.add(a['icon']); icons.update(m['icon'] for m in a['reagents'])
    icons.update(i['icon'] for i in d['shopping'])
os.makedirs('icons', exist_ok=True)
missing = [i for i in icons if not os.path.exists(f'icons/{i}.jpg') or os.path.getsize(f'icons/{i}.jpg') < 500]
print('icons needed', len(icons), 'missing', len(missing))
procs = [subprocess.Popen(['curl', '-sS', '-A', 'Mozilla/5.0', '--max-time', '30', '-o', f'icons/{i}.jpg', f'https://wow.zamimg.com/images/wow/icons/large/{i}.jpg']) for i in missing]
for p in procs: p.wait()
bad = [i for i in missing if not os.path.exists(f'icons/{i}.jpg') or open(f'icons/{i}.jpg','rb').read(4) != b'\xff\xd8\xff\xe0' and open(f'icons/{i}.jpg','rb').read(2) != b'\xff\xd8']
print('still bad', bad)
