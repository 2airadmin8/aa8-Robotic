(function () {
  'use strict';

  const pdfUrl = '/assets/pdf/AirAdmin8_AI_Robotics_Support_for_University_Labs.pdf';
  const params = new URLSearchParams(window.location.search);
  const deliveryId = params.get('rid') || 'unknown';
  const link = document.getElementById('pdf-link');
  let opened = false;

  function openPdf() {
    if (opened) return;
    opened = true;
    window.location.replace(pdfUrl);
  }

  if (link) link.href = pdfUrl;

  window.addEventListener('load', function () {
    if (typeof window.gtag === 'function') {
      window.gtag('event', 'pdf_open', {
        delivery_id: deliveryId,
        document_name: 'university_ai_robot_guide',
        document_path: pdfUrl,
        transport_type: 'beacon',
        event_callback: openPdf
      });
    }
    setTimeout(openPdf, 1500);
  }, { once: true });
})();
