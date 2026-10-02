"""Build the HTML for one profession card (1080x1920) from data/route_<prof>.json.
Usage: python3 render.py <profession> <lang> [background.png]  -> out/html/<prof>_<lang>.html
"""
import json, sys, os, html

UI = {
    'en': {'guide': 'Leveling Guide 1–300', 'shopping': 'Shopping List', 'steps': 'Route', 'trainer': 'Trainer', 'vendor': 'Vendor',
           'quest': 'Quest', 'auto': 'Starter', 'drop': 'Drop', 'unknown': '?', 'item?': '?',
           'ranknames': ['Journeyman', 'Expert', 'Artisan'], 'charlvl': 'character level', 'skilllbl': 'skill',
           'alts': 'Alternatives (same skill range)', 'nodes': 'Nodes by skill', 'skill': 'Skill', 'where': 'Where to find', 'moblvl': 'Mob level', 'zones': 'Zones',
           'ooze': 'also ooze-covered', 'skinnote': 'Required skill: (mob level − 10) × 10 up to level 20, then mob level × 5', 'gguide': 'Gathering Guide 1–300',
           'smallfish': 'For the Fish Bowl camp object — best catch rates', 'nogetaway': 'No get-aways from', 'fishnote': 'Zone thresholds from WoW Classic — to be verified in the Forever beta', 'fguide': 'Fishing Guide 1–300',
           'beta': 'BETA DATA', 'src': 'Data: Wowhead (Forever) · Craft counts are expected values, buy ~10% extra',
           'ranks': 'Journeyman 50 · Expert 125 · Artisan 200', 'title': 'World of Warcraft: Forever'},
    'ru': {'guide': 'Гайд по прокачке 1–300', 'shopping': 'Список покупок', 'steps': 'Маршрут', 'trainer': 'Учитель', 'vendor': 'Торговец',
           'quest': 'Задание', 'auto': 'Изучено', 'drop': 'Добыча', 'unknown': '?', 'item?': '?',
           'ranknames': ['Подмастерье', 'Умелец', 'Искусник'], 'charlvl': 'уровень персонажа', 'skilllbl': 'навык',
           'alts': 'Альтернативы (тот же диапазон)', 'nodes': 'Узлы по навыку', 'skill': 'Навык', 'where': 'Где искать', 'moblvl': 'Уровень мобов', 'zones': 'Зоны',
           'ooze': 'есть и покрытые слизью', 'skinnote': 'Нужный навык: (уровень моба − 10) × 10 до 20 ур., дальше уровень моба × 5', 'gguide': 'Гайд по добыче 1–300',
           'smallfish': 'Для Аквариума (объект лагеря) — где ловится чаще всего', 'nogetaway': 'Без срывов от', 'fishnote': 'Пороги зон взяты из WoW Classic — требуют проверки в бете Forever', 'fguide': 'Гайд по рыбалке 1–300',
           'beta': 'ДАННЫЕ БЕТЫ', 'src': 'Данные: Wowhead (Forever) · Кол-во крафтов ожидаемое, берите ~10% запас',
           'ranks': 'Подмастерье 50 · Умелец 125 · Искусник 200', 'title': 'World of Warcraft: Forever'},
    'cn': {'guide': '专业升级指南 1–300', 'shopping': '材料清单', 'steps': '路线', 'trainer': '训练师', 'vendor': '商人',
           'quest': '任务', 'auto': '初始', 'drop': '掉落', 'unknown': '?', 'item?': '?',
           'ranknames': ['中级', '高级', '专家'], 'charlvl': '角色等级', 'skilllbl': '技能',
           'alts': '替代配方（同一区间）', 'nodes': '按技能等级的采集点', 'skill': '技能', 'where': '采集地点', 'moblvl': '怪物等级', 'zones': '区域',
           'ooze': '含软泥覆盖变体', 'skinnote': '所需技能：20级前为(怪物等级−10)×10，之后为怪物等级×5', 'gguide': '采集指南 1–300',
           'smallfish': '用于营地物品“鱼缸”——最佳钓取地点', 'nogetaway': '不脱钩起始', 'fishnote': '区域门槛取自 WoW Classic，待 Forever 测试服验证', 'fguide': '钓鱼指南 1–300',
           'beta': '测试服数据', 'src': '数据：Wowhead (Forever) · 制作次数为期望值，建议多备约10%',
           'ranks': '中级 50 · 高级 125 · 专家 200', 'title': '魔兽世界：无限'},
    'de': {'guide': 'Skillguide 1–300', 'shopping': 'Einkaufsliste', 'steps': 'Route', 'trainer': 'Lehrer', 'vendor': 'Händler',
           'quest': 'Quest', 'auto': 'Start', 'drop': 'Drop', 'unknown': '?', 'item?': '?',
           'ranknames': ['Geselle', 'Experte', 'Fachmann'], 'charlvl': 'Charakterstufe', 'skilllbl': 'Fertigkeit',
           'alts': 'Alternativen (gleicher Bereich)', 'nodes': 'Vorkommen nach Fertigkeit', 'skill': 'Fertigkeit', 'where': 'Fundorte', 'moblvl': 'Mobstufe', 'zones': 'Zonen',
           'ooze': 'auch schleimbedeckt', 'skinnote': 'Benötigte Fertigkeit: (Mobstufe − 10) × 10 bis Stufe 20, danach Mobstufe × 5', 'gguide': 'Sammelguide 1–300',
           'smallfish': 'Für das Lagerobjekt Aquarium – beste Fangorte', 'nogetaway': 'Kein Entkommen ab', 'fishnote': 'Zonenwerte aus WoW Classic – in der Forever-Beta zu prüfen', 'fguide': 'Angelguide 1–300',
           'beta': 'BETA-DATEN', 'src': 'Daten: Wowhead (Forever) · Anzahl = Erwartungswert, ~10 % Reserve einplanen',
           'ranks': 'Geselle 50 · Experte 125 · Fachmann 200', 'title': 'World of Warcraft: Forever'},
    'fr': {'guide': 'Guide de montée 1–300', 'shopping': "Liste d'achats", 'steps': 'Itinéraire', 'trainer': 'Maître', 'vendor': 'Vendeur',
           'quest': 'Quête', 'auto': 'De base', 'drop': 'Butin', 'unknown': '?', 'item?': '?',
           'ranknames': ['Compagnon', 'Expert', 'Artisan'], 'charlvl': 'niveau du personnage', 'skilllbl': 'compétence',
           'alts': 'Alternatives (même plage)', 'nodes': 'Gisements par compétence', 'skill': 'Compétence', 'where': 'Où trouver', 'moblvl': 'Niveau des monstres', 'zones': 'Zones',
           'ooze': 'aussi couverts de vase', 'skinnote': 'Compétence requise : (niveau du monstre − 10) × 10 jusqu\'au niveau 20, puis niveau × 5', 'gguide': 'Guide de récolte 1–300',
           'smallfish': "Pour l'objet de camp Aquarium – meilleurs taux de pêche", 'nogetaway': 'Sans fuite dès', 'fishnote': 'Seuils de zones issus de WoW Classic – à vérifier sur la bêta Forever', 'fguide': 'Guide de pêche 1–300',
           'beta': 'DONNÉES BÊTA', 'src': 'Données : Wowhead (Forever) · Nombres = valeurs attendues, prévoyez ~10 % de marge',
           'ranks': 'Compagnon 50 · Expert 125 · Artisan 200', 'title': 'World of Warcraft: Forever'},
    'es': {'guide': 'Guía de subida 1–300', 'shopping': 'Lista de compra', 'steps': 'Ruta', 'trainer': 'Instructor', 'vendor': 'Vendedor',
           'quest': 'Misión', 'auto': 'Inicial', 'drop': 'Botín', 'unknown': '?', 'item?': '?',
           'ranknames': ['Oficial', 'Experto', 'Artesano'], 'charlvl': 'nivel del personaje', 'skilllbl': 'habilidad',
           'alts': 'Alternativas (mismo rango)', 'nodes': 'Vetas por habilidad', 'skill': 'Habilidad', 'where': 'Dónde encontrar', 'moblvl': 'Nivel de monstruos', 'zones': 'Zonas',
           'ooze': 'también cubiertas de moco', 'skinnote': 'Habilidad necesaria: (nivel del monstruo − 10) × 10 hasta nivel 20, luego nivel × 5', 'gguide': 'Guía de recolección 1–300',
           'smallfish': 'Para el objeto de campamento Pecera: mejores lugares de pesca', 'nogetaway': 'Sin escapes desde', 'fishnote': 'Umbrales de zona de WoW Classic; pendientes de verificar en la beta de Forever', 'fguide': 'Guía de pesca 1–300',
           'beta': 'DATOS DE BETA', 'src': 'Datos: Wowhead (Forever) · Cantidades esperadas, compra ~10 % extra',
           'ranks': 'Oficial 50 · Experto 125 · Artesano 200', 'title': 'World of Warcraft: Forever'},
    'ko': {'guide': '숙련도 가이드 1–300', 'shopping': '구매 목록', 'steps': '경로', 'trainer': '훈련사', 'vendor': '상인',
           'quest': '퀘스트', 'auto': '기본', 'drop': '드랍', 'unknown': '?', 'item?': '?',
           'ranknames': ['숙련공', '전문가', '장인'], 'charlvl': '캐릭터 레벨', 'skilllbl': '숙련도',
           'alts': '대체 제작법 (같은 구간)', 'nodes': '숙련도별 채집물', 'skill': '숙련도', 'where': '위치', 'moblvl': '몬스터 레벨', 'zones': '지역',
           'ooze': '진흙 덮인 변형 포함', 'skinnote': '필요 숙련도: 20레벨까지 (몬스터 레벨 − 10) × 10, 이후 몬스터 레벨 × 5', 'gguide': '채집 가이드 1–300',
           'smallfish': '야영지 물건 어항 제작용 – 가장 잘 잡히는 지역', 'nogetaway': '놓침 없음', 'fishnote': '지역 기준은 WoW 클래식 자료 – Forever 베타에서 확인 필요', 'fguide': '낚시 가이드 1–300',
           'beta': '베타 데이터', 'src': '자료: Wowhead (Forever) · 제작 횟수는 기대값, ~10% 여유분 권장',
           'ranks': '숙련공 50 · 전문가 125 · 장인 200', 'title': 'World of Warcraft: Forever'},
}
PROF_NAMES = {
    'alchemy': {'en': 'Alchemy', 'ru': 'Алхимия', 'cn': '炼金术', 'de': 'Alchemie', 'fr': 'Alchimie', 'es': 'Alquimia', 'ko': '연금술'},
    'blacksmithing': {'en': 'Blacksmithing', 'ru': 'Кузнечное дело', 'cn': '锻造', 'de': 'Schmiedekunst', 'fr': 'Forge', 'es': 'Herrería', 'ko': '대장기술'},
    'enchanting': {'en': 'Enchanting', 'ru': 'Наложение чар', 'cn': '附魔', 'de': 'Verzauberkunst', 'fr': 'Enchantement', 'es': 'Encantamiento', 'ko': '마법부여'},
    'engineering': {'en': 'Engineering', 'ru': 'Инженерное дело', 'cn': '工程学', 'de': 'Ingenieurskunst', 'fr': 'Ingénierie', 'es': 'Ingeniería', 'ko': '기계공학'},
    'leatherworking': {'en': 'Leatherworking', 'ru': 'Кожевничество', 'cn': '制皮', 'de': 'Lederverarbeitung', 'fr': 'Travail du cuir', 'es': 'Marroquinería', 'ko': '가죽 세공'},
    'tailoring': {'en': 'Tailoring', 'ru': 'Портняжное дело', 'cn': '裁缝', 'de': 'Schneiderei', 'fr': 'Couture', 'es': 'Sastrería', 'ko': '재봉술'},
    'cooking': {'en': 'Cooking', 'ru': 'Кулинария', 'cn': '烹饪', 'de': 'Kochkunst', 'fr': 'Cuisine', 'es': 'Cocina', 'ko': '요리'},
    'first-aid': {'en': 'First Aid', 'ru': 'Первая помощь', 'cn': '急救', 'de': 'Erste Hilfe', 'fr': 'Secourisme', 'es': 'Primeros auxilios', 'ko': '응급치료'},
    'mining': {'en': 'Mining', 'ru': 'Горное дело', 'cn': '采矿', 'de': 'Bergbau', 'fr': 'Minage', 'es': 'Minería', 'ko': '채광'},
    'herbalism': {'en': 'Herbalism', 'ru': 'Травничество', 'cn': '草药学', 'de': 'Kräuterkunde', 'fr': 'Herboristerie', 'es': 'Herboristería', 'ko': '약초채집'},
    'skinning': {'en': 'Skinning', 'ru': 'Снятие шкур', 'cn': '剥皮', 'de': 'Kürschnerei', 'fr': 'Dépeçage', 'es': 'Desuello', 'ko': '무두질'},
    'fishing': {'en': 'Fishing', 'ru': 'Рыбная ловля', 'cn': '钓鱼', 'de': 'Angeln', 'fr': 'Pêche', 'es': 'Pesca', 'ko': '낚시'},
}
SKILL_ICON = {**json.load(open('data/skill_icons.json')), 'First Aid': 'spell_holy_sealofsacrifice', 'Fishing': 'trade_fishing', 'Mining': 'trade_mining'}
QCOLOR = {0: '#9d9d9d', 1: '#ffffff', 2: '#1eff00', 3: '#0070dd', 4: '#a335ee', 5: '#ff8000'}
HEAD_FONT = {'en': "'Cinzel', serif", 'ru': "'Cormorant SC', 'Cinzel', serif", 'cn': "'Noto Serif SC', serif", 'de': "'Cinzel', serif", 'fr': "'Cinzel', serif", 'es': "'Cinzel', serif", 'ko': "'Cinzel', 'Noto Serif KR', serif"}
BODY_FONT = {'en': "'Noto Sans', sans-serif", 'ru': "'Noto Sans', sans-serif", 'cn': "'Noto Sans SC', 'Noto Sans', sans-serif", 'de': "'Noto Sans', sans-serif", 'fr': "'Noto Sans', sans-serif", 'es': "'Noto Sans', sans-serif", 'ko': "'Noto Sans KR', 'Noto Sans', sans-serif"}

