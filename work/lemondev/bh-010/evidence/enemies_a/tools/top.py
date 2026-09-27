import json,sys
S=sys.argv[1]
for c in sys.argv[2:]:
    try: d=json.load(open(f"{S}/{c}_metrics.json"))
    except Exception as e: print(c,e); continue
    cl=d['clips']
    print(c, "tris", d['tris'], "top", round(d['tpose_top'],3), round(d.get('idle_top',0),3))
    for k,v in sorted(cl.items(), key=lambda kv:-kv[1].get('abs_grow',0))[:4]:
        print("  ",k,"ratio",v['max_stretch'],v['bone'],v.get('at_rest'),"| abs",v.get('abs_grow'),v.get('abs_bone'),v.get('abs_at'))
