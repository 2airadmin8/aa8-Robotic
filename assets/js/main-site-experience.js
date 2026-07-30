(() => {
  'use strict';

  const stylesheet = document.querySelector('link[href*="main-site-experience.css"]');
  const baseUrl = stylesheet
    ? new URL(stylesheet.getAttribute('href'), document.baseURI).href.replace(/assets\/css\/main-site-experience\.css(?:\?[^#]*)?$/, '')
    : new URL('./', document.baseURI).href;

  const makeUrl = (path) => new URL(path, baseUrl).href;

  const topButton = document.createElement('button');
  topButton.className = 'aa8-back-to-top';
  topButton.type = 'button';
  topButton.setAttribute('aria-label', 'ページ上部へ戻る');
  topButton.setAttribute('title', 'ページ上部へ戻る');
  topButton.innerHTML = '<span aria-hidden="true">↑</span>';
  topButton.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  document.body.appendChild(topButton);

  const updateTopButton = () => {
    topButton.classList.toggle('is-visible', window.scrollY > 480);
  };
  window.addEventListener('scroll', updateTopButton, { passive: true });
  updateTopButton();

  const quickNav = document.createElement('nav');
  quickNav.className = 'aa8-mobile-quicknav';
  quickNav.setAttribute('aria-label', 'モバイル共通メニュー');
  quickNav.innerHTML = [
    ['製品を探す', 'products.html'],
    ['用途から探す', 'use-cases.html'],
    ['導入を相談', 'contact.html']
  ].map(([label, path]) => `<a href="${makeUrl(path)}">${label}</a>`).join('');
  document.body.appendChild(quickNav);

  // 同一ページ内リンクは固定ヘッダーを考慮して読みやすい位置へ。
  document.querySelectorAll('[id]').forEach((node) => {
    if (node instanceof HTMLElement) node.style.scrollMarginTop = '96px';
  });
})();
