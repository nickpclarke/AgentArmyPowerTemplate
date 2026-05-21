const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--ignore-certificate-errors']
  });

  const url = 'https://nickpclarke.github.io/AgentArmy/big4-network.html';

  // ── Desktop Test ──────────────────────────────────────────────────────────
  console.log('\n=== DESKTOP TEST (1280x800) ===');
  const desktopCtx = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    ignoreHTTPSErrors: true,
  });
  const desktopPage = await desktopCtx.newPage();

  const desktopConsoleErrors = [];
  const desktopNetworkErrors = [];
  desktopPage.on('console', msg => {
    if (msg.type() === 'error') desktopConsoleErrors.push(msg.text());
    else console.log(`[console.${msg.type()}] ${msg.text()}`);
  });
  desktopPage.on('pageerror', err => desktopConsoleErrors.push(`PAGE ERROR: ${err.message}`));
  desktopPage.on('requestfailed', req => desktopNetworkErrors.push(`${req.failure()?.errorText} - ${req.url()}`));

  await desktopPage.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

  // Hard reload
  await desktopPage.keyboard.down('Control');
  await desktopPage.keyboard.down('Shift');
  await desktopPage.keyboard.press('r');
  await desktopPage.keyboard.up('Shift');
  await desktopPage.keyboard.up('Control');
  await desktopPage.waitForTimeout(3000);
  await desktopPage.waitForLoadState('networkidle');

  // Wait for simulation to settle
  await desktopPage.waitForTimeout(4000);

  // Screenshot
  await desktopPage.screenshot({
    path: '/home/user/AgentArmy/screenshots/desktop-1280x800.png',
    fullPage: false
  });
  console.log('Desktop screenshot saved.');

  // Canvas state check
  const canvasInfo = await desktopPage.evaluate(() => {
    const canvas = document.getElementById('graph');
    const rect = canvas.getBoundingClientRect();
    const ctx = canvas.getContext('2d');
    // Sample pixels around centre to see if canvas is blank
    const cx = Math.floor(canvas.width / 2);
    const cy = Math.floor(canvas.height / 2);
    const imageData = ctx.getImageData(cx - 50, cy - 50, 100, 100);
    const pixels = imageData.data;
    let nonBlank = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      if (pixels[i] !== 0 || pixels[i+1] !== 0 || pixels[i+2] !== 0 || pixels[i+3] !== 0) {
        nonBlank++;
      }
    }
    return {
      canvasWidth: canvas.width,
      canvasHeight: canvas.height,
      domWidth: rect.width,
      domHeight: rect.height,
      top: rect.top,
      bottom: rect.bottom,
      nonBlankPixels: nonBlank,
      totalSampledPixels: pixels.length / 4,
    };
  });
  console.log('Canvas info:', JSON.stringify(canvasInfo, null, 2));

  // Wide pixel sweep to detect graph content anywhere on canvas
  const wideSweep = await desktopPage.evaluate(() => {
    const canvas = document.getElementById('graph');
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const imageData = ctx.getImageData(0, 0, w, h);
    const pixels = imageData.data;
    let nonBlank = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      if (pixels[i] !== 0 || pixels[i+1] !== 0 || pixels[i+2] !== 0 || pixels[i+3] !== 0) {
        nonBlank++;
      }
    }
    return { totalPixels: pixels.length / 4, nonBlankPixels: nonBlank, pct: ((nonBlank / (pixels.length/4))*100).toFixed(2) };
  });
  console.log('Full canvas pixel sweep:', JSON.stringify(wideSweep));

  // Filter chip text
  const chips = await desktopPage.evaluate(() => {
    const chips = document.querySelectorAll('.chip');
    return Array.from(chips).map(c => ({
      text: c.textContent.trim(),
      active: c.classList.contains('active'),
      filter: c.dataset.filter,
      val: c.dataset.val
    }));
  });
  console.log('\nFilter chips:');
  chips.forEach(c => console.log(`  [${c.active ? 'ACTIVE' : '      '}] ${c.text} (filter=${c.filter}, val=${c.val})`));

  // Node/link state
  const simState = await desktopPage.evaluate(() => {
    // Access global variables through window — in module-less scripts they are global
    return {
      nodesLength: window.nodes ? window.nodes.length : 'N/A',
      linksLength: window.links ? window.links.length : 'N/A',
      simAlpha: window.sim ? window.sim.alpha() : 'N/A',
      transformK: window.transform ? window.transform.k : 'N/A',
      firstNodeXY: window.nodes ? `x=${window.nodes[0].x?.toFixed(1)}, y=${window.nodes[0].y?.toFixed(1)}` : 'N/A',
    };
  });
  console.log('\nSimulation state:', JSON.stringify(simState, null, 2));

  // DOM layout checks
  const layoutCheck = await desktopPage.evaluate(() => {
    const hdr = document.querySelector('.hdr');
    const filters = document.querySelector('.filters');
    const canvas = document.getElementById('graph');
    const legend = document.querySelector('.legend');
    const hdrRect = hdr ? hdr.getBoundingClientRect() : null;
    const filterRect = filters ? filters.getBoundingClientRect() : null;
    const canvasRect = canvas ? canvas.getBoundingClientRect() : null;
    const legendRect = legend ? legend.getBoundingClientRect() : null;
    return {
      header: hdrRect ? { top: hdrRect.top, height: hdrRect.height, bottom: hdrRect.bottom } : null,
      filters: filterRect ? { top: filterRect.top, height: filterRect.height, bottom: filterRect.bottom } : null,
      canvas: canvasRect ? { top: canvasRect.top, height: canvasRect.height, bottom: canvasRect.bottom } : null,
      legend: legendRect ? { top: legendRect.top, height: legendRect.height, bottom: legendRect.bottom } : null,
      windowH: window.innerHeight,
      windowW: window.innerWidth,
    };
  });
  console.log('\nLayout check:', JSON.stringify(layoutCheck, null, 2));

  console.log('\nDesktop console errors:', desktopConsoleErrors.length ? desktopConsoleErrors : 'None');
  console.log('Desktop network errors:', desktopNetworkErrors.length ? desktopNetworkErrors : 'None');

  await desktopCtx.close();

  // ── Mobile Test ──────────────────────────────────────────────────────────
  console.log('\n\n=== MOBILE TEST (390x844) ===');
  const mobileCtx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
    ignoreHTTPSErrors: true,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
  });
  const mobilePage = await mobileCtx.newPage();

  const mobileConsoleErrors = [];
  const mobileNetworkErrors = [];
  mobilePage.on('console', msg => {
    if (msg.type() === 'error') mobileConsoleErrors.push(msg.text());
    else console.log(`[console.${msg.type()}] ${msg.text()}`);
  });
  mobilePage.on('pageerror', err => mobileConsoleErrors.push(`PAGE ERROR: ${err.message}`));
  mobilePage.on('requestfailed', req => mobileNetworkErrors.push(`${req.failure()?.errorText} - ${req.url()}`));

  await mobilePage.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  await mobilePage.waitForTimeout(4000);

  await mobilePage.screenshot({
    path: '/home/user/AgentArmy/screenshots/mobile-390x844.png',
    fullPage: false
  });
  console.log('Mobile screenshot saved.');

  const mobileCanvasInfo = await mobilePage.evaluate(() => {
    const canvas = document.getElementById('graph');
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const w = canvas.width;
    const h = canvas.height;
    if (w === 0 || h === 0) return { canvasWidth: w, canvasHeight: h, nonBlankPixels: 0, domRect: rect };
    const imageData = ctx.getImageData(0, 0, w, h);
    const pixels = imageData.data;
    let nonBlank = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      if (pixels[i] !== 0 || pixels[i+1] !== 0 || pixels[i+2] !== 0 || pixels[i+3] !== 0) {
        nonBlank++;
      }
    }
    return {
      canvasWidth: w,
      canvasHeight: h,
      domRectTop: rect.top,
      domRectHeight: rect.height,
      nonBlankPixels: nonBlank,
      totalPixels: pixels.length / 4,
      pct: ((nonBlank / (pixels.length/4))*100).toFixed(2)
    };
  });
  console.log('Mobile canvas info:', JSON.stringify(mobileCanvasInfo, null, 2));

  const mobileLayout = await mobilePage.evaluate(() => {
    const hdr = document.querySelector('.hdr');
    const filters = document.querySelector('.filters');
    const canvas = document.getElementById('graph');
    const hdrRect = hdr?.getBoundingClientRect();
    const filterRect = filters?.getBoundingClientRect();
    const canvasRect = canvas?.getBoundingClientRect();
    return {
      header: hdrRect ? { top: hdrRect.top, height: hdrRect.height } : null,
      filters: filterRect ? { top: filterRect.top, height: filterRect.height } : null,
      canvas: canvasRect ? { top: canvasRect.top, height: canvasRect.height, bottom: canvasRect.bottom } : null,
      windowH: window.innerHeight,
      windowW: window.innerWidth,
    };
  });
  console.log('Mobile layout:', JSON.stringify(mobileLayout, null, 2));

  console.log('\nMobile console errors:', mobileConsoleErrors.length ? mobileConsoleErrors : 'None');
  console.log('Mobile network errors:', mobileNetworkErrors.length ? mobileNetworkErrors : 'None');

  await mobileCtx.close();
  await browser.close();
  console.log('\n=== TEST COMPLETE ===');
})();
