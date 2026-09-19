# SatQuery-AI Backend

FastAPI backend for the SatQuery-AI platform.

The backend provides APIs for:
- Satellite imagery search
- Satellite image change detection
- Alert generation and management
- Analyst feedback
- Satellite tile metadata
- PostgreSQL/PostGIS database storage

---

## 1. Technologies Used

- Python 3.14
- FastAPI
- Uvicorn
- PostgreSQL 18
- PostGIS
- SQLAlchemy
- Psycopg
- GeoAlchemy2
- Docker

---

## 2. Project Structure

```text
backend/
│
├── main.py
├── database.py
├── models.py
├── seed.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env
└── README.md# SatQuery-AI Backend

FastAPI backend for the SatQuery-AI satellite imagery search and change-detection platform.

## Technologies

- Python 3.14
- FastAPI
- Uvicorn
- PostgreSQL 18
- PostGIS
- SQLAlchemy
- Psycopg
- GeoAlchemy2
- Docker

## Project Structure

```text
backend/
├── main.py
├── database.py
├── models.py
├── seed.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env
└── README.md

Setup

Create and activate virtual environment:

python -m venv venv
.\venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Configure the .env file with the PostgreSQL database URL.

Run Backend
uvicorn main:app --reload

Backend:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

API Endpoints
| Method | Endpoint            | Purpose                          |
| ------ | ------------------- | -------------------------------- |
| GET    | `/`                 | Backend status                   |
| GET    | `/health`           | Health check                     |
| POST   | `/search`           | Satellite imagery search         |
| POST   | `/change-detection` | Detect changes between two tiles |
| GET    | `/alerts`           | Retrieve alerts                  |
| POST   | `/feedback`         | Confirm/Reject an alert          |
| GET    | `/tiles/{tile_id}`  | Retrieve tile metadata           |

Search API
Request
{
  "query": "urban expansion around Tumkur"
}

Endpoint:

POST /search

The current search response uses temporary results and will be connected to the RemoteCLIP/FAISS module.

Change Detection API
Request
{
  "tile_id_t1": "TILE-001",
  "tile_id_t2": "TILE-003"
}

Endpoint:

POST /change-detection

The API stores the change-detection result and creates an alert when a change is detected.

Feedback API
Request
{
  "alert_id": "ALT-TILE-003",
  "action": "confirm",
  "comment": "Verified as actual construction"
}

Endpoint:

POST /feedback

Supported actions:

confirm
reject
Database

Database:

satquery_db

PostgreSQL 18 with PostGIS.

Tables:

satellite_tiles
alerts
change_detections
feedback
Architecture
React Frontend
      |
      v
FastAPI Backend
      |
      +---- Semantic Retrieval
      |
      +---- Change Detection
      |
      v
PostgreSQL + PostGIS
      |
      v
Alerts / Feedback
Team Integration

Frontend communicates with FastAPI through REST APIs.

ML modules will be connected to:

POST /search
POST /change-detection

The backend stores results and exposes them through:

GET /alerts
GET /tiles/{tile_id}
POST /feedback
Current Status
Completed
FastAPI backend
REST APIs
Swagger documentation
PostgreSQL
PostGIS
SQLAlchemy
Alert storage
Change detection storage
Feedback storage
CORS
Docker configuration
Pending
RemoteCLIP/FAISS integration
Actual change detection model integration
React frontend integration
End-to-end integration testing
Security

Do not commit .env to GitHub.

Database credentials must remain private.

**This shorter version is enough for the hackathon.** The **API Endpoints + Team Integration** sections are the most important for tomorrow's coordination.