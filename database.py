import sqlite3
import json
import os
import secrets
import hashlib
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "hotel.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str) -> str:
    salt = "coastal_palace_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode('utf-8')).hexdigest()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Rooms table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT NOT NULL UNIQUE,
        room_name TEXT NOT NULL,
        room_type TEXT NOT NULL,
        description TEXT NOT NULL,
        price_per_night REAL NOT NULL,
        bed_type TEXT NOT NULL,
        maximum_guests INTEGER NOT NULL DEFAULT 2,
        amenities TEXT NOT NULL,
        photos TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('AVAILABLE', 'OCCUPIED', 'MAINTENANCE', 'BLOCKED')),
        feature TEXT DEFAULT '',
        cancellation TEXT DEFAULT 'Free cancellation',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        booking_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        email TEXT NOT NULL,
        room_id INTEGER NOT NULL,
        check_in TEXT NOT NULL,
        check_out TEXT NOT NULL,
        adults INTEGER NOT NULL DEFAULT 1,
        children INTEGER NOT NULL DEFAULT 0,
        price_per_night REAL NOT NULL,
        number_of_nights INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        booking_status TEXT NOT NULL CHECK(booking_status IN ('PENDING CONFIRMATION', 'CONFIRMED', 'CANCELLED', 'COMPLETED')),
        special_requests TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE RESTRICT
    )
    """)

    # Index for fast booking date overlap queries
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_bookings_dates ON bookings (room_id, check_in, check_out, booking_status)
    """)

    # Feedback table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        contact TEXT DEFAULT '',
        booking_id TEXT DEFAULT '',
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        message TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('PENDING', 'APPROVED', 'HIDDEN')),
        created_at TEXT NOT NULL
    )
    """)

    # Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Seed default settings
    default_settings = {
        "hotel_name": "HOTEL COASTAL PALACE",
        "tagline": "Comfortable stays and coastal hospitality",
        "address": "Pandubettu, Kalmadi, Mudanidambur, Karnataka 576106",
        "official_phone": "+91 94801 88990",
        "official_email": "reservations@hotelcoastalpalace.com",
        "hotel_description": "Welcome to Hotel Coastal Palace, your premier hospitality destination in Pandubettu, Kalmadi, Mudanidambur. Situated in the vibrant coastal region near Malpe, we offer elegant rooms, warm coastal hospitality, and exquisite dining with both pure vegetarian delicacies and authentic coastal seafood.",
        "cancellation_policy": "Free cancellation available up to 24 hours prior to check-in. No advance cancellation penalty.",
        "checkin_time": "12:00 PM",
        "checkout_time": "11:00 AM",
        "map_embed_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3882.880562621934!2d74.7214!3d13.3442!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTPCsDIwJzM5LjEiTiA3NMKwNDMnMTcuMCJF!5e0!3m2!1sen!2sin!4v1700000000000",
        "map_directions_url": "https://www.google.com/maps/dir/?api=1&destination=Pandubettu,+Kalmadi,+Mudanidambur,+Karnataka+576106",
        "admin_username": "admin",
        "admin_password_hash": hash_password("coastal2026!")
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Seed exact 3 initial rooms if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM rooms")
    room_count = cursor.fetchone()["count"]

    if room_count == 0:
        now = datetime.now().isoformat()
        initial_rooms = [
            (
                "101",
                "Standard Double Room",
                "standard",
                "Spacious air-conditioned room tailored for relaxed living. Features an ultra-comfortable double bed, wooden headboard detailing, warm ambient lighting, modern en-suite bathroom with 24/7 hot water, flat-screen TV, and high-speed Wi-Fi.",
                3213.0,
                "1 Double Bed",
                2,
                json.dumps(["Free Wi-Fi", "1 Double Bed", "Air Conditioning", "Flat-screen TV", "Attached Private Bathroom", "24/7 Hot Water", "Daily Housekeeping", "Wardrobe"]),
                json.dumps(["/static/images/rooms/standard_double_1.jpg", "/static/images/rooms/standard_double_2.jpg"]),
                "AVAILABLE",
                "",
                "Free cancellation",
                now,
                now
            ),
            (
                "102",
                "Deluxe Room",
                "deluxe",
                "Elegantly appointed Deluxe Room boasting a private balcony with refreshing coastal breezes. Furnished with a plush double bed, royal blue accents, climate control, tea/coffee maker, premium bath amenities, and high-speed Wi-Fi.",
                3927.0,
                "1 Double Bed",
                2,
                json.dumps(["Balcony", "Free Wi-Fi", "1 Double Bed", "Air Conditioning", "Smart TV", "Private Modern Bathroom", "Electric Kettle & Tea Setup", "24/7 Hot Water", "Work Desk"]),
                json.dumps(["/static/images/rooms/deluxe_1.jpg", "/static/images/rooms/deluxe_2.jpg"]),
                "AVAILABLE",
                "Balcony",
                "Free cancellation",
                now,
                now
            ),
            (
                "103",
                "Superior Double Room",
                "superior",
                "Our premier Superior Double Room offers expansive square footage, rich textured paneling, and an expansive private balcony. Designed with superior luxury bedding, dedicated lounge seating, premium fixtures, and top-tier guest amenities.",
                6426.0,
                "1 Double Bed",
                2,
                json.dumps(["Balcony", "Free Wi-Fi", "1 Double Bed", "Split Air Conditioning", "Lounge Seating", "Large Smart TV", "Luxury Bathroom with Rain Shower", "Coffee / Tea Station", "Complimentary Bottled Water"]),
                json.dumps(["/static/images/rooms/superior_double_1.jpg", "/static/images/rooms/superior_double_2.jpg"]),
                "AVAILABLE",
                "Balcony",
                "Free cancellation",
                now,
                now
            )
        ]

        cursor.executemany("""
        INSERT INTO rooms (
            room_number, room_name, room_type, description,
            price_per_night, bed_type, maximum_guests, amenities,
            photos, status, feature, cancellation, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_rooms)

    # Seed feedback if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM feedback")
    if cursor.fetchone()["count"] == 0:
        initial_feedback = [
            ("Suresh Shetty", "+91 98451 12340", "CPB-1018", 5, "Outstanding hospitality! The rooms were spotless, AC was great, and having Coastal Flavours seafood right downstairs was a dream come true.", "APPROVED", "2026-09-18T14:30:00"),
            ("Pooja Hegde", "pooja.hegde@example.com", "CPB-1044", 5, "We booked the Deluxe Room with balcony. Very clean, prompt service, and Krishna Swaad breakfast (idli vada & filter coffee) was superb.", "APPROVED", "2026-09-22T09:15:00"),
            ("Rohit Nayak", "+91 97410 88219", "CPB-1082", 5, "Convenient location near Malpe beach and Kalmadi church. Comfortable beds, helpful staff, and zero booking hassle.", "APPROVED", "2026-09-25T19:45:00")
        ]
        cursor.executemany("""
        INSERT INTO feedback (customer_name, contact, booking_id, rating, message, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, initial_feedback)

    conn.commit()
    conn.close()

# --- Room Functions ---

def get_all_rooms(include_all_statuses=True):
    conn = get_db_connection()
    if include_all_statuses:
        cursor = conn.execute("SELECT * FROM rooms ORDER BY room_id ASC")
    else:
        cursor = conn.execute("SELECT * FROM rooms WHERE status = 'AVAILABLE' ORDER BY room_id ASC")
    rows = cursor.fetchall()
    rooms = []
    for r in rows:
        room = dict(r)
        room["amenities"] = json.loads(room["amenities"])
        room["photos"] = json.loads(room["photos"])
        rooms.append(room)
    conn.close()
    return rooms

def get_room_by_id(room_id):
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    room = dict(r)
    room["amenities"] = json.loads(room["amenities"])
    room["photos"] = json.loads(room["photos"])
    return room

def check_room_availability(check_in_str: str, check_out_str: str, guests: int = 1):
    """
    Checks room availability for the requested date window.
    Rule 47:
    A room is unavailable when an existing active booking overlaps the customer's requested date range.
    Overlap condition: (existing.check_in < requested_check_out) AND (existing.check_out > requested_check_in).
    Statuses that block a room: 'PENDING CONFIRMATION', 'CONFIRMED'.
    Also checks room manual status == 'AVAILABLE' and room.maximum_guests >= guests.
    """
    conn = get_db_connection()
    query = """
    SELECT r.* FROM rooms r
    WHERE r.status = 'AVAILABLE'
      AND r.maximum_guests >= ?
      AND r.room_id NOT IN (
          SELECT b.room_id FROM bookings b
          WHERE b.booking_status IN ('PENDING CONFIRMATION', 'CONFIRMED')
            AND b.check_in < ?
            AND b.check_out > ?
      )
    ORDER BY r.price_per_night ASC
    """
    cursor = conn.execute(query, (guests, check_out_str, check_in_str))
    rows = cursor.fetchall()
    available_rooms = []
    for r in rows:
        room = dict(r)
        room["amenities"] = json.loads(room["amenities"])
        room["photos"] = json.loads(room["photos"])
        available_rooms.append(room)
    conn.close()
    return available_rooms

def is_room_available_for_dates(room_id: int, check_in_str: str, check_out_str: str, conn_transaction=None):
    """
    Checks if a specific room is available for given dates, can run inside an active transaction.
    """
    close_at_end = False
    if conn_transaction is None:
        conn = get_db_connection()
        close_at_end = True
    else:
        conn = conn_transaction

    # 1. Check room status
    cursor = conn.execute("SELECT status FROM rooms WHERE room_id = ?", (room_id,))
    r = cursor.fetchone()
    if not r or r["status"] != "AVAILABLE":
        if close_at_end: conn.close()
        return False, "Room is currently not available for bookings."

    # 2. Check overlapping bookings
    cursor = conn.execute("""
        SELECT COUNT(*) as conflict_count FROM bookings
        WHERE room_id = ?
          AND booking_status IN ('PENDING CONFIRMATION', 'CONFIRMED')
          AND check_in < ?
          AND check_out > ?
    """, (room_id, check_out_str, check_in_str))
    conflict = cursor.fetchone()["conflict_count"]
    if close_at_end: conn.close()

    if conflict > 0:
        return False, "Sorry, this room is no longer available for the selected dates. Please choose another room."
    return True, ""

# --- Booking Functions ---

def create_booking(customer_name, mobile, email, room_id, check_in_str, check_out_str, adults, children, special_requests=""):
    """
    Creates a booking using a database transaction with double booking protection.
    """
    # Validate date order
    try:
        d_in = date.fromisoformat(check_in_str)
        d_out = date.fromisoformat(check_out_str)
    except Exception:
        return None, "Invalid date format. Expected YYYY-MM-DD."

    if d_out <= d_in:
        return None, "Please select a check-out date after your check-in date."

    nights = (d_out - d_in).days
    if nights <= 0:
        return None, "Stay must be at least 1 night."

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE TRANSACTION")

        # 1. Fetch Room
        cursor.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,))
        room = cursor.fetchone()
        if not room:
            conn.rollback()
            conn.close()
            return None, "Selected room does not exist."

        if room["status"] != "AVAILABLE":
            conn.rollback()
            conn.close()
            return None, f"Room {room['room_number']} is currently marked as {room['status']}. Please choose another room."

        total_guests = adults + children
        if adults < 1:
            conn.rollback()
            conn.close()
            return None, "At least 1 adult guest is required."

        if total_guests > room["maximum_guests"]:
            conn.rollback()
            conn.close()
            return None, f"Maximum capacity for {room['room_name']} is {room['maximum_guests']} guests."

        # 2. Re-verify date collision inside transaction
        cursor.execute("""
            SELECT booking_id FROM bookings
            WHERE room_id = ?
              AND booking_status IN ('PENDING CONFIRMATION', 'CONFIRMED')
              AND check_in < ?
              AND check_out > ?
        """, (room_id, check_out_str, check_in_str))
        existing = cursor.fetchone()
        if existing:
            conn.rollback()
            conn.close()
            return None, "Sorry, this room is no longer available for the selected dates. Please choose another room."

        # 3. Generate Booking ID
        booking_id = f"CPB-{secrets.randbelow(89999) + 10000}"
        price_per_night = float(room["price_per_night"])
        total_amount = round(price_per_night * nights, 2)
        now = datetime.now().isoformat()

        cursor.execute("""
        INSERT INTO bookings (
            booking_id, customer_name, mobile, email, room_id,
            check_in, check_out, adults, children, price_per_night,
            number_of_nights, total_amount, booking_status, special_requests,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            booking_id, customer_name.strip(), mobile.strip(), email.strip(),
            room_id, check_in_str, check_out_str, adults, children,
            price_per_night, nights, total_amount, 'PENDING CONFIRMATION',
            special_requests.strip(), now, now
        ))

        conn.commit()
        conn.close()

        booking_data = {
            "booking_id": booking_id,
            "customer_name": customer_name,
            "mobile": mobile,
            "email": email,
            "room_id": room_id,
            "room_name": room["room_name"],
            "room_number": room["room_number"],
            "check_in": check_in_str,
            "check_out": check_out_str,
            "adults": adults,
            "children": children,
            "price_per_night": price_per_night,
            "number_of_nights": nights,
            "total_amount": total_amount,
            "booking_status": "PENDING CONFIRMATION",
            "created_at": now
        }
        return booking_data, ""
    except Exception as e:
        conn.rollback()
        conn.close()
        return None, f"Database transaction error: {str(e)}"

