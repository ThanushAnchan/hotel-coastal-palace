/**
 * HOTEL COASTAL PALACE - ADMIN DASHBOARD CONTROLLER
 * Real-time metric cards, room CRUD, live status toggle (walk-in support),
 * booking confirmation/cancellation, feedback moderation, settings update.
 */

document.addEventListener('DOMContentLoaded', () => {
  initAdminTabs();
  loadMetrics();
  loadRooms();
  loadBookings();
  loadFeedback();
  loadSettings();
  initRoomModal();
  initBookingFilters();
  initSettingsForm();
});

// --- Tab Switching ---
function initAdminTabs() {
  const tabs = document.querySelectorAll('.admin-nav-item[data-tab]');
  const sections = document.querySelectorAll('.tab-content-section');
  const titleEl = document.getElementById('adminCurrentSectionTitle');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetId = tab.dataset.tab;
      sections.forEach(sec => {
        sec.style.display = sec.id === targetId ? 'block' : 'none';
      });

      if (titleEl) {
        titleEl.textContent = tab.textContent.trim();
      }

      // Refresh data when switching tabs
      if (targetId === 'tabRooms') loadRooms();
      if (targetId === 'tabBookings') loadBookings();
      if (targetId === 'tabFeedback') loadFeedback();
      if (targetId === 'tabOverview') loadMetrics();
    });
  });
}

// --- Metrics Loading ---
async function loadMetrics() {
  try {
    const res = await fetch('/api/admin/metrics');
    if (res.status === 401) {
      window.location.href = '/admin/login';
      return;
    }
    const data = await res.json();
    if (!data.success) return;

    const m = data.metrics;
    document.getElementById('metricTotalRooms').textContent = m.rooms.total;
    document.getElementById('metricAvailableRooms').textContent = m.rooms.available;
    document.getElementById('metricOccupiedRooms').textContent = m.rooms.occupied;
    document.getElementById('metricMaintenanceRooms').textContent = m.rooms.maintenance;
    document.getElementById('metricBlockedRooms').textContent = m.rooms.blocked;

    document.getElementById('metricPendingBookings').textContent = m.bookings.pending;
    document.getElementById('metricConfirmedBookings').textContent = m.bookings.confirmed;
    document.getElementById('metricCancelledBookings').textContent = m.bookings.cancelled;
    document.getElementById('metricConfirmedRevenue').textContent = `₹${m.bookings.confirmed_revenue.toLocaleString('en-IN')}`;

    document.getElementById('metricPendingFeedback').textContent = m.feedback.pending;
  } catch (err) {
    console.error('Failed to load admin metrics:', err);
  }
}

// --- Room Management ---
let roomsCache = [];

async function loadRooms() {
  try {
    const res = await fetch('/api/admin/rooms');
    const data = await res.json();
    if (!data.success) return;

    roomsCache = data.rooms;
    renderRoomsTable(roomsCache);
    loadMetrics(); // Keep metrics in sync
  } catch (err) {
    console.error('Failed to load rooms:', err);
  }
}

