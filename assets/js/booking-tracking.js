(function () {
  'use strict';

  const bookingUrl = 'https://calendar.app.google/ZnqVPUCv3rLN1pjy6';
  const params = new URLSearchParams(window.location.search);
  const deliveryId = params.get('rid') || 'unknown';
  const link = document.getElementById('booking-link');
  let opened = false;

  function openBooking() {
    if (opened) return;
    opened = true;
    window.location.replace(bookingUrl);
  }

  if (link) link.href = bookingUrl;

  window.addEventListener('load', function () {
    if (typeof window.gtag === 'function') {
      window.gtag('event', 'booking_click', {
        delivery_id: deliveryId,
        source: 'university_sales',
        transport_type: 'beacon',
        event_callback: openBooking
      });
    }

    setTimeout(openBooking, 1200);
  }, { once: true });
})();
