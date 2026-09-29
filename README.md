# Hotel Coastal Palace - Full-Stack Web Application

A full-stack, production-quality hospitality and lodging platform built for **HOTEL COASTAL PALACE**, situated at **Pandubettu, Kalmadi, Mudanidambur, Karnataka 576106**.

---

## 🌟 Application Features

1. **Combined Hospitality Hub**:
   - Single unified website combining **Hotel / Lodge Accommodation**, **Room Booking Engine**, **Restaurant Dining**, **Culinary Lightbox Gallery**, **Customer Feedback System**, and **Secure Admin Dashboard**.
2. **Real Full-Stack Architecture**:
   - **Backend**: Python 3.15 + Flask with RESTful API architecture.
   - **Database**: Persistent SQLite database (`data/hotel.db`) with foreign keys, indexes, and immediate ACID transactions.
   - **Real Date-Overlap Availability**: Never hardcoded. Dynamically calculates overlaps using boundary check: `(booking.check_in < requested_out) AND (booking.check_out > requested_in)`. Check-out day handovers are preserved.
   - **Double Booking Protection**: Server-side transactional locks prevent race-condition double reservations.
3. **Exact Room Inventory**:
   - **Standard Double Room** (1 Double Bed, Max 2 Guests, ₹3,213/night, Free Wi-Fi, Free cancellation, AVAILABLE).
   - **Deluxe Room** (1 Double Bed, Max 2 Guests, Balcony, ₹3,927/night, Free Wi-Fi, Free cancellation, AVAILABLE).
   - **Superior Double Room** (1 Double Bed, Max 2 Guests, Balcony, ₹6,426/night, Free Wi-Fi, Free cancellation, AVAILABLE).
   - Dynamic Room Price Management: Prices update live from the database when modified by the admin.
4. **Walk-In Guest Support**:
   - Hotel front desk can instantly toggle room status to `OCCUPIED` (walk-in guest). The public website immediately displays `Currently Unavailable`. On check-out, toggling back to `AVAILABLE` restores booking access.
5. **Customer Booking Flow (Manual Confirmation)**:
   - Check-in, Check-out, and Guest selection with real-time night and total cost calculation.
   - Generates a unique **Booking ID** (e.g. `CPB-XXXXX`) in `PENDING CONFIRMATION` status.
   - Prompting: *"Please call HOTEL COASTAL PALACE to confirm your booking and payment"* with a direct `[ CALL HOTEL ]` phone dialer button (`tel:` link).
6. **Separated Photographic Asset Management**:
   - **Hotel / Lodge Photos**: Exterior facade (`hotel_exterior.jpg`), front reception lobby (`reception_lobby.jpg`), and individual room photographs (`standard_double_*.jpg`, `deluxe_*.jpg`, `superior_double_*.jpg`).
   - **Restaurant / Food Photos**: Strict separation. Features 12 authentic cropped dishes (Crispy Masala Dosa, Squid Kalamari Roast, Fish Fry on banana leaf, Kori Sukka, Medu Vada, Filter Coffee, Gadbad Sundae, etc.) and dining hall interiors.
7. **Customer Feedback Moderation**:
   - Customers submit star reviews (1–5 stars) saved as `PENDING`.
   - Admin moderates reviews (Approve to publish publicly, Hide, or Delete).
8. **Admin Control Center**:
   - Protected behind secure session-based authentication (`/admin/login`).
   - Metrics cards: Total Rooms, Available, Occupied, Maintenance, Blocked, Pending Bookings, Confirmed Bookings, Confirmed Revenue.
   - Full room inventory CRUD and photo/amenities editor.
   - Bookings table with search, status filtering, date filtering, and Confirm/Cancel actions.
   - Hotel settings editor: phone, email, address, cancellation policies, check-in/out times, and password updates.

---

## 🚀 Live Access

- **Public Website**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Admin Dashboard**: [http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin)
  - **Username**: `admin`
  - **Password**: `coastal2026!`

---

## 📁 Project Structure

```
hotel-coastal-palace/
├── app.py                      # REST API & Web Route Handlers
├── database.py                 # SQLite Schema, Seed Data, Transactional Logic
├── run_server.py               # Server startup runner with port management
├── test_suite.py               # Comprehensive 15-point End-to-End Test Suite
├── crop_assets.ps1             # Asset pipeline isolating high-res user photos
├── data/
│   └── hotel.db                # Persistent SQLite database
├── static/
│   ├── css/
│   │   ├── style.css           # Luxury coastal design system
│   │   └── admin.css           # Admin dashboard stylesheet
│   ├── js/
│   │   ├── app.js              # Booking widget, dynamic rooms, modals, lightbox
│   │   └── admin.js            # Admin metrics, room status, bookings, reviews
│   └── images/
│       ├── hotel/              # Property exterior & reception desk
│       ├── rooms/              # Standard, Deluxe, Superior room photos
│       ├── restaurant/         # Dining hall interior photos
│       └── food/               # 12 authentic coastal and veg dish photos
└── templates/
    ├── index.html              # Customer-facing full-page application
    ├── admin.html              # Admin management dashboard
    └── admin_login.html        # Secure admin login portal
```

---

## 🧪 Automated Testing Verification

All 15 end-to-end tests from requirement 51 run and pass via:
```powershell
py test_suite.py
```
- **Test 1**: Admin authentication & verification of 3 initial room types.
- **Test 2**: Date-based availability search for 2 adults.
- **Test 3 & 4**: Booking creation with status `PENDING CONFIRMATION`.
- **Test 5 & 6**: Admin views and confirms booking.
- **Test 7**: Double booking protection: Confirmed room unavailable for overlapping dates.
- **Test 7B**: Date boundary handover: Room available from checkout date onwards.
- **Test 8 & 9**: Walk-in toggle: AVAILABLE -> OCCUPIED and back to AVAILABLE.
- **Test 10**: Live dynamic room price update reflected on public website.
- **Test 11 & 12**: Admin updates room photos and description.
- **Test 13, 14 & 15**: Feedback submission, admin approval to public, and hiding.