function renderRoomsTable(rooms) {
  const tbody = document.getElementById('adminRoomsTableBody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (rooms.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="padding: 2rem;">No rooms configured yet.</td></tr>';
    return;
  }

  rooms.forEach(room => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${room.room_number}</strong></td>
      <td>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <img src="${room.photos[0] || '/static/images/hotel/hotel_exterior.jpg'}" style="width: 50px; height: 38px; object-fit: cover; border-radius: 4px;" alt="${room.room_name}">
          <div>
            <strong>${room.room_name}</strong>
            <div style="font-size: 0.75rem; color: #64748B;">${room.bed_type} · Max ${room.maximum_guests} Guests</div>
          </div>
        </div>
      </td>
      <td><span class="spec-pill">${room.room_type.toUpperCase()}</span></td>
      <td>
        <div style="display: flex; align-items: center; gap: 0.4rem;">
          <span style="font-weight: 700; color: #0A2342;">₹</span>
          <input type="number" class="admin-price-input" data-room-id="${room.room_id}" value="${room.price_per_night}" style="width: 90px; padding: 0.25rem 0.5rem; border: 1px solid #CBD5E1; border-radius: 4px; font-weight: 700;">
          <button class="btn-icon btn-save-price" data-room-id="${room.room_id}" title="Save Price" style="padding: 0.25rem 0.5rem;">💾</button>
        </div>
      </td>
      <td>
        <select class="status-select room-status-dropdown" data-room-id="${room.room_id}">
          <option value="AVAILABLE" ${room.status === 'AVAILABLE' ? 'selected' : ''}>AVAILABLE</option>
          <option value="OCCUPIED" ${room.status === 'OCCUPIED' ? 'selected' : ''}>OCCUPIED (Walk-in / Stay)</option>
          <option value="MAINTENANCE" ${room.status === 'MAINTENANCE' ? 'selected' : ''}>MAINTENANCE</option>
          <option value="BLOCKED" ${room.status === 'BLOCKED' ? 'selected' : ''}>BLOCKED</option>
        </select>
      </td>
      <td><span class="spec-pill">${room.feature || 'None'}</span></td>
      <td>
        <div class="action-btn-group">
          <button class="btn-icon btn-edit-room" data-room-id="${room.room_id}" title="Edit Room Details">✏️ Edit</button>
          <button class="btn-icon danger btn-delete-room" data-room-id="${room.room_id}" title="Delete Room">🗑️</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Attach event listeners for status change
  tbody.querySelectorAll('.room-status-dropdown').forEach(select => {
    select.addEventListener('change', async (e) => {
      const roomId = e.target.dataset.roomId;
      const newStatus = e.target.value;
      try {
        const res = await fetch(`/api/admin/rooms/${roomId}/status`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        });
        const d = await res.json();
        if (!res.ok) {
          alert(d.error || 'Failed to update status');
          loadRooms();
          return;
        }
        showAdminToast(`Room ${roomId} marked as ${newStatus}`);
        loadMetrics();
      } catch (err) {
        alert('Server error changing status');
      }
    });
  });

  // Attach listeners for price saving
  tbody.querySelectorAll('.btn-save-price').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const roomId = btn.dataset.roomId;
      const input = tbody.querySelector(`.admin-price-input[data-room-id="${roomId}"]`);
      const newPrice = parseFloat(input.value);
      if (isNaN(newPrice) || newPrice <= 0) {
        alert('Please enter a valid price.');
        return;
      }
      try {
        const res = await fetch(`/api/admin/rooms/${roomId}/price`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ price_per_night: newPrice })
        });
        const d = await res.json();
        if (!res.ok) {
          alert(d.error || 'Failed to update price');
          return;
        }
        showAdminToast(`Room ${roomId} price updated to ₹${newPrice}`);
      } catch (err) {
        alert('Server error updating price');
      }
    });
  });

  // Edit Room
  tbody.querySelectorAll('.btn-edit-room').forEach(btn => {
    btn.addEventListener('click', () => {
      const roomId = parseInt(btn.dataset.roomId, 10);
      const room = roomsCache.find(r => r.room_id === roomId);
      if (room) openEditRoomModal(room);
    });
  });

  // Delete Room
  tbody.querySelectorAll('.btn-delete-room').forEach(btn => {
    btn.addEventListener('click', async () => {
      const roomId = btn.dataset.roomId;
      if (!confirm(`Are you sure you want to delete Room ID ${roomId}? This cannot be undone.`)) return;
      try {
        const res = await fetch(`/api/admin/rooms/${roomId}`, { method: 'DELETE' });
        const d = await res.json();
        if (!res.ok) {
          alert(d.error || 'Failed to delete room');
          return;
        }
        showAdminToast('Room deleted successfully');
        loadRooms();
      } catch (err) {
        alert('Server error deleting room');
      }
    });
  });
}

// --- Room Add / Edit Modal ---
function initRoomModal() {
  const addBtn = document.getElementById('btnAddRoom');
  const form = document.getElementById('adminRoomForm');
  if (!addBtn || !form) return;

  addBtn.addEventListener('click', () => {
    form.reset();
    document.getElementById('adminRoomIdField').value = '';
    document.getElementById('adminRoomModalTitle').textContent = 'Add New Room';
    document.getElementById('adminRoomStatus').value = 'AVAILABLE';
    document.getElementById('adminRoomPhotos').value = '/static/images/rooms/standard_double_1.jpg, /static/images/rooms/standard_double_2.jpg';
    document.getElementById('adminRoomAmenities').value = 'Free Wi-Fi, 1 Double Bed, Air Conditioning, Flat-Screen TV, Attached Bathroom, 24/7 Hot Water';
    openModal('adminRoomModal');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const roomId = document.getElementById('adminRoomIdField').value;
    const roomNumber = document.getElementById('adminRoomNumber').value.trim();
    const roomName = document.getElementById('adminRoomName').value.trim();
    const roomType = document.getElementById('adminRoomType').value.trim();
    const price = parseFloat(document.getElementById('adminRoomPrice').value);
    const bedType = document.getElementById('adminRoomBedType').value.trim();
    const maxGuests = parseInt(document.getElementById('adminRoomMaxGuests').value, 10);
    const feature = document.getElementById('adminRoomFeature').value.trim();
    const status = document.getElementById('adminRoomStatus').value;
    const cancellation = document.getElementById('adminRoomCancellation').value.trim();
    const description = document.getElementById('adminRoomDesc').value.trim();

    const amenities = document.getElementById('adminRoomAmenities').value
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const photos = document.getElementById('adminRoomPhotos').value
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const payload = {
      room_number: roomNumber,
      room_name: roomName,
      room_type: roomType,
      price_per_night: price,
      bed_type: bedType,
      maximum_guests: maxGuests,
      feature,
      status,
      cancellation,
      description,
      amenities,
      photos
    };

    const isEdit = !!roomId;
    const url = isEdit ? `/api/admin/rooms/${roomId}` : '/api/admin/rooms';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const d = await res.json();
      if (!res.ok) {
        alert(d.error || 'Failed to save room.');
        return;
      }
      closeModal('adminRoomModal');
      showAdminToast(isEdit ? 'Room updated successfully' : 'Room created successfully');
      loadRooms();
    } catch (err) {
      alert('Error saving room.');
    }
  });
}

