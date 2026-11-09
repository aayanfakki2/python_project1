"""Hostel Management & Room Allocation System - backend (Python standard library only).

Run:  python server.py        ->  http://localhost:8000
Options (environment variables):  PORT=8000   HOST=127.0.0.1  (use HOST=0.0.0.0 to share on your network)
"""
import hashlib, json, math, mimetypes, os, re, sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "hostel.db")
STATIC = os.path.join(BASE, "static")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))


class ApiError(Exception):
    """An error whose message is safe to show to the user."""
    def __init__(self, message, code=400):
        super().__init__(message)
        self.code = code


def conn():
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def init_db():
    c = conn()
    with open(os.path.join(BASE, "schema.sql"), encoding="utf-8") as f:
        c.executescript(f.read())
    # Seed only when the database is empty (so a half-created file is also repaired).
    if c.execute("SELECT COUNT(*) FROM hostel").fetchone()[0] == 0:
        c.executemany("INSERT INTO hostel(hostel_name,location) VALUES (?,?)",
                      [("Aryabhatta Boys Hostel", "North Campus"), ("Sarojini Girls Hostel", "South Campus")])
        for h in (1, 2):
            for f in (1, 2):
                for r in range(1, 5):
                    c.execute("INSERT INTO room(hostel_id,room_no,capacity,floor) VALUES (?,?,?,?)",
                              (h, f"{f}0{r}", 2 if r % 2 else 3, f))
        c.executemany("INSERT INTO student(student_name,course,year_of_study,phone) VALUES (?,?,?,?)", [
            ("Rohan Patil", "B.Tech CSE", 2, "9876500001"), ("Sneha Kulkarni", "B.Tech IT", 3, "9876500002"),
            ("Amit Deshmukh", "BBA", 1, "9876500003"), ("Priya Joshi", "B.Sc Physics", 2, "9876500004"),
            ("Karan Mehta", "B.Tech Mech", 4, "9876500005")])
        c.executemany("INSERT INTO allocation(student_id,room_id) VALUES (?,?)", [(1, 1), (2, 9), (3, 1)])
        c.executemany("INSERT INTO payment(student_id,amount,payment_status) VALUES (?,?,?)",
                      [(1, 45000, "Paid"), (2, 45000, "Paid"), (3, 45000, "Pending")])
        c.executemany("INSERT INTO complaint(student_id,category,complaint_text,status) VALUES (?,?,?,?)",
                      [(1, "Plumbing", "Tap leaking in washroom.", "Open"),
                       (2, "Electrical", "Fan not working.", "In Progress")])
        c.execute("INSERT INTO user(username,password,role) VALUES ('admin',?, 'admin')",
                  (hashlib.sha256(b"admin123").hexdigest(),))
        c.commit()
    c.close()


def rows(c, sql):
    return [dict(r) for r in c.execute(sql)]


def state():
    c = conn()
    try:
        return {
            "hostels": rows(c, "SELECT hostel_id id, hostel_name name, location loc FROM hostel ORDER BY hostel_id"),
            "rooms": rows(c, "SELECT room_id id, hostel_id hid, room_no no, capacity cap, floor, occupied occ, status FROM room ORDER BY hostel_id, room_no"),
            "students": rows(c, "SELECT student_id id, student_name name, course, year_of_study year, phone FROM student ORDER BY student_id"),
            "allocs": rows(c, "SELECT allocation_id id, student_id sid, room_id rid, allocation_date date, release_date rel, status st FROM allocation ORDER BY allocation_id DESC"),
            "pays": rows(c, "SELECT payment_id id, student_id sid, amount amt, payment_date date, payment_status st FROM payment ORDER BY payment_id DESC"),
            "comps": rows(c, "SELECT complaint_id id, student_id sid, category cat, complaint_date date, complaint_text txt, status st FROM complaint ORDER BY complaint_id DESC"),
        }
    finally:
        c.close()


# ---------- input helpers ----------
CATEGORIES = ("Plumbing", "Electrical", "Cleanliness", "Mess", "Security", "Other")
PAY_STATUSES = ("Paid", "Pending", "Failed")


def text(d, key, label, maxlen=500):
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ApiError(f"{label} is required.")
    v = v.strip()
    if len(v) > maxlen:
        raise ApiError(f"{label} is too long (max {maxlen} characters).")
    return v


def integer(d, key, label):
    v = d.get(key)
    if isinstance(v, bool):
        raise ApiError(f"{label} must be a whole number.")
    try:
        if isinstance(v, float) and not v.is_integer():
            raise ValueError
        return int(v)
    except (TypeError, ValueError):
        raise ApiError(f"{label} must be a whole number.")


def exists(c, table, col, val, label):
    if c.execute(f"SELECT 1 FROM {table} WHERE {col}=?", (val,)).fetchone() is None:
        raise ApiError(f"{label} not found.", 404)


# ---------- actions ----------
def add_student(c, d):
    name, course = text(d, "name", "Name", 100), text(d, "course", "Course", 100)
    year = integer(d, "year", "Year")
    if not 1 <= year <= 6:
        raise ApiError("Year must be between 1 and 6.")
    phone = d.get("phone")
    phone = str(phone).strip() if phone is not None else ""
    if not re.fullmatch(r"[0-9]{10}", phone):
        raise ApiError("Phone must be exactly 10 digits.")
    c.execute("INSERT INTO student(student_name,course,year_of_study,phone) VALUES (?,?,?,?)",
              (name, course, year, phone))


