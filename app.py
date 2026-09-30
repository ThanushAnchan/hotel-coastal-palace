import os
import secrets
import json
import logging
import tempfile
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import database

logger = logging.getLogger("hotel_coastal_palace")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "coastal-palace-secret-key-99238472918471")

# Vercel / Serverless environment detection
IS_VERCEL = bool(
    os.environ.get("VERCEL")
    or os.environ.get("VERCEL_ENV")
    or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
)

# Upload directory configuration:
# 1. Do NOT create or write upload directories inside static/, templates/, or the deployed project directory.
# 2. If temporary uploads are required, use /tmp/uploads on Vercel.
# 3. Do NOT call os.makedirs() at import time to prevent Read-only file system errors on Vercel.
if IS_VERCEL:
    app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads")
else:
    app.config["UPLOAD_FOLDER"] = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(tempfile.gettempdir(), "hotel_uploads")
    )

# Non-blocking database initialization at import time (logs warning on cold start if database is not reachable yet)
try:
    database.init_db()
except Exception as e:
    logger.warning("Database startup initialization deferred (will initialize on request): %s", e)

_db_initialized = False

@app.before_request
def ensure_db():
    global _db_initialized
    if not _db_initialized:
        try:
            database.init_db()
            _db_initialized = True
        except Exception as e:
            logger.warning("Database ensure_db check: %s", e)


