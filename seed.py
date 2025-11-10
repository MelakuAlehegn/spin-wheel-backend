"""Seed script to initialize database with default event and prizes"""
from database import engine, create_db_and_tables
from models import Event, Prize
from sqlalchemy.orm import Session

SLICES = [
    "T-shirt",
    "USB Flash",
    "Cap",
    "Arif Try!",
    "Arif Luck Next Time!",
    "Stay Arif!",
]

WEIGHTS = {
    "T-shirt": 3,
    "USB Flash": 3,
    "Cap": 3,
    "Arif Try!": 30,
    "Arif Luck Next Time!": 30,
    "Stay Arif!": 31,
}

INVENTORY = {
    "T-shirt": 30,
    "USB Flash": 30,
    "Cap": 30,
}


def seed():
    create_db_and_tables()
    
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Check if event already exists
        existing = db.query(Event).filter(Event.slug == "default").first()
        if existing:
            print("Event already exists, skipping seed")
            return
        
        # Create default event
        event = Event(name="Default Event", slug="default", active=True)
        db.add(event)
        db.commit()
        db.refresh(event)
        
        # Create prizes
        for label in SLICES:
            prize = Prize(
                event_id=event.id,
                name=label,
                weight=WEIGHTS.get(label, 0),
                total_inventory=INVENTORY.get(label, 0),
                remaining_inventory=INVENTORY.get(label, 0),
            )
            db.add(prize)
        
        db.commit()
        print("Database seeded successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
