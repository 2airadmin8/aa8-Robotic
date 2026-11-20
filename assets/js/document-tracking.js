(function () {
  'use strict';

  const pdfUrl = '/assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf';
  const WEB_EVENT_ENDPOINT = 'https://hikari-proxy-dev.vercel.app/api/web-event';
  const params = new URLSearchParams(window.location.search);
  const deliveryId = (params.get('rid') || '').trim();
  const link = document.getElementById('pdf-link');
  let opened = false;

  function validDeliveryId(value) {
    return /^(?:DLV|RSJ)-[A-Za-z0-9._-]{5,153}$/.test(value);
  }

  function emitDirectPdfEvent() {
    if (!validDeliveryId(deliveryId) || !window.crypto?.randomUUID) return;
    // PDF landing/redirect requested, not proof the PDF was read.
    const body = JSON.stringify({
      event_id: window.crypto.randomUUID(),
      event_at: new Date().toISOString(),
      event: 'pdf_open',
      delivery_id: deliveryId,
      page_path: window.location.pathname,
      page_type: 'document',
      document_name: 'university_ai_robot_guide'
    });

    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: 'text/plain;charset=UTF-8' });
        if (navigator.sendBeacon(WEB_EVENT_ENDPOINT, blob)) return;
      }
    } catch (_) {}

    try {
      fetch(WEB_EVENT_ENDPOINT, {
        method: 'POST',
        mode: 'cors',
        keepalive: true,
        headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
        body
      }).catch(() => {});
    } catch (_) {}
  }

  function openPdf() {
    if (opened) return;
    opened = true;
    window.location.replace(pdfUrl);
  }

  if (link) link.href = pdfUrl;

  window.addEventListener('load', function () {
    emitDirectPdfEvent();

    if (typeof window.gtag === 'function') {
      window.gtag('event', 'pdf_open', {
        // Delivery ID is sent exclusively to the signed first-party sink,
        // never to GA4 where it might be joinable to customer information.
        document_name: 'university_ai_robot_guide',
        document_path: pdfUrl,
        transport_type: 'beacon',
        event_callback: openPdf
      });
    }
    setTimeout(openPdf, 1500);
  }, { once: true });
})();
