import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Set console listener
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err.message));

  console.log('Navigating to http://localhost:8080/student...');
  try {
    await page.goto('http://localhost:8080/student', { waitUntil: 'networkidle', timeout: 10000 });
    
    // Check for the ETA bar
    const etaBar = await page.$('#eta-message-bar');
    if (etaBar) {
      const isVisible = await etaBar.isVisible();
      const text = await etaBar.textContent();
      const style = await etaBar.evaluate(el => {
        const s = window.getComputedStyle(el);
        return {
          display: s.display,
          height: s.height,
          visibility: s.visibility,
          opacity: s.opacity,
          zIndex: s.zIndex,
          position: s.position,
          backgroundColor: s.backgroundColor
        };
      });
      
      console.log('ETA Bar found!');
      console.log('Visible:', isVisible);
      console.log('Text content:', text);
      console.log('Styles:', JSON.stringify(style, null, 2));
    } else {
      console.log('ETA Bar NOT found in DOM!');
    }

    // Check for map errors
    const errorBanner = await page.$('div:has-text("⚠️")');
    if (errorBanner) {
      console.log('Error banner detected:', await errorBanner.textContent());
    }

  } catch (err) {
    console.error('Failed to navigate:', err.message);
  }

  await browser.close();
})();
