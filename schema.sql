PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS hostel (
  hostel_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hostel_name TEXT NOT NULL UNIQUE,
  location TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS room (
  room_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hostel_id INTEGER NOT NULL REFERENCES hostel(hostel_id) ON DELETE CASCADE,
  room_no TEXT NOT NULL,
  capacity INTEGER NOT NULL CHECK (capacity > 0),
  occupied INTEGER NOT NULL DEFAULT 0 CHECK (occupied >= 0),
  floor INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'Available' CHECK (status IN ('Available','Full')),
  UNIQUE (hostel_id, room_no),
  CHECK (occupied <= capacity)
);

CREATE TABLE IF NOT EXISTS student (
  student_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_name TEXT NOT NULL CHECK (length(trim(student_name)) > 0),
  course TEXT NOT NULL CHECK (length(trim(course)) > 0),
  year_of_study INTEGER NOT NULL CHECK (year_of_study BETWEEN 1 AND 6),
  phone TEXT NOT NULL CHECK (length(phone) = 10 AND phone NOT GLOB '*[^0-9]*')
);

CREATE TABLE IF NOT EXISTS user (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER UNIQUE REFERENCES student(student_id) ON DELETE CASCADE,
  username TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('admin','student'))
);

CREATE TABLE IF NOT EXISTS allocation (
  allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL REFERENCES student(student_id),
  room_id INTEGER NOT NULL REFERENCES room(room_id),
  allocation_date TEXT NOT NULL DEFAULT (date('now')),
  release_date TEXT,
  status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active','Released'))
);

CREATE TABLE IF NOT EXISTS payment (
  payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL REFERENCES student(student_id),
  amount REAL NOT NULL CHECK (amount > 0),
  payment_date TEXT NOT NULL DEFAULT (date('now')),
  payment_status TEXT NOT NULL DEFAULT 'Pending' CHECK (payment_status IN ('Paid','Pending','Failed'))
);

CREATE TABLE IF NOT EXISTS complaint (
  complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL REFERENCES student(student_id),
  category TEXT NOT NULL,
  complaint_date TEXT NOT NULL DEFAULT (date('now')),
  complaint_text TEXT NOT NULL CHECK (length(trim(complaint_text)) > 0),
  status TEXT NOT NULL DEFAULT 'Open' CHECK (status IN ('Open','In Progress','Resolved'))
);

-- One active room per student
CREATE UNIQUE INDEX IF NOT EXISTS ux_one_active_room
  ON allocation(student_id) WHERE status = 'Active';

-- Block allocation into a full room
CREATE TRIGGER IF NOT EXISTS trg_alloc_check
BEFORE INSERT ON allocation WHEN NEW.status = 'Active'
BEGIN
  SELECT RAISE(ABORT, 'Room is full')
  WHERE (SELECT occupied >= capacity FROM room WHERE room_id = NEW.room_id);
END;

-- Keep room.occupied / room.status in sync
CREATE TRIGGER IF NOT EXISTS trg_alloc_ins AFTER INSERT ON allocation WHEN NEW.status = 'Active'
BEGIN
  UPDATE room SET occupied = occupied + 1,
    status = CASE WHEN occupied + 1 >= capacity THEN 'Full' ELSE 'Available' END
  WHERE room_id = NEW.room_id;
END;

CREATE TRIGGER IF NOT EXISTS trg_alloc_rel AFTER UPDATE OF status ON allocation
WHEN OLD.status = 'Active' AND NEW.status = 'Released'
BEGIN
  UPDATE room SET occupied = occupied - 1, status = 'Available' WHERE room_id = NEW.room_id;
END;