CSS = """
@import url('../../fonts/fonts.css');
*{box-sizing:border-box;margin:0;padding:0}
:root{--s:1;--gold:#d4b46a;--gold2:#8f7434;--ink:#f3e9d2;--dim:#c9bb9a;--panel:rgba(14,9,4,.8);--line:rgba(212,180,106,.55)}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0b0704}
body{font-family:BODYFONT;color:var(--ink);position:relative;word-break:keep-all;overflow-wrap:break-word}
.bg{position:absolute;inset:0;background:url('BG') center/cover no-repeat}
.bg::after{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 30%,rgba(0,0,0,.05),rgba(0,0,0,.55) 70%,rgba(0,0,0,.8))}
.card{position:absolute;inset:0;padding:34px 40px 28px;display:flex;flex-direction:column;gap:14px}
.head{text-align:center}
.logo{height:96px;display:flex;align-items:center;justify-content:center}
.logo img{max-height:96px;max-width:520px;filter:drop-shadow(0 4px 10px rgba(0,0,0,.9)) drop-shadow(0 0 18px rgba(0,0,0,.8))}
.logo .txt{font-family:HEADFONT;font-size:34px;letter-spacing:.14em;color:var(--gold);text-shadow:0 2px 8px #000}
.titlerow{display:flex;align-items:center;justify-content:center;gap:20px;margin-top:8px;padding:10px 40px 12px;border-radius:14px;background:radial-gradient(ellipse at center,rgba(8,5,2,.72) 40%,rgba(8,5,2,.35) 75%,transparent 100%)}
.skillicon{width:76px;height:76px;border:3px solid var(--gold);border-radius:10px;box-shadow:0 0 0 2px #2a1b08,0 6px 18px rgba(0,0,0,.8);background:#000}
.skillicon img{width:100%;height:100%;border-radius:7px;display:block}
h1{font-family:HEADFONT;font-size:H1SIZE;line-height:1;color:#fff;text-shadow:0 0 18px rgba(212,180,106,.35),0 3px 6px #000;font-weight:700}
.sub{font-family:HEADFONT;font-size:22px;letter-spacing:.12em;color:var(--gold);margin-top:8px;text-transform:uppercase;text-shadow:0 1px 3px #000,0 0 10px rgba(0,0,0,.9)}
.beta{display:inline-block;margin-left:14px;padding:2px 10px;background:rgba(8,5,2,.6);border:1.5px solid var(--gold);border-radius:4px;font-size:15px;letter-spacing:.14em;vertical-align:middle;color:var(--gold)}
.rule{height:2px;background:linear-gradient(90deg,transparent,var(--gold) 20%,var(--gold) 80%,transparent);position:relative;margin:4px 40px}
.rule::after{content:'◆';position:absolute;left:50%;top:-11px;transform:translateX(-50%);color:var(--gold);font-size:16px;background:transparent}
.panel{background:var(--panel);border:1.5px solid var(--line);border-radius:12px;padding:10px 16px 12px;backdrop-filter:blur(2px)}
.ptitle{font-family:HEADFONT;font-size:21px;letter-spacing:.1em;color:var(--gold);text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:12px}
.ptitle::after{content:'';flex:1;height:1px;background:var(--line)}
.shop{display:grid;grid-template-columns:repeat(var(--cols,4),1fr);gap:calc(4px * var(--s)) calc(14px * var(--s))}
.item{display:flex;align-items:center;gap:calc(7px * var(--s));font-size:calc(16.5px * var(--s));line-height:1.05;min-height:calc(34px * var(--s))}
.item img{width:calc(30px * var(--s));height:calc(30px * var(--s));border-radius:calc(5px * var(--s));border:calc(1.5px * var(--s)) solid #4a3a1c;flex:none}
.item .n{flex:1;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.item .q{font-weight:700;color:var(--gold);font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;table-layout:fixed}
tr{border-top:calc(1px * var(--s)) solid rgba(212,180,106,.22)}
tr:first-child{border-top:0}
td{padding:calc(5px * var(--s)) calc(5px * var(--s)) calc(7px * var(--s));vertical-align:middle;height:calc(40px * var(--s))}
tr.chk td{height:auto;padding:calc(6px * var(--s)) 6px calc(4px * var(--s));font-family:HEADFONT;font-size:calc(16px * var(--s));letter-spacing:.08em;color:var(--gold);text-transform:uppercase;background:linear-gradient(90deg,rgba(212,180,106,.14),transparent 70%)}
tr.chk .d{font-size:11px;vertical-align:middle;margin:0 4px}
tr.chk b{color:#ffd95a;font-size:calc(21px * var(--s));font-weight:700;text-shadow:0 0 8px rgba(255,217,90,.35);letter-spacing:0}
td.rng{font-family:HEADFONT;font-size:calc(20px * var(--s));color:var(--gold);white-space:nowrap;width:calc(112px * var(--s));font-weight:700}
td.rng.extra{color:#9fd0ff;font-size:calc(16px * var(--s))}
td.rec{width:auto}
.rec .w{display:flex;align-items:center;gap:calc(10px * var(--s))}
.rec img{width:calc(32px * var(--s));height:calc(32px * var(--s));border-radius:calc(5px * var(--s));border:calc(1.5px * var(--s)) solid #4a3a1c;flex:none}
.rec .nm{font-size:calc(19px * var(--s));line-height:1.05;font-weight:600;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.rec .x{color:var(--gold);font-weight:700;font-size:calc(19px * var(--s));white-space:nowrap;display:inline;margin-left:4px}
.rec .note{display:inline-block;margin-left:calc(8px * var(--s));font-size:calc(14px * var(--s));color:#ffb36b;border:calc(1px * var(--s)) solid #c7742d;border-radius:calc(4px * var(--s));padding:0 calc(6px * var(--s));vertical-align:middle;white-space:nowrap}
td.mats{width:MATSW;white-space:nowrap}
.mats .w{display:flex;gap:calc(6px * var(--s));justify-content:flex-start}
.mat{position:relative;width:calc(34px * var(--s));height:calc(34px * var(--s));flex:none}
.mat img{width:calc(34px * var(--s));height:calc(34px * var(--s));border-radius:calc(5px * var(--s));border:calc(1.5px * var(--s)) solid #4a3a1c;display:block}
.mat b{position:absolute;right:-2px;bottom:-1px;background:#0d0803;border:calc(1px * var(--s)) solid var(--gold2);border-radius:calc(4px * var(--s));padding:0 calc(3px * var(--s));font-size:calc(12.5px * var(--s));line-height:calc(14px * var(--s));color:#fff;font-variant-numeric:tabular-nums}
td.src{width:calc(96px * var(--s));text-align:right;font-size:calc(13px * var(--s));color:var(--dim);letter-spacing:.04em;text-transform:uppercase;white-space:nowrap}
.foot{margin-top:auto;display:flex;align-items:center;justify-content:space-between;font-size:14px;color:var(--dim)}
.brand{display:flex;align-items:center;gap:12px;font-size:20px;color:var(--ink);font-weight:600;letter-spacing:.04em}
.brand img{width:22px;height:22px;opacity:.9;filter:invert(1) sepia(1) saturate(2) hue-rotate(10deg) brightness(1.1)}
"""


