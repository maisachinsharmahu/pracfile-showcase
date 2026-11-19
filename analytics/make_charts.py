# Builds aggregate-only analytics charts (no names, roll numbers, IPs or per-person data).
import json, math, sys, collections as C, statistics as st
from datetime import datetime, timedelta, timezone
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
DATA, GEO, OUT = sys.argv[1:4]
d=json.load(open(DATA)); geo=json.load(open(GEO))
IST=timezone(timedelta(hours=5,minutes=30))
ts=lambda s: datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(IST)
V,E,G=d["visitors"],d["events"],d["gens"]; OK=[g for g in G if g["status"]=="ok"]
LAB={"prcv":"PRCV","ml":"ML","dwdm":"DWDM","ds":"DS","rldl":"RLDL","cs_prcv1":"PRCV CS1","cs_prcv2":"PRCV CS2","cs_ml1":"ML CS1","cs_ml2":"ML CS2","dsnew":"DS (new)"}
BG="#f7f5f2"; INK="#0b0b0b"; Y="#ffb114"; B="#0075de"; R="#f5472f"; N="#020a3b"; LB="#62aef0"; PEACH="#f6d5bb"
plt.rcParams.update({"font.family":"Helvetica","axes.facecolor":BG,"figure.facecolor":BG,"axes.edgecolor":"#d6d3cf","axes.spines.top":False,"axes.spines.right":False,"text.color":INK,"axes.labelcolor":INK,"xtick.color":"#555","ytick.color":"#555","axes.titleweight":"bold","axes.titlesize":13,"axes.titlelocation":"left"})
def save(f,name): f.savefig(f"{OUT}/{name}.png",dpi=170,bbox_inches="tight",facecolor=BG); plt.close(f)

ev=[ts(e["created_at"]) for e in E]; go=[ts(g["created_at"]) for g in OK]
t0=min(ev+go).replace(minute=0,second=0,microsecond=0); t1=max(ev+go); hrs=[]; t=t0
while t<=t1: hrs.append(t); t+=timedelta(hours=1)
fl=lambda x:x.replace(minute=0,second=0,microsecond=0)
hv=C.Counter(fl(x) for x in ev); hg=C.Counter(fl(x) for x in go)

# 1 timeline
f,a=plt.subplots(figsize=(10,3.6))
a.fill_between(range(len(hrs)),[hv[h] for h in hrs],color=LB,alpha=.55,label="Page views"); a.plot([hv[h] for h in hrs],color=B,lw=1.6)
a.bar(range(len(hrs)),[hg[h] for h in hrs],color=Y,width=.8,label="Files downloaded")
a.set_xticks(range(0,len(hrs),4)); a.set_xticklabels([h.strftime("%d %b\n%H:00") for h in hrs[::4]],fontsize=8)
a.set_title("Traffic, hour by hour (IST)"); a.legend(frameon=False); a.grid(axis="y",color="#e6e2dd"); save(f,"analytics/01_timeline")

# 2 hour of day
hv24=[sum(1 for x in ev if x.hour==h) for h in range(24)]; hg24=[sum(1 for x in go if x.hour==h) for h in range(24)]
f,a=plt.subplots(figsize=(10,3.2)); a.bar([h-.2 for h in range(24)],hv24,.4,color=B,label="Page views"); a.bar([h+.2 for h in range(24)],hg24,.4,color=Y,label="Downloads")
a.set_xticks(range(24)); a.set_title("When students show up (hour of day)"); a.legend(frameon=False); a.grid(axis="y",color="#e6e2dd"); save(f,"analytics/02_hour_of_day")

# 3 labs
lab=C.Counter(g["lab_key"] for g in OK).most_common()[::-1]
f,a=plt.subplots(figsize=(8,4)); cols={"prcv":Y,"ml":LB,"dwdm":R,"ds":PEACH,"rldl":N}
a.barh([LAB[k] for k,_ in lab],[v for _,v in lab],color=[cols.get(k,"#c9c4bd") for k,_ in lab])
for i,(k,v) in enumerate(lab): a.text(v+2,i,str(v),va="center",fontsize=9,fontweight="bold")
a.set_title("Downloads per lab / case study"); save(f,"analytics/03_labs")

# 4 funnel
uv=len(V); dl=len(set(g["visitor_id"] for g in OK)); ret=sum(1 for v in V if v["visits"]>1)
multi=sum(1 for c in C.Counter(g["visitor_id"] for g in OK).values() if c>=3)
steps=[("Unique visitors",uv),("Downloaded a file",dl),("Came back later",ret),("Downloaded 3+ files",multi)]
f,a=plt.subplots(figsize=(8,3.4))
for i,(k,v) in enumerate(steps[::-1]): a.barh(k,v,color=[Y,B,R,N][3-i] if False else [N,R,B,Y][i]); a.text(v+3,i,f"{v}  ({v/uv*100:.0f}%)",va="center",fontsize=9,fontweight="bold")
a.set_title("From visit to download"); a.set_xlim(0,uv*1.25); save(f,"analytics/04_funnel")

# 5 donuts
def donut(a,items,title):
    k=[x for x,_ in items]; v=[y for _,y in items]
    a.pie(v,labels=None,colors=[Y,B,R,N,LB,PEACH][:len(v)],startangle=90,counterclock=False,wedgeprops=dict(width=.38,edgecolor=BG,linewidth=2))
    a.set_title(title,loc="center",fontsize=11); tot=sum(v)
    a.legend([f"{x}  {y/tot*100:.0f}%" for x,y in items],loc="upper center",bbox_to_anchor=(.5,0),frameon=False,fontsize=8,ncol=1)
