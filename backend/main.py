"""PathShield AI Phase 3"""
import csv, io, json
from collections import Counter, defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ai_engine import calculate_trust_score, score_incident
from database import Base, engine, get_db
from mock_services import get_nearby_services
from models import Incident
from schemas import (
    AnalyticsSummary, AssignUpdate, HotspotResponse, IncidentCreate,
    IncidentResponse, IncidentTypeDist, NearbyService, PublicIncident,
    PublicSummary, SeverityDist, StatusUpdate, TimelineEvent,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="PathShield AI", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174","http://127.0.0.1:5173","http://127.0.0.1:5174"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def _now(): return datetime.now(timezone.utc)
def _pj(f):
    if not f: return []
    try: return json.loads(f)
    except: return [f]
def _tev(a,ac="system",n=""): return {"timestamp":_now().isoformat(),"action":a,"actor":ac,"note":n}
def _atl(i,e):
    evs=_pj(i.timeline_events); evs.append(e); i.timeline_events=json.dumps(evs)

def _dup(body,db):
    cands=db.query(Incident).filter(Incident.incident_type==body.incident_type,Incident.status!="resolved").all()
    lw=set(body.location.lower().split())
    for c in cands:
        if len(lw&set(c.location.lower().split()))>=2: return True,c.incident_id
        if (body.latitude is not None and c.latitude is not None
                and abs(body.latitude-c.latitude)<0.01 and abs(body.longitude-c.longitude)<0.01):
            return True,c.incident_id
    return False,None

def _hs(incidents):
    geo,txt=defaultdict(list),defaultdict(list)
    for i in incidents:
        if i.latitude is not None: geo[(round(i.latitude,2),round(i.longitude,2))].append(i)
        else: txt[" ".join(i.location.lower().split()[:3])].append(i)
    result,hid=[],1
    def _mk(g,lat=None,lng=None,area=None):
        nonlocal hid
        tc=Counter(x.incident_type for x in g); sc=Counter(x.ai_severity for x in g)
        ds=sc.most_common(1)[0][0]
        rl={"Critical":"CRITICAL","High":"HIGH","Moderate":"MEDIUM","Low":"LOW"}.get(ds,"MEDIUM")
        h={"hotspot_id":hid,"area_name":area or g[0].location,"latitude":lat,"longitude":lng,
           "incident_count":len(g),"dominant_incident_type":tc.most_common(1)[0][0],
           "dominant_severity":ds,"risk_level":rl,"incident_ids":[x.incident_id for x in g]}
        hid+=1; return h
    for (la,lo),g in geo.items():
        if len(g)>=3: result.append(_mk(g,lat=la,lng=lo,area=g[0].location))
    for a,g in txt.items():
        if len(g)>=3: result.append(_mk(g,area=a))
    return result

def _build(inc):
    svc=get_nearby_services(inc.latitude,inc.longitude)
    return IncidentResponse(
        incident_id=inc.incident_id,name=inc.name,phone=inc.phone,
        location=inc.location,latitude=inc.latitude,longitude=inc.longitude,
        incident_type=inc.incident_type,description=inc.description,
        victims_count=inc.victims_count,image_url=inc.image_url,
        ai_severity=inc.ai_severity,risk_level=inc.risk_level,ai_score=inc.ai_score,
        ai_reasons=_pj(inc.ai_reasons),first_aid=_pj(inc.first_aid),
        explanation_breakdown=_pj(inc.explanation_breakdown),
        status=inc.status,assigned_department=inc.assigned_department,
        assigned_to=inc.assigned_to,assigned_at=inc.assigned_at,
        duplicate_possible=inc.duplicate_possible,duplicate_of=inc.duplicate_of,
        trust_score=inc.trust_score,timeline_events=_pj(inc.timeline_events),
        created_at=inc.created_at,
        nearby_hospitals=[NearbyService(**s) for s in svc["hospitals"]],
        nearby_police=[NearbyService(**s) for s in svc["police"]],
        ambulance_contact=[NearbyService(**s) for s in svc["ambulance"]],
        emergency_numbers=svc["emergency_numbers"],
    )

@app.get("/")
def health_check(): return {"status":"ok","service":"PathShield AI","version":"3.0.0"}

@app.post("/incident/report",response_model=IncidentResponse,status_code=201)
def create_incident(body:IncidentCreate,db:Session=Depends(get_db)):
    dup,dup_of=_dup(body,db)
    ai=score_incident(body.incident_type,body.description,body.victims_count)
    trust=calculate_trust_score(body.phone,body.latitude,body.longitude,body.description,body.image_url,body.victims_count,dup)
    evs=[_tev("Incident reported","user",f"Type:{body.incident_type}"),
         _tev("AI triage completed","ai_engine",f"Score:{ai['score']}/100")]
    if dup: evs.append(_tev("Duplicate detected","system",f"Dup of #{dup_of}"))
    inc=Incident(name=body.name,phone=body.phone,location=body.location,
        latitude=body.latitude,longitude=body.longitude,
        incident_type=body.incident_type,description=body.description,
        victims_count=body.victims_count,image_url=body.image_url,
        ai_severity=ai["severity"],risk_level=ai["risk_level"],ai_score=ai["score"],
        ai_reasons=json.dumps(ai["reasons"]),first_aid=json.dumps(ai["first_aid_guidance"]),
        explanation_breakdown=json.dumps(ai["explanation_breakdown"]),
        status="reported",duplicate_possible=dup,duplicate_of=dup_of,
        trust_score=trust,timeline_events=json.dumps(evs),created_at=_now())
    db.add(inc); db.commit(); db.refresh(inc); return _build(inc)

@app.get("/incident/all",response_model=List[IncidentResponse])
def list_incidents(db:Session=Depends(get_db)):
    return [_build(i) for i in db.query(Incident).order_by(Incident.created_at.desc()).all()]

@app.get("/incident/{incident_id}",response_model=IncidentResponse)
def get_incident(incident_id:int,db:Session=Depends(get_db)):
    inc=db.query(Incident).filter(Incident.incident_id==incident_id).first()
    if not inc: raise HTTPException(404,"Incident not found")
    return _build(inc)

@app.patch("/incident/{incident_id}/status",response_model=IncidentResponse)
def update_status(incident_id:int,body:StatusUpdate,db:Session=Depends(get_db)):
    valid={"reported","verified","assigned","in_progress","resolved"}
    if body.status not in valid: raise HTTPException(422,f"status must be one of {valid}")
    inc=db.query(Incident).filter(Incident.incident_id==incident_id).first()
    if not inc: raise HTTPException(404,"Incident not found")
    old=inc.status; inc.status=body.status
    _atl(inc,_tev(f"Status changed to {body.status}","admin",f"Previous:{old}"))
    db.commit(); db.refresh(inc); return _build(inc)

@app.patch("/incident/{incident_id}/assign",response_model=IncidentResponse)
def assign_incident(incident_id:int,body:AssignUpdate,db:Session=Depends(get_db)):
    valid={"Police","Ambulance","Road Maintenance","Traffic Department","Vehicle Rescue"}
    if body.assigned_department not in valid: raise HTTPException(422,f"dept must be one of {valid}")
    inc=db.query(Incident).filter(Incident.incident_id==incident_id).first()
    if not inc: raise HTTPException(404,"Incident not found")
    inc.assigned_department=body.assigned_department; inc.assigned_to=body.assigned_to
    inc.assigned_at=_now(); inc.status="assigned"
    _atl(inc,_tev(f"Assigned to {body.assigned_department}","admin",f"To:{body.assigned_to}"))
    db.commit(); db.refresh(inc); return _build(inc)

@app.get("/incident/{incident_id}/timeline",response_model=List[TimelineEvent])
def get_timeline(incident_id:int,db:Session=Depends(get_db)):
    inc=db.query(Incident).filter(Incident.incident_id==incident_id).first()
    if not inc: raise HTTPException(404,"Incident not found")
    return _pj(inc.timeline_events)

@app.get("/analytics/summary",response_model=AnalyticsSummary)
def analytics_summary(db:Session=Depends(get_db)):
    all_inc=db.query(Incident).all(); total=len(all_inc)
    tc=Counter(i.incident_type for i in all_inc); sc=Counter(i.ai_severity for i in all_inc)
    hs=_hs(all_inc)
    return AnalyticsSummary(
        total_reports=total,
        critical_reports=sum(1 for i in all_inc if i.risk_level=="CRITICAL"),
        high_risk_reports=sum(1 for i in all_inc if i.risk_level=="HIGH"),
        resolved_reports=sum(1 for i in all_inc if i.status=="resolved"),
        top_incident_type=tc.most_common(1)[0][0] if total else None,
        active_hotspots=len(hs),
        severity_distribution=[SeverityDist(severity=k,count=v) for k,v in sc.items()],
        incident_type_distribution=[IncidentTypeDist(incident_type=k,count=v) for k,v in tc.items()],
    )

@app.get("/analytics/hotspots",response_model=List[HotspotResponse])
def get_hotspots(db:Session=Depends(get_db)): return _hs(db.query(Incident).all())

@app.get("/public/summary",response_model=PublicSummary)
def public_summary(db:Session=Depends(get_db)):
    all_inc=db.query(Incident).all(); total=len(all_inc)
    tc=Counter(i.incident_type for i in all_inc); sc=Counter(i.ai_severity for i in all_inc)
    hs=_hs(all_inc); recent=sorted(all_inc,key=lambda i:i.created_at,reverse=True)[:10]
    return PublicSummary(
        total_reports=total,resolved_reports=sum(1 for i in all_inc if i.status=="resolved"),
        active_hotspots=len(hs),top_issue_type=tc.most_common(1)[0][0] if total else None,
        severity_distribution=[SeverityDist(severity=k,count=v) for k,v in sc.items()],
        incident_type_distribution=[IncidentTypeDist(incident_type=k,count=v) for k,v in tc.items()],
        recent_incidents=[PublicIncident(incident_id=i.incident_id,incident_type=i.incident_type,
            location=i.location,ai_severity=i.ai_severity,risk_level=i.risk_level,
            status=i.status,created_at=i.created_at) for i in recent],
        hotspots=[HotspotResponse(**h) for h in hs],
    )

@app.get("/export/incidents.csv")
def export_csv(db:Session=Depends(get_db)):
    rows=db.query(Incident).order_by(Incident.created_at.desc()).all()
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["id","created_at","incident_type","location","severity","risk_level",
                "score","status","assigned_department","duplicate_possible","trust_score",
                "victims_count","latitude","longitude"])
    for i in rows:
        w.writerow([i.incident_id,i.created_at.isoformat() if i.created_at else "",
                    i.incident_type,i.location,i.ai_severity,i.risk_level,i.ai_score,
                    i.status,i.assigned_department or "",i.duplicate_possible,
                    i.trust_score,i.victims_count,i.latitude or "",i.longitude or ""])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=incidents.csv"})