def allocate(c, d):
    sid, rid = integer(d, "sid", "Student"), integer(d, "rid", "Room")
    exists(c, "student", "student_id", sid, "Student")
    exists(c, "room", "room_id", rid, "Room")
    c.execute("INSERT INTO allocation(student_id,room_id) VALUES (?,?)", (sid, rid))


def release(c, d, i):
    cur = c.execute("UPDATE allocation SET status='Released', release_date=date('now') "
                    "WHERE allocation_id=? AND status='Active'", (i,))
    if cur.rowcount == 0:
        exists(c, "allocation", "allocation_id", i, "Allocation")
        raise ApiError("This allocation was already released.")


def add_payment(c, d):
    sid = integer(d, "sid", "Student")
    exists(c, "student", "student_id", sid, "Student")
    try:
        amt = float(d.get("amt"))
    except (TypeError, ValueError):
        raise ApiError("Amount must be a number.")
    if not math.isfinite(amt) or amt <= 0:
        raise ApiError("Amount must be greater than zero.")
    if amt > 10_000_000:
        raise ApiError("Amount is too large.")
    st = d.get("st")
    if st not in PAY_STATUSES:
        raise ApiError("Status must be Paid, Pending or Failed.")
    c.execute("INSERT INTO payment(student_id,amount,payment_status) VALUES (?,?,?)", (sid, round(amt, 2), st))


def mark_paid(c, d, i):
    cur = c.execute("UPDATE payment SET payment_status='Paid', payment_date=date('now') "
                    "WHERE payment_id=? AND payment_status!='Paid'", (i,))
    if cur.rowcount == 0:
        exists(c, "payment", "payment_id", i, "Payment")
        raise ApiError("This payment is already marked as paid.")


def add_complaint(c, d):
    sid = integer(d, "sid", "Student")
    exists(c, "student", "student_id", sid, "Student")
    cat = d.get("cat")
    if cat not in CATEGORIES:
        raise ApiError("Please choose a valid category.")
    c.execute("INSERT INTO complaint(student_id,category,complaint_text) VALUES (?,?,?)",
              (sid, cat, text(d, "txt", "Description", 1000)))


def advance(c, d, i):
    cur = c.execute("""UPDATE complaint SET status = CASE status WHEN 'Open' THEN 'In Progress' ELSE 'Resolved' END
                       WHERE complaint_id=? AND status!='Resolved'""", (i,))
    if cur.rowcount == 0:
        exists(c, "complaint", "complaint_id", i, "Complaint")
        raise ApiError("This complaint is already resolved.")


ROUTES = [
    (r"/api/students$", add_student),
    (r"/api/allocations$", allocate),
    (r"/api/allocations/(\d+)/release$", release),
    (r"/api/payments$", add_payment),
    (r"/api/payments/(\d+)/paid$", mark_paid),
    (r"/api/complaints$", add_complaint),
    (r"/api/complaints/(\d+)/advance$", advance),
]


def friendly(e):
    """Turn a database constraint error into a readable message."""
    msg = str(e)
    if "Room is full" in msg:
        return "That room is already full."
    if "ux_one_active_room" in msg or "allocation.student_id" in msg:
        return "That student already has an active room. Release it first."
    if "phone" in msg:
        return "Phone must be exactly 10 digits."
    if "FOREIGN KEY" in msg:
        return "Related record not found."
    return "The database rejected this change: " + msg


class H(BaseHTTPRequestHandler):
    server_version = "HostelApp"

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/api/state":
            try:
                return self.send(200, state())
            except sqlite3.Error as e:
                return self.send(500, {"error": "Database error: " + str(e)})
        if path.startswith("/api/"):
            return self.send(404, {"error": "Not found"})
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        f = os.path.realpath(os.path.join(STATIC, rel))
        if os.path.commonpath([f, os.path.realpath(STATIC)]) != os.path.realpath(STATIC) or not os.path.isfile(f):
            return self.send(404, {"error": "Not found"})
        ctype = mimetypes.guess_type(f)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        with open(f, "rb") as fh:
            self.send(200, fh.read(), ctype)

    def do_POST(self):
        path = urlsplit(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(d, dict):
                raise ValueError
        except ValueError:
            return self.send(400, {"error": "Invalid request body."})
        for pat, fn in ROUTES:
            m = re.match(pat, path)
            if not m:
                continue
            c = conn()
            try:
                fn(c, d, *[int(g) for g in m.groups()])
                c.commit()
                return self.send(200, {"ok": True})
            except ApiError as e:
                c.rollback()
                return self.send(e.code, {"error": str(e)})
            except sqlite3.IntegrityError as e:
                c.rollback()
                return self.send(400, {"error": friendly(e)})
            except sqlite3.Error as e:
                c.rollback()
                return self.send(500, {"error": "Database error: " + str(e)})
            except Exception as e:  # never let a bug kill the connection silently
                c.rollback()
                return self.send(500, {"error": "Server error: " + str(e)})
            finally:
                c.close()
        self.send(404, {"error": "Not found"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    init_db()
    shown = "localhost" if HOST in ("127.0.0.1", "0.0.0.0") else HOST
    print(f"Hostel system running at http://{shown}:{PORT}   (Ctrl+C to stop)")
    try:
        ThreadingHTTPServer((HOST, PORT), H).serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