function openEditRoomModal(room) {
  document.getElementById('adminRoomIdField').value = room.room_id;
  document.getElementById('adminRoomModalTitle').textContent = `Edit Room ${room.room_number}`;
  document.getElementById('adminRoomNumber').value = room.room_number;
  document.getElementById('adminRoomName').value = room.room_name;
  document.getElementById('adminRoomType').value = room.room_type;
  document.getElementById('adminRoomPrice').value = room.price_per_night;
  document.getElementById('adminRoomBedType').value = room.bed_type;
  document.getElementById('adminRoomMaxGuests').value = room.maximum_guests;
  document.getElementById('adminRoomFeature').value = room.feature || '';
  document.getElementById('adminRoomStatus').value = room.status;
  document.getElementById('adminRoomCancellation').value = room.cancellation || 'Free cancellation';
  document.getElementById('adminRoomDesc').value = room.description;
  document.getElementById('adminRoomAmenities').value = (room.amenities || []).join(', ');
  document.getElementById('adminRoomPhotos').value = (room.photos || []).join(', ');

  openModal('adminRoomModal');
}

// --- Bookings Management ---
function initBookingFilters() {
  const searchInput = document.getElementById('bookingSearchInput');
  const statusSelect = document.getElementById('bookingStatusFilter');
  const dateInput = document.getElementById('bookingDateFilter');

  const triggerFilter = () => {
    loadBookings(searchInput.value.trim(), statusSelect.value, dateInput.value);
  };

  searchInput?.addEventListener('input', debounce(triggerFilter, 300));
  statusSelect?.addEventListener('change', triggerFilter);
  dateInput?.addEventListener('change', triggerFilter);
}

