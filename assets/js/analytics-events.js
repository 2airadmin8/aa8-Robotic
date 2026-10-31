(() => {
  'use strict';

  const pagePath = window.location.pathname;
  const pageType = detectPageType();
  const RID_STORAGE_KEY = 'aa8_delivery_id';
  const RID_AT_KEY = 'aa8_delivery_id_at';
  const RID_TTL_MS = 30 * 60 * 1000; // No cross-session customer misattribution.
  const RID_RE = /^(?:DLV|RSJ)-[A-Za-z0-9._-]{5,153}$/;
  const WEB_EVENT_ENDPOINT = 'https://hikari-proxy-dev.vercel.app/api/web-event';
  const params = new URLSearchParams(window.location.search);
  const deliveryId = resolveDeliveryId();
  const productId = detectProductId();

  function resolveDeliveryId() {
    const fromUrl = (params.get('rid') || '').trim();
    if (fromUrl && RID_RE.test(fromUrl)) {
      try {
        sessionStorage.setItem(RID_STORAGE_KEY, fromUrl);
        sessionStorage.setItem(RID_AT_KEY, String(Date.now()));
      } catch (_) {}
      return fromUrl;
    }
    if (fromUrl) return ''; // Invalid or injected attribution ID: do not trust stale storage.
    try {
      const id = sessionStorage.getItem(RID_STORAGE_KEY) || '';
      const at = Number(sessionStorage.getItem(RID_AT_KEY) || 0);
      if (RID_RE.test(id) && at > 0 && Date.now() - at <= RID_TTL_MS && Date.now() >= at) return id;
      sessionStorage.removeItem(RID_STORAGE_KEY);
      sessionStorage.removeItem(RID_AT_KEY);
    } catch (_) {}
    return '';
  }

  function campaignParam(name) {
    const fromUrl = (params.get(name) || '').trim();
    if (fromUrl && /^[A-Za-z0-9._-]{1,80}$/.test(fromUrl)) {
      try { sessionStorage.setItem('aa8_' + name, fromUrl); } catch (_) {}
      return fromUrl;
    }
    if (!deliveryId) return '';
    try {
      const prior = sessionStorage.getItem('aa8_' + name) || '';
      return /^[A-Za-z0-9._-]{1,80}$/.test(prior) ? prior : '';
    } catch (_) { return ''; }
  }

  function emitWebEvent(eventName, payload) {
    const accepted = ['lead_page_view', 'lead_product_click', 'product_view',
      'lead_contact_click', 'lead_inquiry_success'];
    if (!deliveryId || !RID_RE.test(deliveryId) || !accepted.includes(eventName)) return;
    if (!window.crypto || typeof window.crypto.randomUUID !== 'function') return;
    const body = JSON.stringify({
      event_id: window.crypto.randomUUID(),
      event_at: new Date().toISOString(),
      event: eventName,
      delivery_id: deliveryId,
      page_path: payload.page_path,
      page_type: payload.page_type,
      product_id: payload.product_id,
      target_product_id: payload.target_product_id,
      target_path: payload.target_path,
    });
    // Browser sendBeacon=true only means queued, NOT persisted. Backend will
    // return 202 exclusively after the existing GAS sheet acknowledges writes.
    try {
      fetch(WEB_EVENT_ENDPOINT, {
        method: 'POST', mode: 'cors', keepalive: true,
        headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, body
      }).catch(() => {});
    } catch (_) {
      try {
        if (navigator.sendBeacon) navigator.sendBeacon(
          WEB_EVENT_ENDPOINT, new Blob([body], { type: 'text/plain;charset=UTF-8' })
        );
      } catch (_) {}
    }
  }

  function send(eventName, parameters = {}) {
    const payload = {
      page_path: pagePath,
      page_type: pageType,
      delivery_id: deliveryId || undefined,
      product_id: productId || undefined,
      ...sanitize(parameters),
    };

    // Never expose delivery_id (a customer-join key) or full rid-bearing URL
    // to GA4 or shared dataLayer; send those only to our own signed sink.
    const gaPayload = { ...payload };
    delete gaPayload.delivery_id;
    delete gaPayload.page_location;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: eventName, ...gaPayload });
    if (typeof window.gtag === 'function') window.gtag('event', eventName, gaPayload);
    emitWebEvent(eventName, payload);
  }

  function sanitize(values) {
    return Object.fromEntries(Object.entries(values).filter(([, value]) => (
      value !== undefined && value !== null && value !== ''
    )));
  }

  function detectPageType() {
    if (pagePath.endsWith('/products.html')) return 'product_hub';
    if (pagePath.includes('/products/')) return 'product_detail';
    if (pagePath.endsWith('/checklist.html')) return 'checklist';
    if (pagePath.endsWith('/contact.html')) return 'contact';
    if (pagePath.includes('/use-cases/')) return 'use_case_detail';
    if (pagePath.endsWith('/use-cases.html')) return 'use_case_hub';
    if (pagePath.includes('/support/')) return 'support_detail';
    if (pagePath.endsWith('/support.html')) return 'support_hub';
    if (pagePath.endsWith('/resources.html')) return 'resource_hub';
    if (pagePath.includes('/manufacturers/')) return 'manufacturer_detail';
    return 'content';
  }

  function detectProductId() {
    const match = pagePath.match(/\/products\/([^/?#]+?)(?:\.html)?$/i);
    return match ? match[1].replace(/\.html$/i, '') : '';
  }

  function decorateInternalLinks() {
    if (!deliveryId) return;
    document.querySelectorAll('a[href]').forEach((anchor) => {
      const raw = anchor.getAttribute('href') || '';
      if (!raw || raw.startsWith('#') || raw.startsWith('mailto:') || raw.startsWith('tel:') || raw.startsWith('javascript:')) return;
      try {
        const url = new URL(raw, window.location.href);
        if (url.origin !== window.location.origin) return;
        if (url.pathname.startsWith('/assets/')) return;
        if (!url.searchParams.get('rid')) url.searchParams.set('rid', deliveryId);
        ['utm_source', 'utm_medium', 'utm_campaign'].forEach((key) => {
          const campaign = campaignParam(key);
          if (campaign && !url.searchParams.get(key)) url.searchParams.set(key, campaign);
        });
        anchor.href = url.pathname + url.search + url.hash;
      } catch (_) {}
    });
  }

  if (deliveryId) {
    // Read and validate campaign attribution before rewriting internal links.
    ['utm_source', 'utm_medium', 'utm_campaign'].forEach(campaignParam);
    decorateInternalLinks();
    send('lead_page_view', {
      page_title: document.title,
      page_location: window.location.href,
    });
    if (productId) {
      send('product_view', {
        product_id: productId,
      });
    }
  }

  document.addEventListener('change', (event) => {
    const compareCheckbox = event.target.closest('[data-compare-checkbox]');
    if (compareCheckbox) {
      const selectedCount = document.querySelectorAll('[data-compare-checkbox]:checked').length;
      send(compareCheckbox.checked ? 'compare_product_add' : 'compare_product_remove', {
        product_id: compareCheckbox.value,
        selected_count: selectedCount,
      });
      return;
    }

    const checklistCheckbox = event.target.closest('[data-check-item] input[type="checkbox"]');
    if (checklistCheckbox) {
      const total = document.querySelectorAll('[data-check-item]').length;
      const checked = document.querySelectorAll('[data-check-item] input[type="checkbox"]:checked').length;
      send('checklist_progress', {
        checked_count: checked,
        total_count: total,
        completion_rate: total ? Math.round((checked / total) * 100) : 0,
      });
    }
  });

  document.addEventListener('click', (event) => {
    const target = event.target.closest('button, a');
    if (!target) return;

    if (target.tagName === 'A' && deliveryId) {
      try {
        const url = new URL(target.href, window.location.href);
        const match = url.pathname.match(/\/products\/([^/?#]+?)(?:\.html)?$/i);
        if (url.origin === window.location.origin && match) {
          send('lead_product_click', {
            target_product_id: match[1].replace(/\.html$/i, ''),
            target_path: url.pathname,
          });
        }
      } catch (_) {}
    }

    if (target.tagName === 'A' && deliveryId) {
      try {
        const destination = new URL(target.href, window.location.href);
        if (destination.origin === window.location.origin && destination.pathname === '/contact.html') {
          send('lead_contact_click', {target_path: '/contact.html'});
        }
      } catch (_) {}
    }
    if (target.matches('[data-compare-open]')) {
      send('compare_open', {
        selected_count: document.querySelectorAll('[data-compare-checkbox]:checked').length,
        theme: new URLSearchParams(window.location.search).get('theme') || undefined,
      });
    } else if (target.matches('[data-compare-copy]')) {
      send('compare_link_copy', { selected_count: selectedProductCount() });
    } else if (target.matches('[data-compare-print]')) {
      send('compare_pdf_print', { selected_count: selectedProductCount() });
    } else if (target.matches('[data-compare-consult]')) {
      send('compare_consult_click', { selected_count: selectedProductCount() });
    } else if (target.matches('[data-compare-clear]')) {
      send('compare_clear', { selected_count: selectedProductCount() });
    } else if (target.matches('[data-checklist-copy]')) {
      send('checklist_copy', checklistProgress());
    } else if (target.matches('[data-checklist-reset]')) {
      send('checklist_reset', checklistProgress());
    } else if (target.matches('[data-checklist-consult]')) {
      send('checklist_consult_click', checklistProgress());
    } else if (target.matches('[data-confirm-send]')) {
      const category = document.querySelector('[data-contact-form] [name="category"]')?.value || undefined;
      send('contact_mail_open', {
        inquiry_category: category,
        source_service: document.querySelector('[name="source_service"]')?.value || undefined,
        source_theme: document.querySelector('[name="source_theme"]')?.value || undefined,
      });
    } else if (target.matches('[data-copy-mail]')) {
      send('contact_copy_mail', {
        inquiry_category: document.querySelector('[data-contact-form] [name="category"]')?.value || undefined,
      });
    }
  });

  document.addEventListener('submit', (event) => {
    const form = event.target.closest('[data-contact-form]');
    if (!form) return;
    send('contact_review', {
      inquiry_category: form.elements.namedItem('category')?.value || undefined,
      source_service: form.elements.namedItem('source_service')?.value || undefined,
      source_theme: form.elements.namedItem('source_theme')?.value || undefined,
      has_product: Boolean(form.elements.namedItem('product')?.value),
      has_budget: Boolean(form.elements.namedItem('budget')?.value),
      has_schedule: Boolean(form.elements.namedItem('schedule')?.value),
    });
  }, true);

  document.addEventListener('aa8:inquiry-confirmed', () => {
    // This event is emitted ONLY after the original inquiry GAS confirms persistence.
    if (deliveryId && pagePath === '/contact.html') send('lead_inquiry_success');
  });

  function selectedProductCount() {
    return document.querySelectorAll('[data-compare-checkbox]:checked').length;
  }

  function checklistProgress() {
    const total = document.querySelectorAll('[data-check-item]').length;
    const checked = document.querySelectorAll('[data-check-item] input[type="checkbox"]:checked').length;
    return {
      checked_count: checked,
      total_count: total,
      completion_rate: total ? Math.round((checked / total) * 100) : 0,
    };
  }
})();
