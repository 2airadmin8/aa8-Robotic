(() => {
  'use strict';

  const stylesheet = document.querySelector('link[href*="main-site-experience.css"]');
  const baseUrl = stylesheet
    ? new URL(stylesheet.getAttribute('href'), document.baseURI).href.replace(/assets\/css\/main-site-experience\.css(?:\?[^#]*)?$/, '')
    : new URL('./', document.baseURI).href;

  const makeUrl = (path) => new URL(path, baseUrl).href;
  const logoMarkup = `<img class="aa8-main-logo" src="${makeUrl('assets/img/airadmin8-official-logo.png?v=20260731-1')}" alt="AirAdmin8">`;

  document.querySelectorAll(
    '.site-header .brand, .header .brand, header[role="banner"] .brand, .mobile-menu .brand, .drawer .brand, .menu-drawer .brand, .nav-drawer .brand'
  ).forEach((brand) => {
    if (!(brand instanceof HTMLElement)) return;
    brand.setAttribute('aria-label', 'AirAdmin8 ロボティクス ホーム');
    brand.innerHTML = logoMarkup;
  });

  document.querySelectorAll('.site-footer strong, .site-footer .footer-brand, footer .brand').forEach((brand) => {
    if (!(brand instanceof HTMLElement)) return;
    brand.classList.add('aa8-footer-brand');
    brand.innerHTML = logoMarkup;
  });

  const topButton = document.createElement('button');
  topButton.className = 'aa8-back-to-top';
  topButton.type = 'button';
  topButton.setAttribute('aria-label', 'ページ上部へ戻る');
  topButton.setAttribute('title', 'ページ上部へ戻る');
  topButton.innerHTML = '<span aria-hidden="true">↑</span>';
  topButton.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  document.body.appendChild(topButton);

  const updateTopButton = () => topButton.classList.toggle('is-visible', window.scrollY > 480);
  window.addEventListener('scroll', updateTopButton, { passive: true });
  updateTopButton();

  // モバイル共通クイックメニューは廃止。
  // ヘッダー右側の「メニュー」に導線を一本化し、ファーストビューを圧迫しない。
  document.querySelectorAll('.aa8-mobile-quicknav').forEach((nav) => nav.remove());

  document.querySelectorAll('[id]').forEach((node) => {
    if (node instanceof HTMLElement) node.style.scrollMarginTop = '96px';
  });
})();