# --- Decorator for Admin Authentication ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            return jsonify({"error": "Unauthorized. Admin login required."}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- Restaurant & Food Data ---
RESTAURANT_DATA = {
    "title": "DINING AT HOTEL COASTAL PALACE",
    "subheading": "Two Distinct Dining Experiences Under One Roof",
    "outlets": [
        {
            "name": "Krishna Swaad Pure Veg",
            "type": "Pure Vegetarian Family Restaurant",
            "timing": "6:30 AM – 10:30 PM",
            "description": "Authentic South Indian breakfast classics, Mangalorean vegetarian specialties, thalis, and pure vegetarian North Indian dishes prepared with immaculate cleanliness.",
            "highlight": "Pure Ghee Dosas & Authentic Filter Coffee"
        },
        {
            "name": "Coastal Flavours Sea Food Family Restaurant",
            "type": "Multi-Cuisine Seafood Specialist",
            "timing": "11:30 AM – 11:00 PM",
            "description": "Savor the freshest catch from Malpe harbor, including anjal fish fry, squid roast, kori rotti, Mangalore chicken sukka, and authentic coastal curries on banana leaf.",
            "highlight": "Fresh Malpe Catch & Coastal Tawa Masala"
        }
    ],
    "dishes": [
        {
            "id": 1,
            "name": "Coastal Tawa Fish Fry",
            "category": "Seafood",
            "outlet": "Coastal Flavours",
            "image": "/static/images/food/food_fish_fry.jpg",
            "description": "Fresh catch from the Arabian Sea, marinated in authentic Kundapur byadgi chili masala and pan-fried to crisp perfection on banana leaf."
        },
        {
            "id": 2,
            "name": "Mangalorean Kori / Chicken Sukka",
            "category": "Coastal Delicacies",
            "outlet": "Coastal Flavours",
            "image": "/static/images/food/food_chicken_sukka.jpg",
            "description": "Tender country chicken simmered in fragrant roasted spices, freshly grated coconut, and curry leaves."
        },
        {
            "id": 3,
            "name": "Golden Crispy Medu Vada",
            "category": "Pure Veg Breakfast",
            "outlet": "Krishna Swaad",
            "image": "/static/images/food/food_medu_vada.jpg",
            "description": "Crisp on the exterior and fluffy inside, served hot with freshly ground coconut chutney and piping vegetable sambar."
        },
        {
            "id": 4,
            "name": "Crispy Golden Masala Dosa",
            "category": "Pure Veg Breakfast",
            "outlet": "Krishna Swaad",
            "image": "/static/images/food/food_crispy_dosa.jpg",
            "description": "Paper-crisp golden fermented crepe folded with spiced potato masala, served with traditional coconut chutney and sambar."
        },
        {
            "id": 5,
            "name": "Coastal Squid Roast (Kalamari Platter)",
            "category": "Seafood",
            "outlet": "Coastal Flavours",
            "image": "/static/images/food/food_squid_seafood.jpg",
            "description": "Succulent Malpe squid rings tossed with garlic, crushed peppercorns, curry leaves, and coastal spices."
        },
        {
            "id": 6,
            "name": "Piping Hot Poori Bhaji",
            "category": "Pure Veg Breakfast",
            "outlet": "Krishna Swaad",
            "image": "/static/images/food/food_poori_bhaji.jpg",
            "description": "Fluffy, deep-golden wheat pooris paired with mildly spiced homestyle potato saagu and coconut chutney."
        },
        {
            "id": 7,
            "name": "Onion & Tomato Uttapam",
            "category": "Pure Veg Breakfast",
            "outlet": "Krishna Swaad",
            "image": "/static/images/food/food_onion_uttapam.jpg",
            "description": "Thick sourdough pancake topped with finely diced red onions, juicy tomatoes, cilantro, and roasted ghee."
        },
        {
            "id": 8,
            "name": "Coastal Dining Table Platter",
            "category": "Seafood",
            "outlet": "Coastal Flavours",
            "image": "/static/images/food/food_restaurant_table.jpg",
            "description": "A lavish coastal feast featuring pan-seared fresh fish, flaky stuffed parotta, mint dip, and tangy onion salad."
        },
        {
            "id": 9,
            "name": "Grilled Vegetable Club Sandwich",
            "category": "Quick Bites",
            "outlet": "Krishna Swaad",
            "image": "/static/images/food/food_grilled_sandwich.jpg",
            "description": "Triple-decker toasted bread packed with fresh garden vegetables, seasoned cheese, and spicy mint chutney."
        },
        {
            "id": 10,
            "name": "Pineapple Kesari Bath (Sheera)",
            "category": "Desserts & Sweets",
            "outlet": "Krishna Swaad",
            "image": "/static/images/food/food_kesari_bath.jpg",
            "description": "Aromatic semolina pudding prepared in pure desi ghee, infused with saffron, cardamom, and roasted cashews."
        },
        {
            "id": 11,
            "name": "Traditional South Indian Filter Coffee",
            "category": "Beverages",
            "outlet": "Krishna Swaad",
            "image": "/static/images/food/food_filter_coffee.jpg",
            "description": "Brewed with premium Chikmagalur peaberry blend and frothy fresh whole milk, served in an authentic brass Davara tumbler."
        },
        {
            "id": 12,
            "name": "Famous Coastal Gadbad Ice Cream Sundae",
            "category": "Desserts & Sweets",
            "outlet": "Coastal Flavours / Krishna Swaad",
            "image": "/static/images/food/food_gadbad_icecream.jpg",
            "description": "The quintessential coastal Karnataka dessert: layered ice cream scoops, fruit jelly, dry fruits, and crisp wafer crowns."
        }
    ],
    "interiors": [
        {
            "title": "Krishna Swaad & Coastal Flavours Grand AC Dining Hall",
            "image": "/static/images/restaurant/dining_hall_grand.jpg",
            "caption": "Expansive family dining hall featuring ornate laser-cut jali architectural partitions, comfortable leatherette booths, and marble floors."
        },
        {
            "title": "Krishna Swaad Pure Veg Dining Hall",
            "image": "/static/images/restaurant/restaurant_dining_1.jpg",
            "caption": "Elegant seating with decorative jali partitions and plush booths."
        },
        {
            "title": "Coastal Flavours Family Banquette Seating",
            "image": "/static/images/restaurant/restaurant_dining_2.jpg",
            "caption": "Spacious family dining with artistic mural decor and comfortable high-back leatherette booths."
        }
    ]
}

