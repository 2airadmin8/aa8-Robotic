import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://robotics.air-admin8.co.jp',
  trailingSlash: 'always',
  build: { format: 'directory' },
});