async function loadBookings(query = '', status = '', date = '') {
  try {
    const url = `/api/admin/bookings?search=${encodeURIComponent(query)}&status=${encodeURIComponent(status)}&date=${encodeURIComponent(date)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    renderBookingsTable(data.bookings);
    loadMetrics();
  } catch (err) {
    console.error('Failed to load bookings:', err);
  }
}

function renderBookingsTable(bookings) {
  const tbody = document.getElementById('adminBookingsTableBody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (bookings.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="padding: 2rem;">No bookings found matching filters.</td></tr>';
    return;
  }

  bookings.forEach(b => {
    const tr = document.createElement('tr');
    const statusClass = b.booking_status.toLowerCase().replace(/\s+/g, '-');
    tr.innerHTML = `
      <td><strong>${b.booking_id}</strong><div style="font-size: 0.72rem; color: #64748B;">${b.created_at.split('T')[0]}</div></td>
      <td>
        <strong>${b.customer_name}</strong>
        <div style="font-size: 0.8rem; color: #475569;">📞 <a href="tel:${b.mobile}">${b.mobile}</a></div>
        <div style="font-size: 0.75rem; color: #64748B;">✉️ ${b.email}</div>
      </td>
      <td>
        <strong>${b.room_name}</strong>
        <div style="font-size: 0.75rem; color: #64748B;">Room ${b.room_number}</div>
      </td>
      <td>
        <div><strong>${b.check_in}</strong> to <strong>${b.check_out}</strong></div>
        <div style="font-size: 0.75rem; color: #64748B;">${b.number_of_nights} night(s) · ${b.adults}A, ${b.children}C</div>
      </td>
      <td><strong>₹${b.total_amount.toLocaleString('en-IN')}</strong></td>
      <td><span class="status-pill ${statusClass}">${b.booking_status}</span></td>
      <td>
        <div class="action-btn-group">
          ${b.booking_status === 'PENDING CONFIRMATION' ? `
            <button class="btn-icon success btn-confirm-booking" data-booking-id="${b.booking_id}" title="Confirm Booking">✓ Confirm</button>
            <button class="btn-icon danger btn-cancel-booking" data-booking-id="${b.booking_id}" title="Cancel Booking">✕ Cancel</button>
          ` : ''}
          ${b.booking_status === 'CONFIRMED' ? `
            <button class="btn-icon btn-complete-booking" data-booking-id="${b.booking_id}" title="Mark Completed" style="background: #3B82F6; color: white;">✓ Complete</button>
            <button class="btn-icon danger btn-cancel-booking" data-booking-id="${b.booking_id}" title="Cancel Booking">✕ Cancel</button>
          ` : ''}
          ${b.booking_status === 'CANCELLED' ? `
            <span style="font-size: 0.8rem; color: #94A3B8;">Cancelled</span>
          ` : ''}
          ${b.booking_status === 'COMPLETED' ? `
            <span style="font-size: 0.8rem; color: #10B981; font-weight: 600;">Completed</span>
          ` : ''}
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Action listeners
  tbody.querySelectorAll('.btn-confirm-booking').forEach(btn => {
    btn.addEventListener('click', () => updateBookingStatus(btn.dataset.bookingId, 'CONFIRMED'));
  });

  tbody.querySelectorAll('.btn-cancel-booking').forEach(btn => {
    btn.addEventListener('click', () => {
      if (confirm(`Are you sure you want to CANCEL booking ${btn.dataset.bookingId}? This will release the room for those dates.`)) {
        updateBookingStatus(btn.dataset.bookingId, 'CANCELLED');
      }
    });
  });

  tbody.querySelectorAll('.btn-complete-booking').forEach(btn => {
    btn.addEventListener('click', () => updateBookingStatus(btn.dataset.bookingId, 'COMPLETED'));
  });
}

async function updateBookingStatus(bookingId, status) {
  try {
    const res = await fetch(`/api/admin/bookings/${bookingId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    const d = await res.json();
    if (!res.ok) {
      alert(d.error || 'Failed to update booking status');
      return;
    }
    showAdminToast(d.message || `Booking marked as ${status}`);
    loadBookings();
  } catch (err) {
    alert('Server error updating booking status');
  }
}

// --- Customer Feedback Moderation ---
async function loadFeedback() {
  try {
    const res = await fetch('/api/admin/feedback');
    const data = await res.json();
    if (!data.success) return;

    renderFeedbackTable(data.feedback);
    loadMetrics();
  } catch (err) {
    console.error('Failed to load feedback:', err);
  }
}

function renderFeedbackTable(feedbacks) {
  const tbody = document.getElementById('adminFeedbackTableBody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (feedbacks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 2rem;">No feedback submitted yet.</td></tr>';
    return;
  }

  feedbacks.forEach(fb => {
    const tr = document.createElement('tr');
    const stars = '★'.repeat(fb.rating) + '☆'.repeat(5 - fb.rating);
    const statusClass = fb.status.toLowerCase();

    tr.innerHTML = `
      <td>#${fb.feedback_id}</td>
      <td>
        <strong>${fb.customer_name}</strong>
        <div style="font-size: 0.75rem; color: #64748B;">${fb.contact || 'No contact'} · Ref: ${fb.booking_id || 'N/A'}</div>
      </td>
      <td><span style="color: #F59E0B; font-size: 1rem;">${stars}</span></td>
      <td style="max-width: 320px; font-size: 0.85rem; color: #334155;">"${fb.message}"</td>
      <td><span class="status-pill ${statusClass}">${fb.status}</span></td>
      <td>
        <div class="action-btn-group">
          ${fb.status !== 'APPROVED' ? `
            <button class="btn-icon success btn-approve-fb" data-fb-id="${fb.feedback_id}" title="Approve & Publish to website">✓ Approve</button>
          ` : ''}
          ${fb.status !== 'HIDDEN' ? `
            <button class="btn-icon btn-hide-fb" data-fb-id="${fb.feedback_id}" title="Hide from public">👁️ Hide</button>
          ` : ''}
          <button class="btn-icon danger btn-delete-fb" data-fb-id="${fb.feedback_id}" title="Delete feedback">🗑️</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('.btn-approve-fb').forEach(btn => {
    btn.addEventListener('click', () => updateFeedbackStatus(btn.dataset.fbId, 'APPROVED'));
  });

  tbody.querySelectorAll('.btn-hide-fb').forEach(btn => {
    btn.addEventListener('click', () => updateFeedbackStatus(btn.dataset.fbId, 'HIDDEN'));
  });

  tbody.querySelectorAll('.btn-delete-fb').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Are you sure you want to permanently delete this feedback?')) return;
      try {
        const res = await fetch(`/api/admin/feedback/${btn.dataset.fbId}`, { method: 'DELETE' });
        const d = await res.json();
        if (!res.ok) {
          alert(d.error || 'Failed to delete feedback');
          return;
        }
        showAdminToast('Feedback deleted');
        loadFeedback();
      } catch (err) {
        alert('Server error deleting feedback');
      }
    });
  });
}