HOTEL_INFRASTRUCTURE = [
    {
        "title": "Luxury Guest Lounge & Living Aquarium",
        "image": "/static/images/hotel/lobby_lounge_aquarium.jpg",
        "category": "LODGE / HOTEL",
        "caption": "Rich wooden wall paneling, tufted cognac sofas, and a backlit panoramic marine fish aquarium for guest relaxation."
    },
    {
        "title": "Executive Front Desk & Reception",
        "image": "/static/images/hotel/reception_lobby.jpg",
        "category": "LODGE / HOTEL",
        "caption": "24/7 front desk welcoming guests with prompt check-ins, local travel guidance, and dedicated hospitality."
    },
    {
        "title": "Sacred Blessings Sanctum & Golden Shrine",
        "image": "/static/images/hotel/divine_shrine.jpg",
        "category": "HOTEL SANCTUM",
        "caption": "Illuminated golden shrine of Lord Venkateshwara radiating peace, positive aura, and spiritual warmth to all visitors."
    },
    {
        "title": "Hotel Coastal Palace & KSB Complex",
        "image": "/static/images/hotel/hotel_exterior.jpg",
        "category": "PROPERTY EXTERIOR",
        "caption": "Modern multi-storey property located on Main Road, Pandubettu, Kalmadi with prominent signage and ample parking."
    }
]

# --- Page Routes ---

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static", "images", "hotel"), "hotel_exterior.jpg", mimetype="image/jpeg")

@app.route("/")
def index():
    settings = database.get_settings()
    rooms = database.get_all_rooms(include_all_statuses=True)
    feedback_list = database.get_approved_feedback()
    return render_template("index.html", settings=settings, rooms=rooms, feedback=feedback_list, restaurant=RESTAURANT_DATA, infrastructure=HOTEL_INFRASTRUCTURE)


@app.route("/admin/login", methods=["GET"])
def admin_login_page():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard_page"))
    settings = database.get_settings()
    return render_template("admin_login.html", settings=settings)

@app.route("/admin")
@app.route("/admin/dashboard")
def admin_dashboard_page():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login_page"))
    settings = database.get_settings()
    return render_template("admin.html", settings=settings)

# --- Public API Endpoints ---

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    settings = database.get_settings()
    # Mask admin credentials
    safe_settings = {k: v for k, v in settings.items() if not k.startswith("admin_")}
    return jsonify(safe_settings)

@app.route("/api/rooms", methods=["GET"])
def api_get_rooms():
    all_rooms = database.get_all_rooms(include_all_statuses=True)
    return jsonify({"success": True, "rooms": all_rooms})

