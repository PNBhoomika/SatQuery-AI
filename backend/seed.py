from database import SessionLocal
from models import Alert

db = SessionLocal()

alert = Alert(
    alert_id="ALT-001",
    tile_id="TILE-102",
    type="construction",
    confidence=0.92,
    status="pending"
)

db.add(alert)
db.commit()

print("Alert inserted successfully!")

db.close()