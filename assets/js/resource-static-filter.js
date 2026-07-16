(() => {
  'use strict';

  const root = document.querySelector('[data-resource-list][data-prerendered-resources]');
  if (!root || !root.querySelector('.resource-card')) return;

  // site.jsによる再取得・再描画を止め、構築済みカードをそのまま使う。
  root.removeAttribute('data-resource-list');
  root.dataset.resourceStaticList = 'true';

  const form = document.querySelector('[data-resource-filter-form]');
  const count = document.querySelector('[data-resource-count]');
  const empty = document.querySelector('[data-resource-empty]');
  const cards = [...root.querySelectorAll('.resource-card')];

  const normalise = (value) => String(value || '').trim().toLowerCase();

  const readConditions = () => {
    if (!form) return {};
    const values = new FormData(form);
    return {
      maker: String(values.get('maker') || 'all'),
      product: String(values.get('product') || 'all'),
      type: String(values.get('type') || 'all'),
      keyword: String(values.get('keyword') || ''),
    };
  };

  const updateUrl = (conditions) => {
    const url = new URL(window.location.href);
    ['maker', 'product', 'type', 'keyword'].forEach((name) => {
      const value = conditions[name];
      if (!value || value === 'all') url.searchParams.delete(name);
      else url.searchParams.set(name, value);
    });
    window.history.replaceState({}, '', url);
  };

  const apply = (conditions = {}, shouldUpdateUrl = false) => {
    const maker = conditions.maker || 'all';
    const product = conditions.product || 'all';
    const type = conditions.type || 'all';
    const keyword = normalise(conditions.keyword);
    let visibleCount = 0;

    cards.forEach((card) => {
      const makers = card.dataset.resourceMaker || '';
      const products = (card.dataset.resourceProducts || '').split(/\s+/).filter(Boolean);
      const types = (card.dataset.resourceTypes || '').split(/\s+/).filter(Boolean);
      const searchableText = normalise(card.textContent);
      const visible = (maker === 'all' || makers === maker)
        && (product === 'all' || products.includes(product))
        && (type === 'all' || types.includes(type))
        && (!keyword || searchableText.includes(keyword));

      card.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    if (count) count.textContent = String(visibleCount);
    if (empty) empty.hidden = visibleCount !== 0;
    if (shouldUpdateUrl) updateUrl({ maker, product, type, keyword: conditions.keyword || '' });
  };

  const query = new URLSearchParams(window.location.search);
  const initialConditions = {
    maker: query.get('maker') || 'all',
    product: query.get('product') || 'all',
    type: query.get('type') || 'all',
    keyword: query.get('keyword') || '',
  };

  if (form) {
    Object.entries(initialConditions).forEach(([name, value]) => {
      const field = form.elements.namedItem(name);
      if (field && value) field.value = value;
    });

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      apply(readConditions(), true);
    });

    form.addEventListener('reset', () => {
      window.setTimeout(() => apply({}, true), 0);
    });
  }

  document.querySelectorAll('[data-resource-shortcut]').forEach((button) => {
    button.addEventListener('click', () => {
      const selectedType = button.dataset.resourceShortcut || 'all';
      const typeSelect = form?.elements.namedItem('type');
      if (typeSelect) typeSelect.value = selectedType;
      const conditions = { ...readConditions(), type: selectedType };
      apply(conditions, true);
      document.querySelector('#resource-search')?.scrollIntoView({ behavior: 'smooth' });
    });
  });

  apply(initialConditions);
})();
