(() => {
  'use strict';

  const initialiseSharedHeader = () => {
    const header = document.querySelector('.site-header[data-shared-layout="header"]');
    if (!header) return;

    const brand = header.querySelector('.brand');
    if (brand instanceof HTMLElement) {
      brand.setAttribute('aria-label', 'AirAdmin8 Robotics ホームへ戻る');
      brand.innerHTML = `
        <img class="brand-logo brand-logo-pc" src="/assets/img/airadmin8-robotics-logo-pc.svg?v=20260805-2" alt="AirAdmin8 Robotics" width="193" height="40">
        <img class="brand-logo brand-logo-sp" src="/assets/img/airadmin8-robotics-logo-sp.svg?v=20260805-2" alt="AirAdmin8 Robotics" width="154" height="32">`;
    }

    const currentButton = header.querySelector('.menu');
    const navigation = header.querySelector('.nav');
    if (!(currentButton instanceof HTMLButtonElement) || !(navigation instanceof HTMLElement)) return;

    const menuButton = currentButton.cloneNode(true);
    currentButton.replaceWith(menuButton);
    menuButton.dataset.menuReady = 'true';

    const closeMenu = () => {
      navigation.classList.remove('open');
      menuButton.setAttribute('aria-expanded', 'false');
    };

    menuButton.addEventListener('click', () => {
      const isOpen = navigation.classList.toggle('open');
      menuButton.setAttribute('aria-expanded', String(isOpen));
    });

    navigation.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMenu();
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialiseSharedHeader, { once: true });
  } else {
    initialiseSharedHeader();
  }
})();
