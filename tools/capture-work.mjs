// Capture portfolio card screenshots of a live demo: desktop (1200x750) and phone (480x1039)
// usage: node tools/capture-work.mjs <key> <url> [scrollY]
import { chromium } from 'playwright';
const [k, url] = process.argv.slice(2);
const b = await chromium.launch();
const shoot = async (vp, scale, file) => {
  const p = await b.newPage({ viewport: vp, deviceScaleFactor: scale, isMobile: vp.width < 600, hasTouch: vp.width < 600 });
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.waitForTimeout(7000); // let the intro finish
  await p.addStyleTag({ content: '.pd-ribbon,.dock,.toast{display:none!important}' });
  await p.screenshot({ path: file, type: 'jpeg', quality: 82 });
  await p.close();
};
await shoot({ width: 1440, height: 900 }, 1200 / 1440, `assets/work/${k}-d.jpg`);
await shoot({ width: 390, height: 844 }, 480 / 390, `assets/work/${k}-p.jpg`);
await b.close();
console.log('captured', k);