def build(prof, lang, bg='../../bg/placeholder.png', logo=None, s=1.0):
    d = json.load(open(f'data/route_{prof}.json', encoding='utf-8'))
    ui = UI[lang]
    pname = PROF_NAMES[prof][lang]
    icon = SKILL_ICON.get(PROF_NAMES[prof]['en'], 'inv_misc_questionmark')
    esc = html.escape

    logo_html = f'<img src="{logo}">' if logo else f'<div class="txt">{esc(ui["title"])}</div>'
    shop = ''.join(
        f'<div class="item"><img src="../../icons/{i["icon"]}.jpg"><span class="n" style="color:{QCOLOR.get(i["quality"], "#fff")}">{esc(i["name"][lang])}</span><span class="q">{i["qty"]}</span></div>'
        for i in d['shopping'])
    rows = []
    CHECK = [(50, 0, 10), (125, 1, 20), (200, 2, 35)]
    done = set()
    for st in d['steps']:
        for sk, ri, lvl in CHECK:
            if ri not in done and st.get('from', 0) >= sk:
                done.add(ri)
                rows.append(f'<tr class="chk"><td colspan="4"><span class="d">◆</span> {esc(ui["ranknames"][ri])} · {esc(ui["skilllbl"])} <b>{sk}</b> · {esc(ui["charlvl"])} <b>{lvl}</b></td></tr>')
        if st.get('missing'):
            rows.append(f'<tr><td class="rng">{st["from"]}–{st["to"]}</td><td class="rec">?</td><td class="mats"></td><td class="src"></td></tr>')
            continue
        mats = ''.join(f'<div class="mat"><img src="../../icons/{r["icon"]}.jpg"><b>{r["qty"]}</b></div>' for r in st['reagents'])
        stop = ''
        if st.get('stop_note'):
            stop = f'<span class="note">{esc(ui["stop"])} {st["to"]}</span>'
        rng = f'{st["from"]} – {st["to"]}' if st.get('to') else f'⚒ {st["from"]}+'
        rows.append(
            f'<tr><td class="rng{" extra" if st.get("extra") else ""}">{rng}</td>'
            f'<td class="rec"><div class="w"><img src="../../icons/{st["icon"]}.jpg"><span class="nm" style="color:{QCOLOR.get(st["quality"], "#fff")}">{esc(st["name"][lang])} <span class="x">×{st["crafts"]}</span></span>{stop}</div></td>'
            f'<td class="mats"><div class="w">{mats}</div></td><td class="src">{esc(ui[st["source"]])}</td></tr>')
    maxm = max([len(st.get('reagents', [])) for st in d['steps']] + [1])
    alt_panel = ''
    real_steps = [st for st in d['steps'] if not st.get('missing')]
    if len(real_steps) <= 14:
        arows = []
        nalt = 2 if len(real_steps) <= 9 else 1
        for st in real_steps:
            for a in st.get('alts', [])[:nalt]:
                mats = ' '.join(f'<div class="mat"><img src="../../icons/{m["icon"]}.jpg"><b>{m["qty"]}</b></div>' for m in a['reagents'])
                arows.append(f'<tr><td class="rng">{st["from"]} – {st["to"]}</td><td class="rec"><div class="w"><img src="../../icons/{a["icon"]}.jpg"><span class="nm" style="color:{QCOLOR.get(a["quality"], "#fff")}">{esc(a["name"][lang])}</span></div></td><td class="mats"><div class="w">{mats}</div></td><td class="src"></td></tr>')
        if arows:
            alt_panel = f'<div class="panel"><div class="ptitle">{esc(ui["alts"])}</div><table>{"".join(arows)}</table></div>'
    css = CSS.replace('H1SIZE', '44px' if len(pname) > 15 else '56px').replace('MATSW', f'calc({maxm * 40 + 12}px * var(--s))').replace('--s:1;', f'--s:{s};--cols:{4 if s < 1.15 else 3};').replace('BODYFONT', BODY_FONT[lang]).replace('HEADFONT', HEAD_FONT[lang]).replace('BG', bg)
    page = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{esc(pname)}</title><style>{css}</style></head>
