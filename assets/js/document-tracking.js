(function () {
  'use strict';

  const pdfUrl = '/assets/pdf/%E3%80%90AirAdmin8%E3%80%91%E5%A4%A7%E5%AD%A6%E3%83%BB%E7%A0%94%E7%A9%B6%E6%A9%9F%E9%96%A2%E5%90%91%E3%81%91_AI%E3%83%AD%E3%83%9C%E3%83%83%E3%83%88%E5%B0%8E%E5%85%A5%E6%94%AF%E6%8F%B4%E3%81%AE%E3%81%94%E6%A1%88%E5%86%85.pdf';
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
        transport_type: 'beacon',
        event_callback: openPdf
      });
    }
    setTimeout(openPdf, 1500);
  }, { once: true });
})();
