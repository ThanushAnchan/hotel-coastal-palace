import urllib.request
import urllib.parse
import json
import http.cookiejar
import sys

BASE_URL = "http://127.0.0.1:5000"

def run_tests():
    # Setup cookie jar for session maintenance
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Clean up test bookings to ensure idempotency
    import database
    conn = database.get_db_connection()
    conn.execute("DELETE FROM bookings WHERE customer_name IN ('Ramesh Kamath', 'Test Customer')")
    conn.execute("UPDATE rooms SET status = 'AVAILABLE', price_per_night = CASE room_id WHEN 1 THEN 3213.0 WHEN 2 THEN 3927.0 WHEN 3 THEN 6426.0 END")
    conn.commit()
    conn.close()

    print(">>> STARTING COMPREHENSIVE END-TO-END VERIFICATION <<<\n")

    # TEST 1: Admin logs in & sees 3 initial room types
    print("[TEST 1] Admin logs in...")
    login_data = json.dumps({"username": "admin", "password": "coastal2026!"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=login_data, headers={"Content-Type": "application/json"})
    with opener.open(req) as resp:
        assert resp.status == 200, f"Login failed with status {resp.status}"
        data = json.loads(resp.read().decode('utf-8'))
        assert data.get("success") is True
    print("  -> Admin logged in successfully.")

    req = urllib.request.Request(f"{BASE_URL}/api/admin/rooms")
    with opener.open(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        rooms = data.get("rooms", [])
        assert len(rooms) >= 3, f"Expected at least 3 initial rooms, got {len(rooms)}"
        room_names = [r["room_name"] for r in rooms]
        assert "Standard Double Room" in room_names
        assert "Deluxe Room" in room_names
        assert "Superior Double Room" in room_names
    print(f"  -> Verified 3 initial room types: {room_names}")

    # TEST 2: Customer checks availability for 2026-09-29 to 2026-09-30, 2 adults
    print("\n[TEST 2] Customer checks availability (2026-09-29 to 2026-09-30, 2 Adults)...")
    url = f"{BASE_URL}/api/availability?check_in=2026-09-29&check_out=2026-09-30&guests=2"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        available_rooms = data.get("rooms", [])
        assert len(available_rooms) == 3, f"Expected 3 available rooms, found {len(available_rooms)}"
    print(f"  -> Verified availability search returned {len(available_rooms)} available rooms.")

    # Find Deluxe Room ID
    deluxe_room = next(r for r in available_rooms if "Deluxe" in r["room_name"])
    deluxe_id = deluxe_room["room_id"]

    # TEST 3 & 4: Customer selects Deluxe Room & submits booking request -> PENDING CONFIRMATION
    print(f"\n[TEST 3 & 4] Customer books Deluxe Room (ID: {deluxe_id})...")
    booking_payload = json.dumps({
        "customer_name": "Ramesh Kamath",
        "mobile": "+91 98451 99887",
        "email": "ramesh.kamath@example.com",
        "room_id": deluxe_id,
        "check_in": "2026-09-29",
        "check_out": "2026-09-30",
        "adults": 2,
        "children": 0,
        "special_requests": "Upper floor if available"
    }).encode('utf-8')

    req = urllib.request.Request(f"{BASE_URL}/api/bookings", data=booking_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        data = json.loads(resp.read().decode('utf-8'))
        booking = data["booking"]
        booking_id = booking["booking_id"]
        assert booking["booking_status"] == "PENDING CONFIRMATION"
        assert booking["number_of_nights"] == 1
        assert booking["total_amount"] == 3927.0
    print(f"  -> Created Booking ID: {booking_id} with status: {booking['booking_status']} for ₹{booking['total_amount']}.")

    # TEST 5: Admin sees the new booking
    print(f"\n[TEST 5] Admin views bookings list to verify {booking_id}...")
    req = urllib.request.Request(f"{BASE_URL}/api/admin/bookings?search={booking_id}")
    with opener.open(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        admin_bookings = data.get("bookings", [])
        assert any(b["booking_id"] == booking_id for b in admin_bookings), f"Booking {booking_id} not found in admin list"
    print(f"  -> Admin confirmed visibility of booking {booking_id}.")

    # TEST 6: Admin confirms the booking
    print(f"\n[TEST 6] Admin confirms booking {booking_id}...")
    status_payload = json.dumps({"status": "CONFIRMED"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/bookings/{booking_id}/status", data=status_payload, headers={"Content-Type": "application/json"}, method="PATCH")
    with opener.open(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        assert data.get("status") == "CONFIRMED"
    print(f"  -> Booking {booking_id} status updated to CONFIRMED.")

    # TEST 7: Another customer searches the exact same dates -> Deluxe Room must NOT be available!
    print("\n[TEST 7] Double booking check: Customer searches 2026-09-29 to 2026-09-30...")
    url = f"{BASE_URL}/api/availability?check_in=2026-09-29&check_out=2026-09-30&guests=2"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode('utf-8'))
        avail_now = data.get("rooms", [])
        avail_ids = [r["room_id"] for r in avail_now]
        assert deluxe_id not in avail_ids, f"ERROR: Deluxe Room {deluxe_id} should NOT be available, but appeared!"
        assert len(avail_now) == 2, f"Expected 2 rooms available, got {len(avail_now)}"
    print(f"  -> PASS: Deluxe Room is strictly excluded from availability for conflicting dates!")
    print(f"  -> Other rooms remain available: {[r['room_name'] for r in avail_now]}")

    # TEST 7B: Verify checkout day handover works: 2026-09-30 to 2026-10-02 SHOULD allow Deluxe Room!
    print("\n[TEST 7B] Boundary check: Customer searches checkout date 2026-09-30 to 2026-10-02...")
    url = f"{BASE_URL}/api/availability?check_in=2026-09-30&check_out=2026-10-02&guests=2"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        avail_next = data.get("rooms", [])
        avail_next_ids = [r["room_id"] for r in avail_next]
        assert deluxe_id in avail_next_ids, "Deluxe Room should be available starting from checkout day!"
    print("  -> PASS: Room becomes available for subsequent guest starting from checkout date!")

    # TEST 8: Admin manually changes room 101: AVAILABLE -> OCCUPIED
    print("\n[TEST 8] Admin marks Standard Double Room (101) as OCCUPIED (Walk-in guest)...")
    std_room = next(r for r in rooms if r["room_number"] == "101")
    std_id = std_room["room_id"]
    status_payload = json.dumps({"status": "OCCUPIED"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/rooms/{std_id}/status", data=status_payload, headers={"Content-Type": "application/json"}, method="PATCH")
    with opener.open(req) as resp:
        assert resp.status == 200
    # Customer checks room on API
    with urllib.request.urlopen(f"{BASE_URL}/api/rooms/{std_id}") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert data["room"]["status"] == "OCCUPIED"
    print("  -> PASS: Room 101 is now OCCUPIED on customer website ('Currently Unavailable')")

    # TEST 9: Admin changes OCCUPIED -> AVAILABLE (Guest checked out)
    print("\n[TEST 9] Admin checks out walk-in guest: OCCUPIED -> AVAILABLE...")
    status_payload = json.dumps({"status": "AVAILABLE"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/rooms/{std_id}/status", data=status_payload, headers={"Content-Type": "application/json"}, method="PATCH")
    with opener.open(req) as resp:
        assert resp.status == 200
    with urllib.request.urlopen(f"{BASE_URL}/api/rooms/{std_id}") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert data["room"]["status"] == "AVAILABLE"
    print("  -> PASS: Room 101 immediately reflects as AVAILABLE again!")

    # TEST 10: Admin changes room price
    print("\n[TEST 10] Admin edits room price for Standard Double Room: ₹3,213 -> ₹3,450...")
    price_payload = json.dumps({"price_per_night": 3450.0}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/rooms/{std_id}/price", data=price_payload, headers={"Content-Type": "application/json"}, method="PATCH")
    with opener.open(req) as resp:
        assert resp.status == 200
    with urllib.request.urlopen(f"{BASE_URL}/api/rooms/{std_id}") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert data["room"]["price_per_night"] == 3450.0
    print("  -> PASS: Customer website dynamically displays new price: ₹3,450")

    # TEST 11 & 12: Admin updates room photos and description
    print("\n[TEST 11 & 12] Admin updates photos and description...")
    updated_photos = ["/static/images/rooms/standard_double_2.jpg", "/static/images/rooms/standard_double_1.jpg"]
    updated_desc = "Newly refreshed Standard Double Room with enhanced ergonomic workspace, high-speed Wi-Fi, and 24/7 hot water."
    update_payload = json.dumps({
        "room_number": "101",
        "room_name": "Standard Double Room",
        "room_type": "standard",
        "price_per_night": 3450.0,
        "bed_type": "1 Double Bed",
        "maximum_guests": 2,
        "amenities": ["Free Wi-Fi", "1 Double Bed", "Air Conditioning"],
        "photos": updated_photos,
        "status": "AVAILABLE",
        "feature": "",
        "cancellation": "Free cancellation",
        "description": updated_desc
    }).encode('utf-8')

    req = urllib.request.Request(f"{BASE_URL}/api/admin/rooms/{std_id}", data=update_payload, headers={"Content-Type": "application/json"}, method="PUT")
    with opener.open(req) as resp:
        assert resp.status == 200
    with urllib.request.urlopen(f"{BASE_URL}/api/rooms/{std_id}") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert data["room"]["description"] == updated_desc
        assert data["room"]["photos"] == updated_photos
    print("  -> PASS: Updated photos and description reflected on website!")

    # TEST 13: Customer submits feedback -> PENDING in admin
    print("\n[TEST 13] Customer submits new feedback...")
    fb_payload = json.dumps({
        "customer_name": "Ananya Rao",
        "contact": "ananya.rao@example.com",
        "booking_id": booking_id,
        "rating": 5,
        "message": "The fish fry at Coastal Flavours was unforgettable, and our room was so peaceful!"
    }).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/feedback", data=fb_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
    
    # Check in admin
    req = urllib.request.Request(f"{BASE_URL}/api/admin/feedback")
    with opener.open(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        all_fb = data.get("feedback", [])
        ananya_fb = next((f for f in all_fb if f["customer_name"] == "Ananya Rao"), None)
        assert ananya_fb is not None
        assert ananya_fb["status"] == "PENDING"
        ananya_id = ananya_fb["feedback_id"]
    print(f"  -> PASS: Feedback submitted and appears in admin with status: PENDING (ID: {ananya_id})")

    # TEST 14: Admin approves feedback -> appears publicly
    print("\n[TEST 14] Admin approves feedback...")
    req = urllib.request.Request(f"{BASE_URL}/api/admin/feedback/{ananya_id}/status", data=json.dumps({"status": "APPROVED"}).encode('utf-8'), headers={"Content-Type": "application/json"}, method="PATCH")
    with opener.open(req) as resp:
        assert resp.status == 200
    
    with urllib.request.urlopen(f"{BASE_URL}/api/feedback") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        approved_names = [f["customer_name"] for f in data.get("feedback", [])]
        assert "Ananya Rao" in approved_names
    print("  -> PASS: Approved feedback now appears publicly on website!")

    # TEST 15: Admin hides feedback -> disappears from public website
    print("\n[TEST 15] Admin hides feedback...")
    req = urllib.request.Request(f"{BASE_URL}/api/admin/feedback/{ananya_id}/status", data=json.dumps({"status": "HIDDEN"}).encode('utf-8'), headers={"Content-Type": "application/json"}, method="PATCH")
    with opener.open(req) as resp:
        assert resp.status == 200
    
    with urllib.request.urlopen(f"{BASE_URL}/api/feedback") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        approved_names = [f["customer_name"] for f in data.get("feedback", [])]
        assert "Ananya Rao" not in approved_names
    print("  -> PASS: Hidden feedback completely removed from public display!")

    print("\n========================================================")
    print("ALL 15 END-TO-END CRITICAL TESTS PASSED WITH 100% SUCCESS!")
    print("========================================================")

if __name__ == "__main__":
    run_tests()