DEMO_DATA=[
    {"name":"Ravi Kumar","phone":"9876501001","location":"Avinashi Road, Coimbatore","latitude":11.0168,"longitude":76.9558,"incident_type":"accident","description":"Bike collision with heavy bleeding. Person unconscious on highway.","victims_count":2,"image_url":None},
    {"name":"Priya Nair","phone":"9876501002","location":"Avinashi Road, Coimbatore","latitude":11.0170,"longitude":76.9560,"incident_type":"accident","description":"Multiple vehicles collision. Severe pain reported. Highway blocked.","victims_count":3,"image_url":None},
    {"name":"Suresh Babu","phone":"9876501003","location":"Avinashi Road, Coimbatore","latitude":11.0165,"longitude":76.9555,"incident_type":"accident","description":"Truck accident. Person trapped inside vehicle. Fire risk.","victims_count":1,"image_url":None},
    {"name":"Meena Devi","phone":"9876501004","location":"Gandhipuram, Coimbatore","latitude":11.0200,"longitude":76.9600,"incident_type":"pothole","description":"Large pothole causing vehicle damage near bus stand.","victims_count":0,"image_url":None},
    {"name":"Karthik Raja","phone":"9876501005","location":"Gandhipuram, Coimbatore","latitude":11.0202,"longitude":76.9602,"incident_type":"pothole","description":"Deep pothole. Minor injury to bike rider.","victims_count":1,"image_url":None},
    {"name":"Anitha S","phone":"9876501006","location":"Gandhipuram, Coimbatore","latitude":11.0198,"longitude":76.9598,"incident_type":"pothole","description":"Multiple potholes on main road. Road block forming.","victims_count":0,"image_url":None},
    {"name":"Vijay Mohan","phone":"9876501007","location":"RS Puram, Coimbatore","latitude":11.0050,"longitude":76.9600,"incident_type":"signal_issue","description":"Traffic signal not working. Signal issue causing congestion.","victims_count":0,"image_url":None},
    {"name":"Lakshmi P","phone":"9876501008","location":"Peelamedu, Coimbatore","latitude":11.0250,"longitude":77.0100,"incident_type":"signal_issue","description":"Signal failure at main junction near IIT Coimbatore.","victims_count":0,"image_url":None},
    {"name":"Dinesh T","phone":"9876501009","location":"Saibaba Colony, Coimbatore","latitude":11.0100,"longitude":76.9700,"incident_type":"road_block","description":"Road block due to fallen tree. Emergency vehicles cannot pass.","victims_count":0,"image_url":None},
    {"name":"Kavitha M","phone":"9876501010","location":"Singanallur, Coimbatore","latitude":11.0000,"longitude":77.0200,"incident_type":"street_light_issue","description":"Street light not working for 3 days. Accident risk at night.","victims_count":0,"image_url":None},
    {"name":"Arjun Das","phone":"9876501011","location":"Ukkadam, Coimbatore","latitude":10.9900,"longitude":76.9800,"incident_type":"accident","description":"Head injury and fracture. Person not breathing. Ambulance called.","victims_count":4,"image_url":"https://example.com/accident1.jpg"},
    {"name":"Selvi R","phone":"9876501012","location":"Tidel Park Road, Coimbatore","latitude":11.0300,"longitude":77.0300,"incident_type":"pothole","description":"Pothole repaired but area still has debris.","victims_count":0,"image_url":None},
    {"name":"Mani K","phone":"9876501013","location":"Avinashi Road, Coimbatore","latitude":11.0169,"longitude":76.9559,"incident_type":"accident","description":"Bike accident near same spot. Possible duplicate report.","victims_count":1,"image_url":None},
]

