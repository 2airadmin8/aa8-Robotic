import fs from 'node:fs/promises';
import path from 'node:path';
import { createServer } from 'vite';
import React from 'react';
import { renderToString } from 'react-dom/server';
const root = process.cwd();
const server = await createServer({ root, server: { middlewareMode: true }, appType: 'custom' });
try {
  const { default: App } = await server.ssrLoadModule('/src/App.tsx');
  const body = renderToString(React.createElement(App));
  const out = path.join(root, 'dist/index.html');
  let html = await fs.readFile(out, 'utf8');
  if (!html.includes('<div id="root"></div>')) throw Error('Missing root');
  html = html.replace('<div id="root"></div>', '<div id="root">' + body + '</div>');
  await fs.writeFile(out, html, 'utf8');
  if (!html.includes('X2 EDU') || !html.includes('ROS2')) throw Error('SSR content missing');
  console.log('SEO prerender complete');
} finally { await server.close(); }
