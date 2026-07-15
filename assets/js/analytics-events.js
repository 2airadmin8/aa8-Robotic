(() => {
  'use strict';

  const pagePath = window.location.pathname;
  const pageType = detectPageType();

  function send(eventName, parameters = {}) {
    const payload = {
      page_path: pagePath,
      page_type: pageType,
      ...sanitize(parameters),
    };

    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: eventName, ...payload });
    if (typeof window.gtag === 'function') window.gtag('event', eventName, payload);
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
    return 'content';
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