@app.route("/api/rooms/<int:room_id>", methods=["GET"])
def api_get_room(room_id):
    room = database.get_room_by_id(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    return jsonify({"success": True, "room": room})

@app.route("/api/availability", methods=["GET"])
def api_check_availability():
    check_in = request.args.get("check_in", "").strip()
    check_out = request.args.get("check_out", "").strip()
    try:
        guests = int(request.args.get("guests", 1))
    except ValueError:
        guests = 1

    if not check_in or not check_out:
        return jsonify({"error": "Check-in and check-out dates are required."}), 400

    try:
        d_in = date.fromisoformat(check_in)
        d_out = date.fromisoformat(check_out)
    except Exception:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if d_out <= d_in:
        return jsonify({"error": "Please select a check-out date after your check-in date."}), 400

    available_rooms = database.check_room_availability(check_in, check_out, guests)
    nights = (d_out - d_in).days

    return jsonify({
        "success": True,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "guests": guests,
        "count": len(available_rooms),
        "rooms": available_rooms,
        "message": "Rooms found." if available_rooms else "No rooms are available for the selected dates. Please try different dates."
    })

@app.route("/api/bookings", methods=["POST"])
def api_create_booking():
    data = request.get_json() or {}
    customer_name = data.get("customer_name", "").strip()
    mobile = data.get("mobile", "").strip()
    email = data.get("email", "").strip()
    room_id = data.get("room_id")
    check_in = data.get("check_in", "").strip()
    check_out = data.get("check_out", "").strip()
    special_requests = data.get("special_requests", "").strip()

    try:
        adults = int(data.get("adults", 1))
        children = int(data.get("children", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid guest counts."}), 400

    # Validation
    if not customer_name:
        return jsonify({"error": "Customer full name is required."}), 400
    if not mobile:
        return jsonify({"error": "Mobile phone number is required."}), 400
    if not email:
        return jsonify({"error": "Email address is required."}), 400
    if not room_id:
        return jsonify({"error": "A room must be selected."}), 400
    if not check_in or not check_out:
        return jsonify({"error": "Check-in and check-out dates are required."}), 400

    # Validate mobile phone (simple sanity check)
    clean_mobile = "".join(c for c in mobile if c.isdigit())
    if len(clean_mobile) < 10:
        return jsonify({"error": "Please provide a valid 10-digit mobile number."}), 400

    booking_data, err = database.create_booking(
        customer_name=customer_name,
        mobile=mobile,
        email=email,
        room_id=int(room_id),
        check_in_str=check_in,
        check_out_str=check_out,
        adults=adults,
        children=children,
        special_requests=special_requests
    )

    if err:
        return jsonify({"error": err}), 400

    settings = database.get_settings()
    return jsonify({
        "success": True,
        "booking": booking_data,
        "official_phone": settings.get("official_phone", "+91 94801 88990"),
        "message": "Booking Request Submitted! Please call HOTEL COASTAL PALACE to confirm your booking and payment."
    }), 201

@app.route("/api/bookings/<booking_id>", methods=["GET"])
def api_get_booking(booking_id):
    booking = database.get_booking_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found."}), 404
    return jsonify({"success": True, "booking": booking})

@app.route("/api/feedback", methods=["GET", "POST"])
def api_feedback():
    if request.method == "GET":
        feedback_list = database.get_approved_feedback()
        return jsonify({"success": True, "feedback": feedback_list})

    # POST new feedback
    data = request.get_json() or {}
    customer_name = data.get("customer_name", "").strip()
    contact = data.get("contact", "").strip()
    booking_id = data.get("booking_id", "").strip()
    message = data.get("message", "").strip()
    try:
        rating = int(data.get("rating", 5))
    except (ValueError, TypeError):
        rating = 5

    if not customer_name:
        return jsonify({"error": "Please enter your name."}), 400
    if not message:
        return jsonify({"error": "Please enter your feedback message."}), 400

    fb_id, err = database.create_feedback(customer_name, contact, booking_id, rating, message)
    if err:
        return jsonify({"error": err}), 400

    return jsonify({
        "success": True,
        "message": "Thank you for sharing your experience with Hotel Coastal Palace!"
    }), 201

@app.route("/api/restaurant", methods=["GET"])
def api_get_restaurant():
    return jsonify({"success": True, "data": RESTAURANT_DATA})

# --- Admin Authentication & API Routes ---

@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    settings = database.get_settings()
    admin_user = settings.get("admin_username", "admin")
    admin_hash = settings.get("admin_password_hash", database.hash_password("coastal2026!"))

    if username == admin_user and database.hash_password(password) == admin_hash:
        session["is_admin"] = True
        session["admin_user"] = username
        return jsonify({"success": True, "message": "Login successful."})
    else:
        return jsonify({"error": "Invalid admin username or password."}), 401

@app.route("/api/admin/logout", methods=["POST", "GET"])
def api_admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_user", None)
    if request.is_json or request.method == "POST":
        return jsonify({"success": True, "message": "Logged out successfully."})
    return redirect(url_for("admin_login_page"))

@app.route("/api/admin/metrics", methods=["GET"])
@admin_required
def api_admin_metrics():
    metrics = database.get_dashboard_metrics()
    return jsonify({"success": True, "metrics": metrics})

@app.route("/api/admin/rooms", methods=["GET", "POST"])
@admin_required
def api_admin_rooms():
    if request.method == "GET":
        rooms = database.get_all_rooms(include_all_statuses=True)
        return jsonify({"success": True, "rooms": rooms})

    # POST add room
    data = request.get_json() or {}
    room_number = data.get("room_number", "").strip()
    room_name = data.get("room_name", "").strip()
    room_type = data.get("room_type", "standard").strip()
    description = data.get("description", "").strip()
    price = data.get("price_per_night")
    bed_type = data.get("bed_type", "1 Double Bed").strip()
    maximum_guests = data.get("maximum_guests", 2)
    amenities = data.get("amenities", [])
    photos = data.get("photos", [])
    status = data.get("status", "AVAILABLE")
    feature = data.get("feature", "").strip()
    cancellation = data.get("cancellation", "Free cancellation").strip()

    if not room_number or not room_name or price is None:
        return jsonify({"error": "Room number, name, and price per night are required."}), 400

    room_id, err = database.add_room(
        room_number, room_name, room_type, description,
        price, bed_type, maximum_guests, amenities, photos,
        status, feature, cancellation
    )
    if err:
        return jsonify({"error": err}), 400

    return jsonify({"success": True, "room_id": room_id, "message": "Room created successfully."}), 201

@app.route("/api/admin/rooms/<int:room_id>", methods=["GET", "PUT", "DELETE"])
@admin_required
def api_admin_room_detail(room_id):
    if request.method == "GET":
        room = database.get_room_by_id(room_id)
        if not room:
            return jsonify({"error": "Room not found."}), 404
        return jsonify({"success": True, "room": room})

    if request.method == "DELETE":
        ok, err = database.delete_room(room_id)
        if not ok:
            return jsonify({"error": err or "Failed to delete room."}), 400
        return jsonify({"success": True, "message": "Room deleted successfully."})

    # PUT update room
    data = request.get_json() or {}
    room_number = data.get("room_number", "").strip()
    room_name = data.get("room_name", "").strip()
    room_type = data.get("room_type", "standard").strip()
    description = data.get("description", "").strip()
    price = data.get("price_per_night")
    bed_type = data.get("bed_type", "1 Double Bed").strip()
    maximum_guests = data.get("maximum_guests", 2)
    amenities = data.get("amenities", [])
    photos = data.get("photos", [])
    status = data.get("status", "AVAILABLE")
    feature = data.get("feature", "").strip()
    cancellation = data.get("cancellation", "Free cancellation").strip()

    ok, err = database.update_room(
        room_id, room_number, room_name, room_type, description,
        price, bed_type, maximum_guests, amenities, photos,
        status, feature, cancellation
    )
    if not ok:
        return jsonify({"error": err or "Failed to update room."}), 400

    return jsonify({"success": True, "message": "Room updated successfully."})

@app.route("/api/admin/rooms/<int:room_id>/status", methods=["PATCH"])
@admin_required
def api_admin_room_status(room_id):
    data = request.get_json() or {}
    new_status = data.get("status", "").upper()
    ok, err = database.update_room_status(room_id, new_status)
    if not ok:
        return jsonify({"error": err or "Failed to update room status."}), 400
    return jsonify({"success": True, "status": new_status, "message": f"Room status updated to {new_status}."})

@app.route("/api/admin/rooms/<int:room_id>/price", methods=["PATCH"])
@admin_required
def api_admin_room_price(room_id):
    data = request.get_json() or {}
    try:
        new_price = float(data.get("price_per_night", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid price format."}), 400

    ok, err = database.update_room_price(room_id, new_price)
    if not ok:
        return jsonify({"error": err or "Failed to update price."}), 400
    return jsonify({"success": True, "price_per_night": new_price, "message": "Room price updated successfully."})

@app.route("/api/admin/bookings", methods=["GET"])
@admin_required
def api_admin_bookings():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    date_val = request.args.get("date", "").strip()
    bookings = database.get_all_bookings(search, status, date_val)
    return jsonify({"success": True, "bookings": bookings})

@app.route("/api/admin/bookings/<booking_id>/status", methods=["PATCH"])
@admin_required
def api_admin_booking_status(booking_id):
    data = request.get_json() or {}
    new_status = data.get("status", "").upper()
    ok, err = database.update_booking_status(booking_id, new_status)
    if not ok:
        return jsonify({"error": err or "Failed to update booking status."}), 400
    return jsonify({"success": True, "status": new_status, "message": f"Booking marked as {new_status}."})

@app.route("/api/admin/feedback", methods=["GET"])
@admin_required
def api_admin_feedback():
    feedback_list = database.get_all_feedback()
    return jsonify({"success": True, "feedback": feedback_list})

@app.route("/api/admin/feedback/<int:feedback_id>/status", methods=["PATCH"])
@admin_required
def api_admin_feedback_status(feedback_id):
    data = request.get_json() or {}
    new_status = data.get("status", "").upper()
    ok, err = database.update_feedback_status(feedback_id, new_status)
    if not ok:
        return jsonify({"error": err or "Failed to update feedback status."}), 400
    return jsonify({"success": True, "status": new_status, "message": f"Feedback status updated to {new_status}."})

@app.route("/api/admin/feedback/<int:feedback_id>", methods=["DELETE"])
@admin_required
def api_admin_feedback_delete(feedback_id):
    ok, err = database.delete_feedback(feedback_id)
    if not ok:
        return jsonify({"error": err or "Failed to delete feedback."}), 400
    return jsonify({"success": True, "message": "Feedback deleted successfully."})

@app.route("/api/admin/settings", methods=["GET", "PUT"])
@admin_required
def api_admin_settings():
    if request.method == "GET":
        s = database.get_settings()
        s.pop("admin_password_hash", None)
        return jsonify({"success": True, "settings": s})

    data = request.get_json() or {}
    database.update_settings(data)
    return jsonify({"success": True, "message": "Settings updated successfully."})

@app.route("/uploads/<path:filename>")
@app.route("/static/images/uploads/<path:filename>")
def serve_upload(filename):
    upload_folder = app.config.get("UPLOAD_FOLDER")
    if upload_folder and os.path.exists(os.path.join(upload_folder, filename)):
        return send_from_directory(upload_folder, filename)
    static_uploads = os.path.join(app.static_folder, "images", "uploads")
    if os.path.exists(os.path.join(static_uploads, filename)):
        return send_from_directory(static_uploads, filename)
    return jsonify({"error": "File not found."}), 404

@app.route("/api/admin/upload-photo", methods=["POST"])
@admin_required
def api_admin_upload_photo():
    if "photo" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"error": "No selected file."}), 400

    filename = secure_filename(file.filename)
    unique_name = f"{int(datetime.now().timestamp())}_{filename}"
    upload_folder = app.config.get("UPLOAD_FOLDER", "/tmp/uploads")
    try:
        os.makedirs(upload_folder, exist_ok=True)
    except OSError as e:
        return jsonify({"error": f"Cannot write to upload directory: {e}"}), 500

    filepath = os.path.join(upload_folder, unique_name)
    file.save(filepath)
    rel_url = f"/static/images/uploads/{unique_name}"
    return jsonify({"success": True, "url": rel_url})


# --- Health check ---
@app.route("/api/health")
def api_health():
    return jsonify({"status": "healthy", "service": "Hotel Coastal Palace Full Stack API"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