def get_booking_by_id(booking_id):
    conn = get_db_connection()
    cursor = conn.execute("""
    SELECT b.*, r.room_name, r.room_number, r.room_type, r.photos
    FROM bookings b
    JOIN rooms r ON b.room_id = r.room_id
    WHERE b.booking_id = ?
    """, (booking_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    b = dict(row)
    b["photos"] = json.loads(b["photos"])
    return b

def get_all_bookings(search_query="", status_filter="", date_filter=""):
    conn = get_db_connection()
    query = """
    SELECT b.*, r.room_name, r.room_number, r.room_type
    FROM bookings b
    JOIN rooms r ON b.room_id = r.room_id
    WHERE 1=1
    """
    params = []

    if status_filter:
        query += " AND b.booking_status = ?"
        params.append(status_filter)

    if date_filter:
        query += " AND (b.check_in <= ? AND b.check_out >= ?)"
        params.extend([date_filter, date_filter])

    if search_query:
        query += " AND (b.booking_id LIKE ? OR b.customer_name LIKE ? OR b.mobile LIKE ? OR b.email LIKE ? OR r.room_number LIKE ?)"
        like_p = f"%{search_query}%"
        params.extend([like_p, like_p, like_p, like_p, like_p])

    query += " ORDER BY b.created_at DESC"
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    bookings = [dict(r) for r in rows]
    conn.close()
    return bookings

def update_booking_status(booking_id: str, new_status: str):
    valid_statuses = ['PENDING CONFIRMATION', 'CONFIRMED', 'CANCELLED', 'COMPLETED']
    if new_status not in valid_statuses:
        return False, f"Invalid status: {new_status}"

    conn = get_db_connection()
    cursor = conn.cursor()

    # If confirming, ensure no conflict exists with another confirmed booking
    if new_status == 'CONFIRMED':
        cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        b = cursor.fetchone()
        if not b:
            conn.close()
            return False, "Booking not found."

        cursor.execute("""
            SELECT booking_id FROM bookings
            WHERE room_id = ?
              AND booking_id != ?
              AND booking_status = 'CONFIRMED'
              AND check_in < ?
              AND check_out > ?
        """, (b["room_id"], booking_id, b["check_out"], b["check_in"]))
        conflict = cursor.fetchone()
        if conflict:
            conn.close()
            return False, f"Cannot confirm: Overlaps with confirmed booking {conflict['booking_id']}."

    now = datetime.now().isoformat()
    cursor.execute("""
    UPDATE bookings SET booking_status = ?, updated_at = ? WHERE booking_id = ?
    """, (new_status, now, booking_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0, ""

# --- Admin Room CRUD & Status Management ---

def add_room(room_number, room_name, room_type, description, price_per_night, bed_type, maximum_guests, amenities_list, photos_list, status="AVAILABLE", feature="", cancellation="Free cancellation"):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute("""
        INSERT INTO rooms (
            room_number, room_name, room_type, description,
            price_per_night, bed_type, maximum_guests, amenities,
            photos, status, feature, cancellation, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            room_number.strip(), room_name.strip(), room_type.strip(), description.strip(),
            float(price_per_night), bed_type.strip(), int(maximum_guests),
            json.dumps(amenities_list), json.dumps(photos_list),
            status, feature.strip(), cancellation.strip(), now, now
        ))
        room_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return room_id, ""
    except sqlite3.IntegrityError:
        conn.close()
        return None, f"Room number '{room_number}' already exists."
    except Exception as e:
        conn.close()
        return None, str(e)

def update_room(room_id, room_number, room_name, room_type, description, price_per_night, bed_type, maximum_guests, amenities_list, photos_list, status, feature="", cancellation="Free cancellation"):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    try:
        cursor.execute("""
        UPDATE rooms SET
            room_number = ?, room_name = ?, room_type = ?, description = ?,
            price_per_night = ?, bed_type = ?, maximum_guests = ?, amenities = ?,
            photos = ?, status = ?, feature = ?, cancellation = ?, updated_at = ?
        WHERE room_id = ?
        """, (
            room_number.strip(), room_name.strip(), room_type.strip(), description.strip(),
            float(price_per_night), bed_type.strip(), int(maximum_guests),
            json.dumps(amenities_list), json.dumps(photos_list),
            status, feature.strip(), cancellation.strip(), now, room_id
        ))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        if affected == 0:
            return False, "Room not found."
        return True, ""
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"Room number '{room_number}' already exists on another room."
    except Exception as e:
        conn.close()
        return False, str(e)

def update_room_status(room_id: int, new_status: str):
    valid_statuses = ['AVAILABLE', 'OCCUPIED', 'MAINTENANCE', 'BLOCKED']
    if new_status not in valid_statuses:
        return False, f"Invalid status: {new_status}"
    conn = get_db_connection()
    now = datetime.now().isoformat()
    cursor = conn.execute("UPDATE rooms SET status = ?, updated_at = ? WHERE room_id = ?", (new_status, now, room_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0, ""

def update_room_price(room_id: int, new_price: float):
    if new_price <= 0:
        return False, "Price must be greater than 0."
    conn = get_db_connection()
    now = datetime.now().isoformat()
    cursor = conn.execute("UPDATE rooms SET price_per_night = ?, updated_at = ? WHERE room_id = ?", (new_price, now, room_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0, ""

def delete_room(room_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if there are active bookings
    cursor.execute("""
    SELECT COUNT(*) as count FROM bookings WHERE room_id = ? AND booking_status IN ('PENDING CONFIRMATION', 'CONFIRMED')
    """, (room_id,))
    if cursor.fetchone()["count"] > 0:
        conn.close()
        return False, "Cannot delete room with active pending or confirmed bookings. Please cancel or complete them first."

    try:
        cursor.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0, ""
    except Exception as e:
        conn.close()
        return False, str(e)

# --- Feedback Functions ---

def create_feedback(customer_name, contact, booking_id, rating, message):
    if rating < 1 or rating > 5:
        return None, "Rating must be between 1 and 5."
    if not customer_name.strip() or not message.strip():
        return None, "Customer name and message are required."

    conn = get_db_connection()
    now = datetime.now().isoformat()
    cursor = conn.execute("""
    INSERT INTO feedback (customer_name, contact, booking_id, rating, message, status, created_at)
    VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
    """, (customer_name.strip(), contact.strip(), booking_id.strip(), rating, message.strip(), now))
    fb_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return fb_id, ""

def get_approved_feedback():
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM feedback WHERE status = 'APPROVED' ORDER BY created_at DESC")
    rows = cursor.fetchall()
    feedback = [dict(r) for r in rows]
    conn.close()
    return feedback

def get_all_feedback():
    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC")
    rows = cursor.fetchall()
    feedback = [dict(r) for r in rows]
    conn.close()
    return feedback

def update_feedback_status(feedback_id: int, new_status: str):
    if new_status not in ['PENDING', 'APPROVED', 'HIDDEN']:
        return False, "Invalid status"
    conn = get_db_connection()
    cursor = conn.execute("UPDATE feedback SET status = ? WHERE feedback_id = ?", (new_status, feedback_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0, ""

def delete_feedback(feedback_id: int):
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM feedback WHERE feedback_id = ?", (feedback_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0, ""

# --- Settings & Metrics Functions ---

def get_settings():
    conn = get_db_connection()
    cursor = conn.execute("SELECT key, value FROM settings")
    settings = {r["key"]: r["value"] for r in cursor.fetchall()}
    conn.close()
    return settings

def update_settings(new_settings: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    for k, v in new_settings.items():
        if k == "admin_password" and v:
            cursor.execute("UPDATE settings SET value = ? WHERE key = 'admin_password_hash'", (hash_password(v),))
        elif k != "admin_password":
            cursor.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (k, str(v)))
    conn.commit()
    conn.close()
    return True

def get_dashboard_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Room stats
    cursor.execute("SELECT COUNT(*) as total FROM rooms")
    total_rooms = cursor.fetchone()["total"]

    cursor.execute("SELECT status, COUNT(*) as count FROM rooms GROUP BY status")
    room_status_counts = {r["status"]: r["count"] for r in cursor.fetchall()}

    # Booking stats
    cursor.execute("SELECT booking_status, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total_revenue FROM bookings GROUP BY booking_status")
    booking_counts = {r["booking_status"]: {"count": r["count"], "revenue": r["total_revenue"]} for r in cursor.fetchall()}

    # Feedback stats
    cursor.execute("SELECT status, COUNT(*) as count FROM feedback GROUP BY status")
    feedback_counts = {r["status"]: r["count"] for r in cursor.fetchall()}

    conn.close()

    return {
        "rooms": {
            "total": total_rooms,
            "available": room_status_counts.get("AVAILABLE", 0),
            "occupied": room_status_counts.get("OCCUPIED", 0),
            "maintenance": room_status_counts.get("MAINTENANCE", 0),
            "blocked": room_status_counts.get("BLOCKED", 0)
        },
        "bookings": {
            "pending": booking_counts.get("PENDING CONFIRMATION", {}).get("count", 0),
            "confirmed": booking_counts.get("CONFIRMED", {}).get("count", 0),
            "cancelled": booking_counts.get("CANCELLED", {}).get("count", 0),
            "completed": booking_counts.get("COMPLETED", {}).get("count", 0),
            "total": sum(b.get("count", 0) for b in booking_counts.values()),
            "confirmed_revenue": booking_counts.get("CONFIRMED", {}).get("revenue", 0)
        },
        "feedback": {
            "pending": feedback_counts.get("PENDING", 0),
            "approved": feedback_counts.get("APPROVED", 0),
            "hidden": feedback_counts.get("HIDDEN", 0),
            "total": sum(feedback_counts.values())
        }
    }
