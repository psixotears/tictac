"""Render a card and binary-search the content scale so the last panel ends near the footer.
Usage: python3 fit.py <lang> <bgdir> <logo|-> <prof> [<prof> ...]
"""
import json, os, subprocess, sys

TARGET = 1830          # last panel bottom (px); footer sits at ~1892
LANG, BGDIR, LOGO = sys.argv[1], sys.argv[2], sys.argv[3]
PROFS = sys.argv[4:] or ['alchemy', 'blacksmithing', 'enchanting', 'engineering', 'leatherworking', 'tailoring', 'cooking', 'first-aid']
env = dict(os.environ, NODE_PATH=subprocess.check_output(['npm', 'root', '-g']).decode().strip())


def render(prof, s):
    bg = f'../../{BGDIR}/{prof}.png' if os.path.exists(f'{BGDIR}/{prof}.png') else '../../bg/placeholder.png'
    subprocess.run(['python3', 'render.py', prof, LANG, bg, LOGO, str(s)], check=True, capture_output=True)
    out = subprocess.check_output(['node', 'shot.js', f'out/html/{prof}_{LANG}.html', f'out/png/{prof}_{LANG}.png', '1'], env=env)
    return json.loads(out)['panel']


for prof in PROFS:
    lo, hi = (0.66 if prof in ('herbalism', 'mining') else 0.8), 1.25
    best = None
    for _ in range(6):
        mid = round((lo + hi) / 2, 3)
        panel = render(prof, mid)
        if panel <= TARGET:
            best = (mid, panel); lo = mid
        else:
            hi = mid
    if best is None or best[0] != mid:
        panel = render(prof, best[0] if best else lo)
        best = (best[0] if best else lo, panel)
    print(f'{prof:<16} {LANG} scale={best[0]} panel_bottom={best[1]:.0f}')
