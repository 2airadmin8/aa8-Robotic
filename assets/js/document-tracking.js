(function () {
  'use strict';

  const pdfUrl = '/assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf';
  const WEB_EVENT_ENDPOINT = 'https://hikari-proxy-dev.vercel.app/api/web-event';
  const params = new URLSearchParams(window.location.search);
  const deliveryId = (params.get('rid') || '').trim();
  const link = document.getElementById('pdf-link');
  let opened = false;

  function validDeliveryId(value) {
    return /^DLV-[A-Za-z0-9._-]+$/.test(value);
  }

  function emitDirectPdfEvent() {
    if (!validDeliveryId(deliveryId)) return;
    const body = JSON.stringify({
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
        delivery_id: deliveryId || 'unknown',
        document_name: 'university_ai_robot_guide',
        document_path: pdfUrl,
        transport_type: 'beacon',
        event_callback: openPdf
      });
    }
    setTimeout(openPdf, 1500);
  }, { once: true });
})();