@app.post("/demo/seed",status_code=201)
def demo_seed(db:Session=Depends(get_db)):
    created=[]
    for d in DEMO_DATA:
        body=IncidentCreate(**d); dup,dup_of=_dup(body,db)
        ai=score_incident(body.incident_type,body.description,body.victims_count)
        trust=calculate_trust_score(body.phone,body.latitude,body.longitude,body.description,body.image_url,body.victims_count,dup)
        evs=[_tev("Incident reported","demo_seed",f"Demo:{body.incident_type}"),
             _tev("AI triage completed","ai_engine",f"Score:{ai['score']}/100")]
        inc=Incident(name=body.name,phone=body.phone,location=body.location,
            latitude=body.latitude,longitude=body.longitude,
            incident_type=body.incident_type,description=body.description,
            victims_count=body.victims_count,image_url=body.image_url,
            ai_severity=ai["severity"],risk_level=ai["risk_level"],ai_score=ai["score"],
            ai_reasons=json.dumps(ai["reasons"]),first_aid=json.dumps(ai["first_aid_guidance"]),
            explanation_breakdown=json.dumps(ai["explanation_breakdown"]),
            status="reported",duplicate_possible=dup,duplicate_of=dup_of,
            trust_score=trust,timeline_events=json.dumps(evs),is_demo=True,created_at=_now())
        db.add(inc); created.append(inc)
    db.flush()
    if len(created)>=2:
        created[-2].status="resolved"
        _atl(created[-2],_tev("Status changed to resolved","demo_seed","Demo resolved"))
    db.commit()
    return {"seeded":len(created),"message":f"Created {len(created)} demo incidents"}

@app.delete("/demo/clear")
def demo_clear(db:Session=Depends(get_db)):
    deleted=db.query(Incident).filter(Incident.is_demo==True).delete()
    db.commit()
    return {"cleared":deleted,"message":f"Removed {deleted} demo incidents"}