# Legacy URL Policy

- Production origin is `https://robotics.air-admin8.co.jp/`.
- The historical repository prefix `/aa8-Robotic/` must never serve a styled 404 page for a page that still exists at the root URL.
- During build, every publishable root HTML page is mirrored as a lightweight redirect page under `_site/aa8-Robotic/`.
- Redirect pages use an absolute target URL, `noindex,follow`, canonical, meta refresh, and `location.replace`.
- CI must fail when a current HTML page has no corresponding legacy-prefix redirect.
