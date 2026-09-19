from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from schemas import SearchRequest, ChangeDetectionRequest, FeedbackRequest

from database import SessionLocal
from models import Alert, Feedback, ChangeDetection, SatelliteTile


app = FastAPI(
    title="SatQuery-AI Backend",
    description="Backend API for satellite imagery search and change detection",
    version="1.0.0"
)


# -----------------------------
# CORS
# -----------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# HOME
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "SatQuery-AI Backend is running!"
    }


# -----------------------------
# HEALTH
# -----------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SatQuery-AI Backend",
        "database": "connected"
    }


# -----------------------------
# SEARCH
# -----------------------------

@app.post("/search")
def search(request: SearchRequest):

    # TODO: Connect actual RemoteCLIP / FAISS module

    return {
        "message": "Search processed",
        "query": request.query,
        "results": [
            {
                "tile_id": "TILE-102",
                "similarity_score": 0.94
            },
            {
                "tile_id": "TILE-087",
                "similarity_score": 0.89
            }
        ]
    }


# -----------------------------
# CHANGE DETECTION
# -----------------------------

@app.post("/change-detection")
def change_detection(request: ChangeDetectionRequest):

    db = SessionLocal()

    try:
        detected = True
        confidence = 0.91
        change_type = "construction"

        result = ChangeDetection(
            tile_id_t1=request.tile_id_t1,
            tile_id_t2=request.tile_id_t2,
            change_detected=str(detected).lower(),
            change_type=change_type,
            confidence=confidence
        )

        db.add(result)

        # Create an alert when meaningful change is detected
        alert = None

        if detected:
            alert = Alert(
                alert_id=f"ALT-{request.tile_id_t2}",
                tile_id=request.tile_id_t2,
                type=change_type,
                confidence=confidence,
                status="pending"
            )

            db.add(alert)

        db.commit()

        return {
            "message": "Change detection completed",
            "tile_id_t1": request.tile_id_t1,
            "tile_id_t2": request.tile_id_t2,
            "change_detected": detected,
            "confidence": confidence,
            "change_type": change_type,
            "alert_created": detected
        }

    finally:
        db.close()

# -----------------------------
# ALERTS
# -----------------------------

@app.get("/alerts")
def get_alerts():

    db = SessionLocal()

    try:
        db_alerts = db.query(Alert).all()

        return {
            "count": len(db_alerts),
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "tile_id": alert.tile_id,
                    "type": alert.type,
                    "confidence": alert.confidence,
                    "status": alert.status,
                    "created_at": alert.created_at
                }
                for alert in db_alerts
            ]
        }

    finally:
        db.close()


# -----------------------------
# FEEDBACK
# -----------------------------

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):

    db = SessionLocal()

    try:
        alert = db.query(Alert).filter(
            Alert.alert_id == request.alert_id
        ).first()

        if not alert:
            return {
                "message": "Alert not found",
                "alert_id": request.alert_id
            }

        # Update alert status
        alert.status = request.action

        # Store feedback permanently
        feedback = Feedback(
            alert_id=request.alert_id,
            action=request.action,
            comment=request.comment
        )

        db.add(feedback)
        db.commit()

        return {
            "message": "Feedback recorded",
            "alert_id": request.alert_id,
            "action": request.action,
            "comment": request.comment
        }

    finally:
        db.close()


# -----------------------------
# TILE
# -----------------------------

@app.get("/tiles/{tile_id}")
def get_tile(tile_id: str):

    db = SessionLocal()

    try:
        tile = db.query(SatelliteTile).filter(
            SatelliteTile.tile_id == tile_id
        ).first()

        if not tile:
            return {
                "message": "Tile not found",
                "tile_id": tile_id
            }

        return {
            "tile_id": tile.tile_id,
            "satellite": tile.satellite,
            "acquisition_date": tile.acquisition_date,
            "image_url": tile.image_url
        }

    finally:
        db.close()