/**
 * HOTEL COASTAL PALACE - PUBLIC CLIENT SCRIPT
 * Handles real-time availability check, room modal, booking flow,
 * food lightbox gallery, feedback submission, and mobile navigation.
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initDatePickers();
  initBookingSearch();
  initRoomCards();
  initBookingTriggers();
  initBookingModalHandlers();
  initFeedbackForm();
  initLightbox();
  initBackdropClose();
});

// Current active state
let currentLightboxItems = [];
let currentLightboxIndex = 0;

// --- Mobile Navigation ---
function initMobileNav() {
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const mobileNav = document.getElementById('mobileNav');
  if (!hamburgerBtn || !mobileNav) return;

  hamburgerBtn.addEventListener('click', () => {
    hamburgerBtn.classList.toggle('active');
    mobileNav.classList.toggle('open');
  });

  // Close on nav link click
  mobileNav.querySelectorAll('.nav-link, button').forEach(el => {
    el.addEventListener('click', () => {
      hamburgerBtn.classList.remove('active');
      mobileNav.classList.remove('open');
    });
  });

  // Header scroll shadow
  window.addEventListener('scroll', () => {
    const header = document.querySelector('.site-header');
    if (!header) return;
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });
}

// --- Date Pickers & Validation ---
function initDatePickers() {
  const checkInInput = document.getElementById('searchCheckIn');
  const checkOutInput = document.getElementById('searchCheckOut');
  if (!checkInInput || !checkOutInput) return;

  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);

  const formatDate = (d) => d.toISOString().split('T')[0];

  const todayStr = formatDate(today);
  const tomorrowStr = formatDate(tomorrow);

  checkInInput.min = todayStr;
  checkOutInput.min = tomorrowStr;

  if (!checkInInput.value) checkInInput.value = todayStr;
  if (!checkOutInput.value) checkOutInput.value = tomorrowStr;

  // When check-in changes, auto update check-out min
  checkInInput.addEventListener('change', () => {
    const selectedIn = new Date(checkInInput.value);
    if (!isNaN(selectedIn.getTime())) {
      const nextDay = new Date(selectedIn);
      nextDay.setDate(selectedIn.getDate() + 1);
      const nextDayStr = formatDate(nextDay);
      checkOutInput.min = nextDayStr;
      if (checkOutInput.value <= checkInInput.value) {
        checkOutInput.value = nextDayStr;
      }
    }
  });
}

// --- Real Database Availability Search ---
function initBookingSearch() {
  const searchForm = document.getElementById('bookingSearchForm');
  const alertBox = document.getElementById('searchAlert');
  if (!searchForm || !alertBox) return;

  searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const checkIn = document.getElementById('searchCheckIn').value;
    const checkOut = document.getElementById('searchCheckOut').value;
    const adults = parseInt(document.getElementById('searchAdults').value, 10) || 1;
    const children = parseInt(document.getElementById('searchChildren').value, 10) || 0;
    const totalGuests = adults + children;

    alertBox.className = 'availability-alert';
    alertBox.style.display = 'none';

    // Strict client validation
    if (!checkIn || !checkOut) {
      alertBox.textContent = 'Please select both check-in and check-out dates.';
      alertBox.classList.add('error');
      alertBox.style.display = 'block';
      return;
    }

    if (checkOut <= checkIn) {
      alertBox.textContent = 'Please select a check-out date after your check-in date.';
      alertBox.classList.add('error');
      alertBox.style.display = 'block';
      return;
    }

    try {
      const searchBtn = searchForm.querySelector('button[type="submit"]');
      const originalText = searchBtn.innerHTML;
      searchBtn.disabled = true;
      searchBtn.innerHTML = '<span>Checking...</span>';

      const res = await fetch(`/api/availability?check_in=${encodeURIComponent(checkIn)}&check_out=${encodeURIComponent(checkOut)}&guests=${totalGuests}`);
      const data = await res.json();

      searchBtn.disabled = false;
      searchBtn.innerHTML = originalText;

      if (!res.ok) {
        alertBox.textContent = data.error || 'Failed to check availability.';
        alertBox.classList.add('error');
        alertBox.style.display = 'block';
        return;
      }

      if (data.count === 0) {
        alertBox.textContent = 'No rooms are available for the selected dates. Please try different dates.';
        alertBox.classList.add('error');
        alertBox.style.display = 'block';
      } else {
        alertBox.innerHTML = `
          <span>Great news! <strong>${data.count} room(s)</strong> available from ${checkIn} to ${checkOut} (${data.nights} night${data.nights > 1 ? 's' : ''}).</span>
          <button type="button" class="btn btn-primary" id="btnBookFromSearch" style="margin-left: 1rem; padding: 0.4rem 1rem; font-size: 0.82rem; border-radius: 6px;">BOOK NOW</button>
        `;
        alertBox.classList.add('success');
        alertBox.style.display = 'flex';
        alertBox.style.alignItems = 'center';
        alertBox.style.justifyContent = 'space-between';
        alertBox.style.flexWrap = 'wrap';
        alertBox.style.gap = '0.5rem';

        document.getElementById('btnBookFromSearch')?.addEventListener('click', () => {
          openBookingModal(data.rooms[0]?.room_id, checkIn, checkOut, adults, children);
        });

        highlightAvailableRooms(data.rooms, checkIn, checkOut, adults, children);
      }

      // Smooth scroll to rooms
      const roomsEl = document.getElementById('rooms');
      if (roomsEl) {
        roomsEl.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (err) {
      alertBox.textContent = 'Unable to check room availability right now. Please try again or call the hotel.';
      alertBox.classList.add('error');
      alertBox.style.display = 'block';
    }
  });
}

function highlightAvailableRooms(availableRooms, checkIn, checkOut, adults, children) {
  const availableIds = new Set(availableRooms.map(r => r.room_id));
  document.querySelectorAll('.room-card').forEach(card => {
    const roomId = parseInt(card.dataset.roomId, 10);
    const bookBtn = card.querySelector('.btn-book-room');
    if (availableIds.has(roomId)) {
      card.style.opacity = '1';
      card.style.border = '2px solid #10B981';
      if (bookBtn) {
        bookBtn.disabled = false;
        bookBtn.textContent = 'BOOK NOW';
        bookBtn.dataset.checkIn = checkIn;
        bookBtn.dataset.checkOut = checkOut;
        bookBtn.dataset.adults = adults;
        bookBtn.dataset.children = children;
      }
    } else {
      card.style.opacity = '0.6';
      card.style.border = '1px solid #CBD5E1';
      if (bookBtn) {
        bookBtn.disabled = true;
        bookBtn.textContent = 'UNAVAILABLE';
      }
    }
  });
}

// --- General Booking Trigger Buttons ---
function initBookingTriggers() {
  // Any button with class .btn-trigger-booking or specific IDs triggers the booking modal
  document.querySelectorAll('.btn-trigger-booking, #navBookBtn, #heroBookStayBtn, #connectionBookBtn, #footerBookBtn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const inVal = document.getElementById('searchCheckIn')?.value;
      const outVal = document.getElementById('searchCheckOut')?.value;
      const adultsVal = document.getElementById('searchAdults')?.value || 1;
      const childrenVal = document.getElementById('searchChildren')?.value || 0;
      openBookingModal(null, inVal, outVal, adultsVal, childrenVal);
    });
  });
}

// --- Room Cards Event Listeners ---
function initRoomCards() {
  document.addEventListener('click', (e) => {
    // View Room details modal
    const viewBtn = e.target.closest('.btn-view-room');
    if (viewBtn) {
      const roomId = viewBtn.dataset.roomId;
      openRoomDetailsModal(roomId);
      return;
    }

    // Book Room directly from card
    const bookBtn = e.target.closest('.btn-book-room');
    if (bookBtn && !bookBtn.disabled) {
      const roomId = bookBtn.dataset.roomId;
      const checkIn = bookBtn.dataset.checkIn || document.getElementById('searchCheckIn')?.value;
      const checkOut = bookBtn.dataset.checkOut || document.getElementById('searchCheckOut')?.value;
      const adults = bookBtn.dataset.adults || document.getElementById('searchAdults')?.value || 1;
      const children = bookBtn.dataset.children || document.getElementById('searchChildren')?.value || 0;
      openBookingModal(roomId, checkIn, checkOut, adults, children);
    }
  });
}

// --- View Room Details Modal ---
async function openRoomDetailsModal(roomId) {
  const modal = document.getElementById('roomDetailsModal');
  if (!modal) return;

  try {
    const res = await fetch(`/api/rooms/${roomId}`);
    const data = await res.json();
    if (!data.success || !data.room) return;
    const room = data.room;

    document.getElementById('modalRoomName').textContent = room.room_name;
    document.getElementById('modalRoomNumber').textContent = `Room ${room.room_number}`;
    document.getElementById('modalRoomDesc').textContent = room.description;
    document.getElementById('modalBedType').textContent = room.bed_type;
    document.getElementById('modalMaxGuests').textContent = `Up to ${room.maximum_guests} Guests`;
    document.getElementById('modalRoomPrice').textContent = `₹${room.price_per_night.toLocaleString('en-IN')}`;
    document.getElementById('modalCancellation').textContent = room.cancellation || 'Free cancellation';

    // Status Badge
    const statusBadge = document.getElementById('modalRoomStatus');
    statusBadge.textContent = room.status;
    statusBadge.className = `room-badge ${room.status.toLowerCase()}`;

    // Amenities
    const amenitiesContainer = document.getElementById('modalRoomAmenities');
    amenitiesContainer.innerHTML = '';
    (room.amenities || []).forEach(am => {
      const span = document.createElement('span');
      span.className = 'spec-pill';
      span.textContent = `✓ ${am}`;
      amenitiesContainer.appendChild(span);
    });

    // Gallery Photos
    const mainImg = document.getElementById('modalMainImage');
    const thumbContainer = document.getElementById('modalThumbsContainer');
    thumbContainer.innerHTML = '';

    if (room.photos && room.photos.length > 0) {
      mainImg.src = room.photos[0];
      mainImg.alt = room.room_name;

      room.photos.forEach((photo, idx) => {
        const thumb = document.createElement('img');
        thumb.src = photo;
        thumb.alt = `${room.room_name} photo ${idx + 1}`;
        thumb.className = `room-thumb ${idx === 0 ? 'active' : ''}`;
        thumb.style.width = '70px';
        thumb.style.height = '50px';
        thumb.style.objectFit = 'cover';
        thumb.style.borderRadius = '6px';
        thumb.style.cursor = 'pointer';
        thumb.style.border = idx === 0 ? '2px solid #C59B27' : '1px solid #CBD5E1';

        thumb.addEventListener('click', () => {
          mainImg.src = photo;
          thumbContainer.querySelectorAll('img').forEach(t => {
            t.style.border = '1px solid #CBD5E1';
          });
          thumb.style.border = '2px solid #C59B27';
        });

        thumbContainer.appendChild(thumb);
      });
    }

    // Modal Book Button
    const modalBookBtn = document.getElementById('modalBookBtn');
    if (room.status === 'AVAILABLE') {
      modalBookBtn.disabled = false;
      modalBookBtn.textContent = 'BOOK THIS ROOM';
      modalBookBtn.onclick = () => {
        closeModal('roomDetailsModal');
        openBookingModal(room.room_id);
      };
    } else {
      modalBookBtn.disabled = true;
      modalBookBtn.textContent = room.status === 'OCCUPIED' ? 'Currently Unavailable' : 'Temporarily Unavailable';
    }

    openModal('roomDetailsModal');
  } catch (err) {
    console.error('Failed to open room details:', err);
  }
}

// --- Customer Booking Modal ---
function openBookingModal(roomId, defaultCheckIn, defaultCheckOut, defaultAdults, defaultChildren) {
  const modal = document.getElementById('bookingModal');
  if (!modal) return;

  const roomSelect = document.getElementById('bookingRoomSelect');
  const roomIdInput = document.getElementById('bookingRoomId');
  const inInput = document.getElementById('bookingCheckIn');
  const outInput = document.getElementById('bookingCheckOut');
  const adultsInput = document.getElementById('bookingAdults');
  const childrenInput = document.getElementById('bookingChildren');

  // Set default dates if empty
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);
  const formatDate = (d) => d.toISOString().split('T')[0];

  const todayStr = formatDate(today);
  const tomorrowStr = formatDate(tomorrow);

  inInput.min = todayStr;
  outInput.min = tomorrowStr;

  inInput.value = defaultCheckIn || document.getElementById('searchCheckIn')?.value || todayStr;
  outInput.value = defaultCheckOut || document.getElementById('searchCheckOut')?.value || tomorrowStr;
  if (defaultAdults) adultsInput.value = defaultAdults;
  if (defaultChildren) childrenInput.value = defaultChildren;

  // Select the appropriate room in the dropdown
  if (roomSelect) {
    if (roomId) {
      roomSelect.value = roomId.toString();
    }
    if (roomIdInput) {
      roomIdInput.value = roomSelect.value;
    }
  }

  // Recalculate summary live
  updateBookingSummary();

  // Reset alert messages & view screens
  document.getElementById('bookingErrorAlert').style.display = 'none';
  document.getElementById('bookingFormScreen').style.display = 'block';
  document.getElementById('bookingSuccessScreen').style.display = 'none';

  openModal('bookingModal');
}

function updateBookingSummary() {
  const roomSelect = document.getElementById('bookingRoomSelect');
  const inVal = document.getElementById('bookingCheckIn')?.value;
  const outVal = document.getElementById('bookingCheckOut')?.value;
  const nightsEl = document.getElementById('summaryNights');
  const priceEl = document.getElementById('summaryPricePerNight');
  const totalEl = document.getElementById('summaryTotal');
  const subtitleName = document.getElementById('bookModalRoomName');

  let pricePerNight = 3213;
  let roomName = 'Standard Double Room';

  if (roomSelect && roomSelect.selectedOptions.length > 0) {
    const opt = roomSelect.selectedOptions[0];
    pricePerNight = parseFloat(opt.dataset.price) || 3213;
    roomName = opt.dataset.name || opt.textContent.split('—')[0].trim();
    const roomIdInput = document.getElementById('bookingRoomId');
    if (roomIdInput) roomIdInput.value = opt.value;
  }

  if (subtitleName) subtitleName.textContent = roomName;
  if (priceEl) priceEl.textContent = `₹${pricePerNight.toLocaleString('en-IN')}`;

  let nights = 1;
  if (inVal && outVal && outVal > inVal) {
    const dIn = new Date(inVal);
    const dOut = new Date(outVal);
    nights = Math.max(1, Math.round((dOut - dIn) / (1000 * 60 * 60 * 24)));
  }

  if (nightsEl) nightsEl.textContent = `${nights} night${nights > 1 ? 's' : ''}`;
  const total = pricePerNight * nights;
  if (totalEl) totalEl.textContent = `₹${total.toLocaleString('en-IN')}`;
}

function initBookingModalHandlers() {
  const roomSelect = document.getElementById('bookingRoomSelect');
  const inInput = document.getElementById('bookingCheckIn');
  const outInput = document.getElementById('bookingCheckOut');
  const bookingForm = document.getElementById('customerBookingForm');

  roomSelect?.addEventListener('change', updateBookingSummary);

  inInput?.addEventListener('change', () => {
    if (inInput.value) {
      const next = new Date(inInput.value);
      next.setDate(next.getDate() + 1);
      const nextStr = next.toISOString().split('T')[0];
      outInput.min = nextStr;
      if (outInput.value <= inInput.value) {
        outInput.value = nextStr;
      }
    }
    updateBookingSummary();
  });

  outInput?.addEventListener('change', updateBookingSummary);

  // Submit Booking Form
  bookingForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorAlert = document.getElementById('bookingErrorAlert');
    errorAlert.style.display = 'none';

    const customerName = document.getElementById('bookingCustomerName').value.trim();
    const mobile = document.getElementById('bookingMobile').value.trim();
    const email = document.getElementById('bookingEmail').value.trim();
    const roomId = roomSelect ? roomSelect.value : document.getElementById('bookingRoomId')?.value;
    const checkIn = document.getElementById('bookingCheckIn').value;
    const checkOut = document.getElementById('bookingCheckOut').value;
    const adults = parseInt(document.getElementById('bookingAdults').value, 10) || 1;
    const children = parseInt(document.getElementById('bookingChildren').value, 10) || 0;
    const specialRequests = document.getElementById('bookingNotes')?.value.trim() || '';

    if (!roomId) {
      errorAlert.textContent = 'Please select a room to book.';
      errorAlert.style.display = 'block';
      return;
    }

    if (checkOut <= checkIn) {
      errorAlert.textContent = 'Please select a check-out date after your check-in date.';
      errorAlert.style.display = 'block';
      return;
    }

    const submitBtn = bookingForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Processing Booking...</span>';

    try {
      const res = await fetch('/api/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          mobile,
          email,
          room_id: parseInt(roomId, 10),
          check_in: checkIn,
          check_out: checkOut,
          adults,
          children,
          special_requests: specialRequests
        })
      });

      const data = await res.json();
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;

      if (!res.ok) {
        errorAlert.textContent = data.error || 'Failed to submit booking request.';
        errorAlert.style.display = 'block';
        return;
      }

      // Show confirmation screen
      document.getElementById('bookingFormScreen').style.display = 'none';
      const successScreen = document.getElementById('bookingSuccessScreen');
      successScreen.style.display = 'block';

      const b = data.booking;
      document.getElementById('successBookingId').textContent = b.booking_id;
      document.getElementById('successCustomerName').textContent = b.customer_name;
      document.getElementById('successRoomName').textContent = `${b.room_name} (${b.room_number})`;
      document.getElementById('successDates').textContent = `${b.check_in} to ${b.check_out} (${b.number_of_nights} night${b.number_of_nights > 1 ? 's' : ''})`;
      document.getElementById('successTotal').textContent = `₹${b.total_amount.toLocaleString('en-IN')}`;

      // Call Hotel Button with tel: link
      const phone = data.official_phone || '+91 94801 88990';
      const cleanPhone = phone.replace(/[^0-9+]/g, '');
      const callBtn = document.getElementById('successCallHotelBtn');
      if (callBtn) {
        callBtn.href = `tel:${cleanPhone}`;
        callBtn.textContent = `📞 CALL HOTEL (${phone})`;
      }
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
      errorAlert.textContent = 'Server connection error. Please try again or call the hotel.';
      errorAlert.style.display = 'block';
    }
  });
}

// --- Feedback Submission ---
function initFeedbackForm() {
  const form = document.getElementById('customerFeedbackForm');
  const alertBox = document.getElementById('feedbackAlert');
  if (!form || !alertBox) return;

  // Star selector
  const starInputs = form.querySelectorAll('.star-rating-input input');
  starInputs.forEach(input => {
    input.addEventListener('change', () => {
      const val = input.value;
      form.querySelectorAll('.star-label').forEach((lbl, idx) => {
        lbl.style.color = idx < val ? '#F59E0B' : '#CBD5E1';
      });
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    alertBox.style.display = 'none';

    const customerName = document.getElementById('feedbackName').value.trim();
    const contact = document.getElementById('feedbackContact').value.trim();
    const bookingId = document.getElementById('feedbackBookingId').value.trim();
    const message = document.getElementById('feedbackMessage').value.trim();
    const ratingInput = form.querySelector('input[name="rating"]:checked');
    const rating = ratingInput ? parseInt(ratingInput.value, 10) : 5;

    if (!customerName || !message) {
      alertBox.textContent = 'Name and feedback message are required.';
      alertBox.className = 'availability-alert error';
      alertBox.style.display = 'block';
      return;
    }

    try {
      const submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';

      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          contact,
          booking_id: bookingId,
          rating,
          message
        })
      });

      const data = await res.json();
      submitBtn.disabled = false;
      submitBtn.textContent = 'SUBMIT FEEDBACK';

      if (!res.ok) {
        alertBox.textContent = data.error || 'Failed to submit feedback.';
        alertBox.className = 'availability-alert error';
        alertBox.style.display = 'block';
        return;
      }

      alertBox.textContent = data.message || 'Thank you for sharing your experience with Hotel Coastal Palace!';
      alertBox.className = 'availability-alert success';
      alertBox.style.display = 'block';
      form.reset();

      setTimeout(() => {
        closeModal('feedbackModal');
        alertBox.style.display = 'none';
      }, 2500);
    } catch (err) {
      alertBox.textContent = 'Server connection error. Please try again.';
      alertBox.className = 'availability-alert error';
      alertBox.style.display = 'block';
    }
  });
}

// --- Lightbox Gallery for Food & Restaurant Photos ---
function initLightbox() {
  const lightbox = document.getElementById('galleryLightbox');
  if (!lightbox) return;

  const imgEl = document.getElementById('lightboxImage');
  const captionEl = document.getElementById('lightboxCaption');
  const prevBtn = document.getElementById('lightboxPrev');
  const nextBtn = document.getElementById('lightboxNext');
  const closeBtn = document.getElementById('lightboxClose');

  const updateLightbox = () => {
    if (currentLightboxItems.length === 0) return;
    const item = currentLightboxItems[currentLightboxIndex];
    imgEl.src = item.src;
    imgEl.alt = item.caption || 'Hotel Coastal Palace Photo';
    captionEl.textContent = item.caption || '';
  };

  const showNext = () => {
    currentLightboxIndex = (currentLightboxIndex + 1) % currentLightboxItems.length;
    updateLightbox();
  };

  const showPrev = () => {
    currentLightboxIndex = (currentLightboxIndex - 1 + currentLightboxItems.length) % currentLightboxItems.length;
    updateLightbox();
  };

  prevBtn?.addEventListener('click', showPrev);
  nextBtn?.addEventListener('click', showNext);
  closeBtn?.addEventListener('click', () => lightbox.classList.remove('active'));

  // Keyboard controls
  window.addEventListener('keydown', (e) => {
    if (!lightbox.classList.contains('active')) return;
    if (e.key === 'Escape') lightbox.classList.remove('active');
    if (e.key === 'ArrowRight') showNext();
    if (e.key === 'ArrowLeft') showPrev();
  });

  // Food cards trigger
  document.querySelectorAll('.food-item-card').forEach((card, index, allCards) => {
    card.addEventListener('click', () => {
      currentLightboxItems = Array.from(allCards).map(c => ({
        src: c.querySelector('img').src,
        caption: c.querySelector('.food-title').textContent + ' — ' + (c.querySelector('.food-desc')?.textContent || '')
      }));
      currentLightboxIndex = index;
      updateLightbox();
      lightbox.classList.add('active');
    });
  });
}

// --- Click Backdrop Outside to Close Modal ---
function initBackdropClose() {
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        closeModal(backdrop.id);
      }
    });
  });
}

// --- Generic Modal Helpers ---
window.openModal = function(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
};

window.closeModal = function(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.remove('active');
    document.body.style.overflow = '';
  }
};