f,ax=plt.subplots(1,3,figsize=(11,4))
donut(ax[0],C.Counter(g["device"].title() for g in OK).most_common(),"Device")
donut(ax[1],C.Counter(g["os"] for g in OK).most_common(5),"Operating system")
donut(ax[2],C.Counter(g["browser"] for g in OK).most_common(),"Browser"); save(f,"analytics/05_devices")

# 6 labs per student
per=C.defaultdict(set)
for g in OK: per[g["roll_no"] or "v"+g["visitor_id"]].add(g["lab_key"])
pc=C.Counter(len(s) for s in per.values())
f,a=plt.subplots(figsize=(8,3.2)); a.bar([str(k) for k in sorted(pc)],[pc[k] for k in sorted(pc)],color=Y)
for i,k in enumerate(sorted(pc)): a.text(i,pc[k]+.8,pc[k],ha="center",fontsize=9,fontweight="bold")
a.set_xlabel("Different labs downloaded by one student"); a.set_title("Students who grabbed the whole set"); save(f,"analytics/06_labs_per_student")

# 7 visit loyalty + speed
vd=C.Counter(min(v["visits"],6) for v in V)
f,ax=plt.subplots(1,2,figsize=(11,3.2))
ax[0].bar([("1" if k<6 else "6+") if k!=1 else "1" for k in sorted(vd)],[vd[k] for k in sorted(vd)],color=B); ax[0].set_title("Visits per visitor")
dur=[g["duration_ms"]/1000 for g in OK if g["duration_ms"]]
ax[1].hist([x for x in dur if x<20],bins=24,color=R); ax[1].axvline(st.median(dur),color=INK,ls="--",lw=1); ax[1].text(st.median(dur)+.2,ax[1].get_ylim()[1]*.85,f"median {st.median(dur):.1f}s",fontsize=9)
ax[1].set_title("Time from click to finished file (s)"); save(f,"analytics/07_loyalty_speed")

# 8 India map
vc=C.defaultdict(C.Counter)
for e in E: vc[e["visitor_id"]][(e["meta"] or {}).get("city") or "?"]+=1; 
ctry={e["visitor_id"]:(e["meta"] or {}).get("country") for e in E}
cu=C.Counter(vc[v["id"]].most_common(1)[0][0] for v in V if v["id"] in vc and ctry.get(v["id"])=="IN")
COORD={"Delhi":(28.65,77.23),"New Delhi":(28.61,77.21),"Rāni Khera":(28.75,77.0),"Ghāziābād":(28.67,77.43),"Gurugram":(28.46,77.03),"Nāngloi Jāt":(28.68,77.06),"Faridabad":(28.41,77.31),"Delhi Cantonment":(28.59,77.13),"Kāpas Herd":(28.55,77.08),"Greater Noida":(28.47,77.5),"Gharroli":(28.62,77.32),"Mīthepur":(28.50,77.30),"Dādri":(28.55,77.55),"Ambāla":(30.38,76.78),"Mohali":(30.70,76.72),"Hashtsāl":(28.62,77.05),"Dwarka":(28.59,77.05),"Patna":(25.59,85.14),"Kanjhawāla":(28.73,77.0),"Bela":(28.0,77.6),"Pitampura":(28.70,77.13),"Alīpur":(28.80,77.14),"Hisar":(29.15,75.72),"Varanasi":(25.32,82.97),"Jaipur":(26.91,75.79),"Sonīpat":(28.99,77.02),"Narela":(28.85,77.09),"Rishīkesh":(30.09,78.27),"Civil Lines":(28.68,77.22),"Jhānsi":(25.45,78.57),"Bahadurgarh":(28.69,76.93),"Jhajjar":(28.61,76.66),"Deoli":(28.50,77.23)}
def draw(a,bbox,tol,lab):
    x0,y0,x1,y1=bbox
    for ft in geo["features"]:
        g=ft["geometry"]; polys=g["coordinates"] if g["type"]=="MultiPolygon" else [g["coordinates"]]
        for p in polys:
            r=p[0]; o=[r[0]]
            for q in r[1:]:
                if abs(q[0]-o[-1][0])+abs(q[1]-o[-1][1])>tol: o.append(q)
            if len(o)>2: a.add_patch(MP(o,closed=True,fc="#ebe7e1",ec="#c9c4bd",lw=.4))
    for c,n in cu.items():
        if c in COORD:
            la,lo=COORD[c]; 
            if x0<=lo<=x1 and y0<=la<=y1:
                a.scatter(lo,la,s=40+n*14,color=Y,alpha=.6,edgecolor=INK,linewidth=.6,zorder=3)
                if lab and n>=lab: a.text(lo+.04*(x1-x0)/1.2,la,f"{c.replace('ā','a').replace('ī','i')} {n}",fontsize=8,fontweight="bold",va="center",zorder=4)
    a.set_xlim(x0,x1); a.set_ylim(y0,y1); a.set_aspect(1/math.cos(math.radians((y0+y1)/2))); a.axis("off")
f,ax=plt.subplots(1,2,figsize=(11,6.2),gridspec_kw={"width_ratios":[1.1,1]})
draw(ax[0],(67.5,6.5,98,37.5),.08,0); ax[0].set_title("Visitors across India")
draw(ax[1],(76.6,28.1,77.8,29.1),.004,5); ax[1].set_title("Zoom: Delhi NCR")
save(f,"analytics/08_india_map")
print("ok",uv,dl,ret,multi)
