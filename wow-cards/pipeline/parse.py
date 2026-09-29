import re, json, sys, glob, os
def listviews(h):
    out={}
    for m in re.finditer(r'new Listview\((\{.*?\})\);', h, re.S):
        blk=m.group(1)
        idm=re.search(r'id:\s*[\'"]([\w-]+)[\'"]',blk); dm=re.search(r'data:\s*(\[.*\])\s*[,}]',blk,re.S)
        if not idm or not dm: continue
        try: out[idm.group(1)]=json.loads(dm.group(1))
        except Exception as e: out[idm.group(1)]=('ERR',str(e)[:80])
    return out
summary={}
for f in sorted(glob.glob('raw/*.html')):
    prof,lang=os.path.basename(f)[:-5].rsplit('_',1); lang={'www':'en'}.get(lang,lang)
    lv=listviews(open(f,encoding='utf-8').read())
    rec=lv.get('recipes',[]); 
    if isinstance(rec,tuple): print(f,rec); rec=[]
    json.dump({k:v for k,v in lv.items() if k in ('recipes','recipe-items','crafted-items','spells')}, open(f'data/{prof}_{lang}.json','w',encoding='utf-8'), ensure_ascii=False)
    summary.setdefault(prof,{})[lang]=len(rec)
for p,v in summary.items(): print(p,v)
