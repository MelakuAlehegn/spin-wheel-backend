from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import secrets
import time
import hashlib
from typing import Dict, List
from datetime import datetime

from database import get_session, create_db_and_tables
from models import Event, Prize, Session as DBSession, Spin
from schemas import SpinResult, InventoryStats, PrizeStats, SpinResponse

app = FastAPI(title="Spin Wheel API")

# CORS for local Next.js dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# In-memory rate limiting (can move to Redis later)
RATE_BUCKET: Dict[str, List[float]] = {}

# Default event slug
DEFAULT_EVENT_SLUG = "default"

SLICES = [
    "T-shirt",
    "USB Flash",
    "Cap",
    "Arif Try!",
    "Arif Luck Next Time!",
    "Stay Arif!",
]


def get_ip_hash(request: Request) -> str:
    ip = request.client.host if request.client else "0.0.0.0"
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def rate_limit(ip_hash: str, limit: int = 10, window_s: int = 60) -> None:
    now = time.time()
    bucket = RATE_BUCKET.setdefault(ip_hash, [])
    RATE_BUCKET[ip_hash] = [t for t in bucket if now - t <= window_s]
    if len(RATE_BUCKET[ip_hash]) >= limit:
        raise HTTPException(status_code=429, detail={"error": "rate_limited", "message": "Too many requests"})
    RATE_BUCKET[ip_hash].append(now)


@app.get("/api/status")
def get_status(db: Session = Depends(get_session)):
    """Check if prizes are available"""
    event = db.query(Event).filter(Event.slug == DEFAULT_EVENT_SLUG).first()
    if not event:
        return {"allPrizesGone": True, "message": "Event not found"}
    
    prizes = db.query(Prize).filter(Prize.event_id == event.id).all()
    total_remaining = sum(p.remaining_inventory for p in prizes if p.remaining_inventory > 0)
    
    return {
        "allPrizesGone": total_remaining == 0,
        "totalRemaining": total_remaining
    }


@app.post("/api/spin", response_model=SpinResult)
def spin(request: Request, response: Response, db: Session = Depends(get_session)):
    # Get or create session cookie
    sid = request.cookies.get("sid")
    if not sid:
        sid = secrets.token_urlsafe(16)
        response.set_cookie(
            key="sid",
            value=sid,
            httponly=True,
            samesite="lax",
        )

    ip_hash = get_ip_hash(request)
    rate_limit(ip_hash)

    # Get event
    event = db.query(Event).filter(Event.slug == DEFAULT_EVENT_SLUG).first()
    if not event:
        raise HTTPException(status_code=404, detail={"error": "event_not_found", "message": "Event not found"})

    # Check if user already spun
    db_session = db.query(DBSession).filter(DBSession.session_id == sid).first()
    if db_session and db_session.has_spun:
        raise HTTPException(status_code=409, detail={"error": "already_spun", "message": "You have already used your attempt."})

    # Get all prizes for this event
    prizes = db.query(Prize).filter(Prize.event_id == event.id).all()
    prize_map = {p.name: p for p in prizes}
    
    # Check if all prizes are gone
    total_remaining = sum(p.remaining_inventory for p in prizes if p.remaining_inventory > 0)
    all_prizes_gone = total_remaining == 0

    # Build weighted selection
    import random
    available_labels: List[str] = []
    weights: List[int] = []
    
    # Messages that are not prizes (always available)
    MESSAGE_SLICES = ["Arif Try!", "Arif Luck Next Time!", "Stay Arif!"]
    
    for label in SLICES:
        if label in prize_map:
            prize = prize_map[label]
            # If it's a message (no inventory), always use its weight
            # If it's a prize, only use weight if inventory > 0
            if prize.total_inventory == 0:
                # This is a message, always available
                w = prize.weight
            else:
                # This is a prize, only available if inventory > 0
                w = prize.weight if prize.remaining_inventory > 0 else 0
        else:
            # Shouldn't happen if seed was run, but fallback
            w = 30 if label in MESSAGE_SLICES else 0
        
        if w > 0:
            available_labels.append(label)
            weights.append(w)

    # Safety fallback
    if not any(weights):
        available_labels = ["Arif Try!", "Arif Luck Next Time!", "Stay Arif!"]
        weights = [1, 1, 1]

    # Pick winner
    label = random.choices(available_labels, weights=weights, k=1)[0]
    idx = SLICES.index(label)
    is_prize = label in prize_map

    prize_id = None
    if is_prize:
        prize = prize_map[label]
        if prize.remaining_inventory > 0:
            prize.remaining_inventory -= 1
            prize_id = prize.id
            db.add(prize)
        else:
            # Prize depleted, fallback to message
            is_prize = False
            idx = 3  # Arif Try!
            label = SLICES[idx]

    # Create or update session
    if not db_session:
        db_session = DBSession(
            session_id=sid,
            event_id=event.id,
            ip_hash=ip_hash,
            has_spun=True,
            spun_at=datetime.utcnow()
        )
        db.add(db_session)
    else:
        db_session.has_spun = True
        db_session.spun_at = datetime.utcnow()
        db.add(db_session)

    # Log spin
    spin_record = Spin(
        session_id=sid,
        event_id=event.id,
        slice_index=idx,
        label=label,
        is_prize=is_prize,
        prize_id=prize_id
    )
    db.add(spin_record)
    db.commit()

    return SpinResult(sliceIndex=idx, label=label, prize=is_prize, allPrizesGone=all_prizes_gone)


@app.get("/api/admin/inventory", response_model=InventoryStats)
def get_inventory(db: Session = Depends(get_session)):
    """Admin endpoint to view inventory and stats"""
    event = db.query(Event).filter(Event.slug == DEFAULT_EVENT_SLUG).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    prizes = db.query(Prize).filter(Prize.event_id == event.id).all()
    spins = db.query(Spin).filter(Spin.event_id == event.id).all()
    
    prize_list = []
    total_remaining = 0
    for prize in prizes:
        prize_list.append(PrizeStats(
            name=prize.name,
            total=prize.total_inventory,
            remaining=prize.remaining_inventory,
            weight=prize.weight
        ))
        total_remaining += prize.remaining_inventory
    
    total_spins = len(spins)
    total_wins = sum(1 for s in spins if s.is_prize)

    return InventoryStats(
        prizes=prize_list,
        total_spins=total_spins,
        total_wins=total_wins,
        all_prizes_gone=total_remaining == 0
    )


@app.get("/api/admin/spins", response_model=List[SpinResponse])
def get_spins(limit: int = 50, db: Session = Depends(get_session)):
    """Admin endpoint to view recent spins"""
    event = db.query(Event).filter(Event.slug == DEFAULT_EVENT_SLUG).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    spins = db.query(Spin)\
        .filter(Spin.event_id == event.id)\
        .order_by(Spin.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [
        SpinResponse(
            id=s.id,
            label=s.label,
            is_prize=s.is_prize,
            created_at=s.created_at.isoformat()
        )
        for s in spins
    ]
