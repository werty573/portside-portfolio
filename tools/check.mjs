// Playwright check: serve the folder, load the page, report console errors, screenshot desktop + phone at a few scroll points
// node tools/check.mjs <outdir>
import { chromium } from 'playwright';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1')), '..');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.png': 'image/png', '.bin': 'application/octet-stream', '.json': 'application/json', '.svg': 'image/svg+xml' };
const server = http.createServer((q, r) => { let p = decodeURIComponent(q.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html'; const f = path.join(root, p);
  if (!f.startsWith(root) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); }).listen(5180);
const out = process.argv[2] || 'shots';
const b = await chromium.launch({ args: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'] });
for (const [name, vp, mob] of [['desk', { width: 1440, height: 900 }, false], ['phone', { width: 390, height: 844 }, true]]) {
  const ctx = await b.newContext({ viewport: vp, deviceScaleFactor: mob ? 2 : 1, isMobile: mob, hasTouch: mob });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
  await p.goto('http://localhost:5180/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(6500);
  await p.screenshot({ path: `${out}/pf-${name}-0.png` });
  const H = await p.evaluate(() => document.documentElement.scrollHeight);
  for (const [k, f] of [[1, .12], [2, .2], [3, .32], [4, .45], [5, .62], [6, .8], [7, 1]].entries()) {
    await p.evaluate(y => window.scrollTo(0, y), Math.round((H - vp.height) * f[1]));
    await p.waitForTimeout(2200);
    await p.screenshot({ path: `${out}/pf-${name}-${f[0]}.png` });
  }
  console.log(name, 'height', H, errs.length ? errs.join(' | ') : 'no errors');
  await ctx.close();
}
await b.close(); server.close();
