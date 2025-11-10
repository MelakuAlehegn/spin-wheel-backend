"""Reset script to clear all spins and sessions, restore inventory"""
from database import SessionLocal, create_db_and_tables
from models import Event, Prize, Session, Spin

INVENTORY = {
    "T-shirt": 30,
    "USB Flash": 30,
    "Cap": 30,
}


def reset():
    create_db_and_tables()
    
    db = SessionLocal()
    try:
        # Get default event
        event = db.query(Event).filter(Event.slug == "default").first()
        if not event:
            print("Event not found. Run seed.py first.")
            return
        
        # Delete all spins
        spin_count = db.query(Spin).filter(Spin.event_id == event.id).delete()
        print(f"Deleted {spin_count} spin records")
        
        # Delete all sessions
        session_count = db.query(Session).filter(Session.event_id == event.id).delete()
        print(f"Deleted {session_count} session records")
        
        # Reset prize inventory
        prizes = db.query(Prize).filter(Prize.event_id == event.id).all()
        for prize in prizes:
            if prize.name in INVENTORY:
                prize.remaining_inventory = INVENTORY[prize.name]
                db.add(prize)
                print(f"Reset {prize.name}: {INVENTORY[prize.name]} remaining")
        
        db.commit()
        print("\n✅ Database reset complete! You can now spin again.")
        print("(Clear your browser cookies to get a new session)")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("This will delete all spins and sessions. Continue? (yes/no): ")
    if confirm.lower() == "yes":
        reset()
    else:
        print("Reset cancelled.")

