# Hostel Management & Room Allocation System

Python (standard library only) + SQLite backend with an HTML/JS frontend.

## Run
    python server.py
Open http://localhost:8000  (requires Python 3.8+; no pip install needed).
The database file `hostel.db` is created and seeded automatically on first run.
**Delete `hostel.db` to reset** (required once if you used an older version, because the schema got stricter).

Optional: `PORT=9000 python server.py`, or `HOST=0.0.0.0 python server.py` to open it to other devices on your network
(by default it only listens on your own computer).

## Put your name on it
Open `static/index.html`, find `const AUTHOR={name:'Your Name',prn:'Your PRN'};` near the top of the script and edit it.
It updates the page subtitle and the "Developer" card on the Project tab.

## Structure
- `schema.sql`        – tables, constraints, unique index and triggers (matches the ER diagram)
- `server.py`         – REST API + static file server (validates every input)
- `static/index.html` – frontend (works offline; the ER diagram uses Mermaid if internet is available, otherwise a built-in fallback)

## Database rules enforced in SQL
- Foreign keys on all relationships; `user.student_id` is UNIQUE (student 1 : 0..1 user)
- One active room per student (partial unique index)
- Triggers block allocation to a full room and keep `room.occupied` / `room.status` in sync on allocate and release
- Phone must be exactly 10 digits; names, courses and complaint text cannot be blank

## API
GET  /api/state
POST /api/students | /api/allocations | /api/payments | /api/complaints
POST /api/allocations/<id>/release | /api/payments/<id>/paid | /api/complaints/<id>/advance
Errors return JSON `{"error": "readable message"}` with status 400 (bad input), 404 (not found) or 500 (server fault).