async function updateFeedbackStatus(fbId, status) {
  try {
    const res = await fetch(`/api/admin/feedback/${fbId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    const d = await res.json();
    if (!res.ok) {
      alert(d.error || 'Failed to update feedback status');
      return;
    }
    showAdminToast(`Feedback status updated to ${status}`);
    loadFeedback();
  } catch (err) {
    alert('Server error updating feedback');
  }
}

// --- Hotel Settings ---
async function loadSettings() {
  try {
    const res = await fetch('/api/admin/settings');
    const data = await res.json();
    if (!data.success) return;

    const s = data.settings;
    document.getElementById('settingHotelName').value = s.hotel_name || '';
    document.getElementById('settingTagline').value = s.tagline || '';
    document.getElementById('settingAddress').value = s.address || '';
    document.getElementById('settingPhone').value = s.official_phone || '';
    document.getElementById('settingEmail').value = s.official_email || '';
    document.getElementById('settingCheckinTime').value = s.checkin_time || '12:00 PM';
    document.getElementById('settingCheckoutTime').value = s.checkout_time || '11:00 AM';
    document.getElementById('settingCancellationPolicy').value = s.cancellation_policy || '';
    document.getElementById('settingHotelDesc').value = s.hotel_description || '';
    document.getElementById('settingDirectionsUrl').value = s.map_directions_url || '';
    const adminUserEl = document.getElementById('settingAdminUsername');
    if (adminUserEl) adminUserEl.value = s.admin_username || 'admin';
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
}

function initSettingsForm() {
  const form = document.getElementById('adminSettingsForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      hotel_name: document.getElementById('settingHotelName').value.trim(),
      tagline: document.getElementById('settingTagline').value.trim(),
      address: document.getElementById('settingAddress').value.trim(),
      official_phone: document.getElementById('settingPhone').value.trim(),
      official_email: document.getElementById('settingEmail').value.trim(),
      checkin_time: document.getElementById('settingCheckinTime').value.trim(),
      checkout_time: document.getElementById('settingCheckoutTime').value.trim(),
      cancellation_policy: document.getElementById('settingCancellationPolicy').value.trim(),
      hotel_description: document.getElementById('settingHotelDesc').value.trim(),
      map_directions_url: document.getElementById('settingDirectionsUrl').value.trim()
    };

    const adminUser = document.getElementById('settingAdminUsername')?.value.trim();
    if (adminUser) {
      payload.admin_username = adminUser;
    }

    const newPass = document.getElementById('settingNewPassword').value.trim();
    if (newPass) {
      payload.admin_password = newPass;
    }

    try {
      const res = await fetch('/api/admin/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const d = await res.json();
      if (!res.ok) {
        alert(d.error || 'Failed to update settings');
        return;
      }
      showAdminToast('Settings updated successfully!');
      document.getElementById('settingNewPassword').value = '';
    } catch (err) {
      alert('Server error updating settings');
    }
  });
}

// --- Admin Toast Notification Helper ---
function showAdminToast(msg) {
  let toast = document.getElementById('adminToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'adminToast';
    toast.style.position = 'fixed';
    toast.style.bottom = '2rem';
    toast.style.right = '2rem';
    toast.style.background = '#0A2342';
    toast.style.color = '#FFFFFF';
    toast.style.padding = '0.9rem 1.5rem';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 6px 20px rgba(0,0,0,0.2)';
    toast.style.zIndex = '9999';
    toast.style.fontWeight = '600';
    toast.style.fontSize = '0.9rem';
    toast.style.borderLeft = '4px solid #C59B27';
    toast.style.transition = 'all 0.3s ease';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.display = 'block';
  toast.style.opacity = '1';

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => { toast.style.display = 'none'; }, 300);
  }, 3500);
}

// --- Utility: Debounce ---
function debounce(fn, delay) {
  let timer = null;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