<body><div class="bg"></div><div class="card">
<div class="head"><div class="logo">{logo_html}</div>
<div class="titlerow"><div class="skillicon"><img src="../../icons/{icon}.jpg"></div><div><h1>{esc(pname)}</h1><div class="sub">{esc(ui['guide'])}<span class="beta">{esc(ui['beta'])}</span></div></div></div></div>
<div class="rule"></div>
<div class="panel"><div class="ptitle">{esc(ui['shopping'])}</div><div class="shop">{shop}</div></div>
<div class="panel"><div class="ptitle">{esc(ui['steps'])}</div><table>{''.join(rows)}</table></div>
{alt_panel}<div class="foot"><div>{esc(ui['src'])}</div><div class="brand"><img src="../../brand/twitch.svg"><img src="../../brand/telegram.svg"><img src="../../brand/tiktok.svg"><span>psixotears</span></div></div>
</div></body></html>"""
    os.makedirs('out/html', exist_ok=True)
    path = f'out/html/{prof}_{lang}.html'
    open(path, 'w', encoding='utf-8').write(page)
    return path


GCSS = """
td.gs{font-family:HEADFONT;font-size:calc(22px * var(--s));color:var(--gold);width:calc(110px * var(--s));font-weight:700;white-space:nowrap}
td.gn{width:calc(300px * var(--s))}
.gn .w{display:flex;align-items:center;gap:calc(10px * var(--s))}
.gn .chips{display:flex;flex-direction:column;gap:calc(3px * var(--s))}
.gn img{width:calc(34px * var(--s));height:calc(34px * var(--s));border-radius:5px;border:1.5px solid #4a3a1c;flex:none}
.gn .nm{font-size:calc(19px * var(--s));font-weight:600;line-height:1.05}
.gn .sk{display:inline-block;margin-left:6px;padding:0 6px;border:1px solid var(--gold2);border-radius:4px;font-family:HEADFONT;font-size:calc(14px * var(--s));color:#ffd95a;vertical-align:middle;line-height:1.3}
.gn .oz{font-size:calc(12px * var(--s));color:var(--dim);display:block;margin-top:2px}
td.gz{font-size:calc(16px * var(--s));line-height:1.25;color:var(--ink)}
.gz span{white-space:normal}
.gz small{color:var(--dim);font-size:calc(12.5px * var(--s))}
td.gm{font-size:calc(17px * var(--s));color:var(--ink);width:calc(120px * var(--s));white-space:nowrap}
.note{font-size:calc(14px * var(--s));color:var(--dim);margin-top:8px}
.sfish{display:flex;gap:calc(12px * var(--s));align-items:flex-start;margin-top:calc(14px * var(--s));padding-top:calc(12px * var(--s));border-top:1px solid rgba(212,180,106,.22);font-size:calc(16px * var(--s));color:var(--ink)}
.sfish img{width:calc(44px * var(--s));height:calc(44px * var(--s));border-radius:6px;border:1.5px solid #4a3a1c;flex:none}
.sfish b{color:#fff}
.sfish .gz{font-size:calc(15px * var(--s))}
"""


def build_gather(prof, lang, bg='../../bg/placeholder.png', logo=None, s=1.0):
    d = json.load(open(f'data/gather_{prof}.json', encoding='utf-8'))
    ui = UI[lang]
    pname = PROF_NAMES[prof][lang]
    icon = SKILL_ICON.get(PROF_NAMES[prof]['en'], 'inv_misc_questionmark')
    esc = html.escape
    logo_html = f'<img src="{logo}">' if logo else f'<div class="txt">{esc(ui["title"])}</div>'
    def zones_html(zs):
        def lvl(z):
            a, b = z['lvl']
            if not a: return ''
            return f'<small>{a}–{b}</small>' if b - a <= 30 else ''
        return ' · '.join(f'<span>{esc(z["name"].get(lang) or z["name"]["en"])} {lvl(z)}</span>' for z in zs)
    rows = []
    if d['kind'] == 'bands':
        for r in d['rows']:
            sk = str(r['skill']) if r['skill'] == r['skill_hi'] else f'{r["skill"]}–{r["skill_hi"]}'
            chips = ''.join(f'<div class="w"><img src="../../icons/{n["icon"]}.jpg"><div><span class="nm">{esc(n["name"].get(lang) or n["name"]["en"])} <span class="sk">{n["skill"]}</span></span>{("<span class=oz>" + esc(ui["ooze"]) + "</span>") if n.get("ooze") else ""}</div></div>' for n in r['nodes'])
            rows.append(f'<tr><td class="gs">{sk}</td><td class="gn"><div class="chips">{chips}</div></td><td class="gz">{zones_html(r["zones"])}</td></tr>')
        head = f'<tr><td class="src" style="text-align:left">{esc(ui["skill"])}</td><td class="src" style="text-align:left"></td><td class="src" style="text-align:left">{esc(ui["where"])}</td></tr>'
        note = ''
        d['kind'] = 'nodes'
    elif d['kind'] == 'fishing':
        for r in d['rows']:
            rows.append(f'<tr><td class="gs">{r["skill"]}+</td><td class="gm">{r["nogetaway"]}+</td><td class="gz">{zones_html(r["zones"])}</td></tr>')
        head = f'<tr><td class="src" style="text-align:left">{esc(ui["skill"])}</td><td class="src" style="text-align:left">{esc(ui["nogetaway"])}</td><td class="src" style="text-align:left">{esc(ui["zones"])}</td></tr>'
        note = f'<div class="note">{esc(ui["fishnote"])}</div>'
        sf = d.get('smallfish')
        if sf:
            zs = ' · '.join(f'<span>{esc(z["name"].get(lang) or z["name"]["en"])} <small>{z["pct"]}%</small></span>' for z in sf['zones'])
            note += f'<div class="sfish"><img src="../../icons/{sf["icon"]}.jpg"><div><b>{esc(sf["name"].get(lang) or sf["name"]["en"])}</b> — {esc(ui["smallfish"])}<div class="gz" style="margin-top:4px">{zs}</div></div></div>'
    else:
        for r in d['rows']:
            sk = str(r['skill']) if r.get('skill_hi', r['skill']) == r['skill'] else f'{r["skill"]}–{r["skill_hi"]}'
            rows.append(f'<tr><td class="gs">{sk}</td><td class="gm">{r["mob"][0]}–{r["mob"][1]}</td><td class="gz">{zones_html(r["zones"])}</td></tr>')
        head = f'<tr><td class="src" style="text-align:left">{esc(ui["skill"])}</td><td class="src" style="text-align:left">{esc(ui["moblvl"])}</td><td class="src" style="text-align:left">{esc(ui["zones"])}</td></tr>'
        note = f'<div class="note">{esc(ui["skinnote"])}</div>'
    css = (CSS + GCSS).replace('H1SIZE', '44px' if len(pname) > 15 else '56px').replace('MATSW', '300px').replace('--s:1;', f'--s:{s};').replace('BODYFONT', BODY_FONT[lang]).replace('HEADFONT', HEAD_FONT[lang]).replace('BG', bg)
    page = f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{esc(pname)}</title><style>{css}</style></head>
<body><div class="bg"></div><div class="card">
<div class="head"><div class="logo">{logo_html}</div>
<div class="titlerow"><div class="skillicon"><img src="../../icons/{icon}.jpg"></div><div><h1>{esc(pname)}</h1><div class="sub">{esc(ui['fguide'] if prof == 'fishing' else ui['gguide'])}<span class="beta">{esc(ui['beta'])}</span></div></div></div></div>
<div class="rule"></div>
<div class="panel"><div class="ptitle">{esc(ui['nodes'] if d['kind'] not in ('skinning', 'fishing') else ui['zones'])}<span style="font-family:inherit;font-size:15px;letter-spacing:.06em;color:var(--dim);text-transform:none">{esc(ui['ranks'])}</span></div><table><colgroup><col style="width:calc({'110px' if d['kind'] not in ('skinning', 'fishing') else '110px'} * var(--s))"><col style="width:calc({'300px' if d['kind'] not in ('skinning', 'fishing') else '150px'} * var(--s))"><col></colgroup>{head}{''.join(rows)}</table>{note}</div>
<div class="foot"><div>{esc(ui['src'].split(' · ')[0])}</div><div class="brand"><img src="../../brand/twitch.svg"><img src="../../brand/telegram.svg"><img src="../../brand/tiktok.svg"><span>psixotears</span></div></div>
</div></body></html>"""
    os.makedirs('out/html', exist_ok=True)
    path = f'out/html/{prof}_{lang}.html'
    open(path, 'w', encoding='utf-8').write(page)
    return path


if __name__ == '__main__':
    prof, lang = sys.argv[1], sys.argv[2]
    bg = sys.argv[3] if len(sys.argv) > 3 else '../../bg/placeholder.png'
    logo = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else None
    s = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
    print(build_gather(prof, lang, bg, logo, s) if prof in ('mining', 'herbalism', 'skinning', 'fishing') else build(prof, lang, bg, logo, s))
