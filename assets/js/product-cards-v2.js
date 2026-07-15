(() => {
  'use strict';

  const priorityMap = {
    'unitree-g1-d': { order: 1, label: '大学研究・VLA向け' },
    'agibot-g2': { order: 2, label: '移動操作・PoC向け' },
    'unitree-g1': { order: 3, label: '人型研究向け' },
    'unitree-go2-edu': { order: 4, label: '教育・移動研究向け' },
    'agibot-x2-edu': { order: 5, label: '研究教育向け' },
    'tianji-marvin': { order: 6, label: 'データ収集構成' },
    'limx-oli': { order: 7, label: '全身制御研究向け' },
  };

  document.querySelectorAll('[data-product-list]').forEach((root) => {
    const enhance = () => {
      const cards = [...root.querySelectorAll('.research-product-card')];
      if (!cards.length) return false;

      cards.forEach((card) => {
        const config = priorityMap[card.id] || { order: 99, label: '比較対象' };
        card.dataset.productOrder = String(config.order);

        if (!card.querySelector('.product-priority-ribbon')) {
          const ribbon = document.createElement('span');
          ribbon.className = 'product-priority-ribbon';
          ribbon.textContent = config.label;
          card.prepend(ribbon);
        }

        const body = card.querySelector('.product-body');
        const maker = card.querySelector('.product-maker');
        if (body && maker && !body.querySelector('.product-category-label')) {
          const category = document.createElement('p');
          category.className = 'product-category-label';
          category.textContent = inferCategory(card);
          maker.insertAdjacentElement('afterend', category);
        }

        const imageNote = card.querySelector('.image-note');
        if (imageNote) imageNote.textContent = '参考イメージ';
      });

      cards
        .sort((a, b) => Number(a.dataset.productOrder) - Number(b.dataset.productOrder))
        .forEach((card) => root.appendChild(card));

      if (!root.previousElementSibling?.classList.contains('product-list-summary')) {
        const summary = document.createElement('div');
        summary.className = 'product-list-summary';
        summary.innerHTML = `<strong>${cards.length}製品を比較</strong><span>価格・納期・SDK・取扱状態を正式見積前に確認します。</span>`;
        root.insertAdjacentElement('beforebegin', summary);
      }

      return true;
    };

    if (enhance()) return;

    const observer = new MutationObserver(() => {
      if (!enhance()) return;
      observer.disconnect();
    });
    observer.observe(root, { childList: true });
  });

  function inferCategory(card) {
    const groups = (card.dataset.productGroups || '').split(' ');
    if (groups.includes('mobile-manipulation')) return '移動操作・データ収集';
    if (groups.includes('quadruped')) return '四足・移動研究';
    if (groups.includes('arm')) return 'アーム・操作';
    if (groups.includes('education')) return '研究・教育';
    if (groups.includes('humanoid')) return 'ヒューマノイド';
    return 'AIロボット';
  }
})();