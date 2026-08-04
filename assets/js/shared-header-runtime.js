(() => {
  'use strict';

  const closeMenu = () => {
    const header = document.querySelector('.site-header[data-shared-layout="header"]');
    if (!header) return;
    const button = header.querySelector('.menu');
    const navigation = header.querySelector('.nav');
    navigation?.classList.remove('open');
    button?.setAttribute('aria-expanded', 'false');
  };

  const restoreOfficialLogo = () => {
    const header = document.querySelector('.site-header[data-shared-layout="header"]');
    const brand = header?.querySelector('.brand');
    if (!(brand instanceof HTMLElement)) return;

    brand.setAttribute('aria-label', 'AirAdmin8 Robotics ホームへ戻る');
    brand.innerHTML = `
      <img class="brand-logo brand-logo-pc" src="/assets/img/airadmin8-robotics-logo-pc.svg?v=20260805-3" alt="AirAdmin8 Robotics" width="193" height="40">
      <img class="brand-logo brand-logo-sp" src="/assets/img/airadmin8-robotics-logo-sp.svg?v=20260805-3" alt="AirAdmin8 Robotics" width="154" height="32">`;
  };

  document.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    const menuButton = target.closest('.site-header[data-shared-layout="header"] .menu');
    if (menuButton instanceof HTMLButtonElement) {
      event.preventDefault();
      event.stopImmediatePropagation();

      const header = menuButton.closest('.site-header[data-shared-layout="header"]');
      const navigation = header?.querySelector('.nav');
      if (!(navigation instanceof HTMLElement)) return;

      const isOpen = navigation.classList.toggle('open');
      menuButton.setAttribute('aria-expanded', String(isOpen));
      menuButton.dataset.menuReady = 'true';
      return;
    }

    if (target.closest('.site-header[data-shared-layout="header"] .nav a')) {
      closeMenu();
    }
  }, true);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restoreOfficialLogo, { once: true });
  } else {
    restoreOfficialLogo();
  }

  window.addEventListener('load', restoreOfficialLogo, { once: true });
})();
