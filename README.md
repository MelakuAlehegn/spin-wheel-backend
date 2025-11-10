# Backend Setup

## Installation

1. Install dependencies:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Database Setup

### Option 1: SQLite (Development - Default)
No setup needed! The default `DATABASE_URL` uses SQLite.

### Option 2: PostgreSQL (Production)
1. Install PostgreSQL
2. Create a database:
```sql
CREATE DATABASE spinthewheel;
```
3. Set environment variable:
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/spinthewheel
```
Or create a `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost:5432/spinthewheel
```

## Initialize Database

Run the seed script to create tables and initial data:
```bash
python seed.py
```

This will:
- Create the database tables
- Create a default event
- Add prizes with initial inventory (T-shirt: 30, USB Flash: 30, Cap: 30)
- Set up weights for weighted selection

## Run Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /api/spin` - Spin the wheel
- `GET /api/status` - Check if prizes are available
- `GET /api/admin/inventory` - View inventory stats (admin)
- `GET /api/admin/spins` - View recent spins (admin)

## Admin Dashboard

Access the admin dashboard at: http://localhost:3000/admin

