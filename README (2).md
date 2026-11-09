# Hostel Management & Room Allocation System

A DBMS mini project: a web app for managing hostel rooms, student allocation, fee payments and complaints.

- **Backend:** Python 3 (standard library only) with a REST API
- **Database:** SQLite, with constraints and triggers enforcing the business rules
- **Frontend:** a single HTML/CSS/JS page (no frameworks, no build step)

No `pip install` and no internet connection are needed to run it.

## Features

- **Dashboard:** total rooms, beds occupied and available, pending payments, open complaints, and occupancy per hostel
- **Rooms:** every room with its hostel, floor, capacity, occupancy and status (Available or Full)
- **Students:** add students and see which room each one has
- **Allocation:** allocate a student to a room, release a room, and view the full allocation history
- **Payments:** record payments (Paid, Pending or Failed) and mark pending ones as paid
- **Complaints:** raise complaints by category and move them from Open to In Progress to Resolved
- **Project tab:** problem statement, ER diagram, relationships table and developer details

## Requirements

- Python 3.8 or newer. Check with `python --version` (use `python3` on Mac or Linux)
- Any modern browser

## Quick start

1. Extract the project fully so you have this folder structure:
   ```
   hostel-app/
   ├── server.py
   ├── schema.sql
   ├── README.md
   └── static/
       └── index.html
   ```
2. Open a terminal **inside the `hostel-app` folder**.
   - Windows: open the folder in File Explorer, click the address bar, type `cmd` and press Enter.
   - Mac/Linux: `cd` into the folder.
3. Start the server:
   ```
   python server.py
   ```
   (Use `py server.py` on Windows if `python` is not found, or `python3 server.py` on Mac/Linux.)
4. You should see: `Hostel system running at http://localhost:8000`
5. Open **http://localhost:8000** in your browser.

Keep the terminal window open while you use the app. Press `Ctrl+C` to stop the server.

> Do not double-click `index.html`. The page needs the server to load its data.

The database file `hostel.db` is created and filled with sample data automatically the first time you run the server.

## Put your name on it

Open `static/index.html`, find this line near the top of the `<script>` section, and edit it:

```js
const AUTHOR={name:'Your Name',prn:'Your PRN'};
```

It updates the page subtitle and the Developer card on the Project tab.

## Configuration

| Setting | Default | Example |
|---|---|---|
| `PORT` | `8000` | Windows: `set PORT=9000` then `python server.py`. Mac/Linux: `PORT=9000 python3 server.py` |
| `HOST` | `127.0.0.1` (this computer only) | `HOST=0.0.0.0` lets other devices on your network open the app |

## Resetting the data

Stop the server, delete `hostel.db`, and start the server again. A fresh database with sample data is created.

## Sample data

On first run the app creates:

- 2 hostels (Aryabhatta Boys Hostel, Sarojini Girls Hostel), each with 8 rooms across 2 floors
- 5 students, 3 allocations, 3 payments and 2 complaints
- 1 admin account (`admin`, password stored as a SHA-256 hash). The app has no login screen yet; the account exists to match the ER diagram.

## Database design

Seven tables: `hostel`, `room`, `student`, `user`, `allocation`, `payment`, `complaint`.

| Relationship | Cardinality |
|---|---|
| Hostel to Room | 1 : N |
| Room to Allocation | 1 : N |
| Student to Allocation | 1 : N |
| Student to Payment | 1 : N |
| Student to Complaint | 1 : N |
| Student to User | 1 : 0..1 |

### Rules enforced by the database itself

- Foreign keys on every relationship
- A student can have only **one active room** at a time (partial unique index)
- A trigger **blocks allocation to a full room**
- Triggers keep `room.occupied` and `room.status` in sync when a room is allocated or released
- Phone numbers must be exactly 10 digits
- Names, courses and complaint text cannot be blank
- Payment amount must be greater than zero; payment, complaint and allocation statuses are restricted to fixed values

## API reference

All request and response bodies are JSON.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/state` | All hostels, rooms, students, allocations, payments and complaints |
| POST | `/api/students` | Add a student: `name`, `course`, `year`, `phone` |
| POST | `/api/allocations` | Allocate a room: `sid`, `rid` |
| POST | `/api/allocations/<id>/release` | Release an allocation |
| POST | `/api/payments` | Record a payment: `sid`, `amt`, `st` |
| POST | `/api/payments/<id>/paid` | Mark a payment as paid |
| POST | `/api/complaints` | Raise a complaint: `sid`, `cat`, `txt` |
| POST | `/api/complaints/<id>/advance` | Move a complaint to the next status |

Success returns `{"ok": true}`. Failures return `{"error": "readable message"}` with status 400 (invalid input), 404 (record not found) or 500 (server fault).

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised | Try `py server.py` (Windows) or `python3 server.py` (Mac/Linux). Install Python from python.org and tick "Add Python to PATH" |
| Browser shows "Cannot reach the backend" | The server is not running. Start it with `python server.py` and keep the terminal open. Open the `http://localhost:8000` address, not the HTML file |
| "Address already in use" | Another program is using port 8000. Set a different `PORT` (see Configuration) |
| `schema.sql` not found | You are running it from inside the zip. Extract all files first |
| Errors after updating the code | Delete `hostel.db` so the new schema is applied |
| ER diagram shows boxes instead of a diagram | Expected when offline; the diagram library loads from the internet. The same information is shown as entity boxes |

## Project structure

| File | Purpose |
|---|---|
| `server.py` | HTTP server, REST API and input validation |
| `schema.sql` | Tables, constraints, unique index and triggers |
| `static/index.html` | The whole frontend |
| `hostel.db` | SQLite database (created on first run) |

## Author

Replace this line with your name and PRN.
