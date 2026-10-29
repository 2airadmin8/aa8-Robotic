/* Unitree G1 official video: click-to-play embedded YouTube on our product page.
 * No video is re-uploaded. The official URL remains an accessible fallback. */
(() => {
  'use strict';
  const wrapper = document.querySelector('[data-g1-player]');
  if (!wrapper) return;
  const videoId = wrapper.getAttribute('data-video-id');
  if (videoId !== 'O5GphCrjx98') return;

  const start = (event) => {
    const isPoster = event && event.currentTarget &&
      event.currentTarget.classList.contains('g1-hero-video-poster');
    if (event) event.preventDefault();
    if (!wrapper.querySelector('iframe')) {
      const frame = document.createElement('iframe');
      frame.className = 'g1-video-iframe';
      frame.title = 'Unitree Robotics 公式動画：Unitree G1 Kungfu Kid V6.0';
      frame.src = 'https://www.youtube-nocookie.com/embed/' + videoId + '?autoplay=1&playsinline=1&rel=0';
      frame.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      frame.allowFullscreen = true;
      const poster = wrapper.querySelector('.g1-hero-video-poster');
      if (poster) poster.replaceWith(frame);
      else wrapper.appendChild(frame);
    }
    if (!isPoster) wrapper.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
  document.querySelectorAll('[data-g1-video-trigger]').forEach((trigger) => {
    trigger.addEventListener('click', start);
  });
})();
