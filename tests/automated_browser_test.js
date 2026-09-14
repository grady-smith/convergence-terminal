const puppeteer = require('puppeteer');

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE_URL = 'http://localhost:8080';

const VIEWPORTS = [
  { name: 'Desktop Large', width: 1440, height: 900, expectedCols: 2 },
  { name: 'Desktop Medium', width: 1024, height: 768, expectedCols: 2 },
  { name: 'Tablet', width: 768, height: 1024, expectedCols: 1 },
  { name: 'Mobile', width: 390, height: 844, expectedCols: 1 }
];

async function runTests() {
  console.log('🚀 Launching automated browser tests with local Chrome...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  let totalErrors = 0;

  try {
    const page = await browser.newPage();

    // Listen for console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('pageerror', err => {
      consoleErrors.push(err.toString());
    });

    console.log(`🌐 Navigating to ${BASE_URL}...`);
    await page.goto(BASE_URL, { waitUntil: 'networkidle0' });

    // 1. Check Console Errors
    console.log('\n--- Test 1: Console Errors ---');
    if (consoleErrors.length > 0) {
      console.error('❌ Console errors detected:', consoleErrors);
      totalErrors += consoleErrors.length;
    } else {
      console.log('✅ No console errors during initial page load.');
    }

    // Wait for signal cards to be present
    await page.waitForSelector('#signals-container article', { timeout: 5000 });

    // 2. Check for Duplicate Content
    console.log('\n--- Test 2: Duplicate Content Detection ---');
    const duplicateReport = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('#signals-container article'));
      const postUrls = [];
      const contentFingerprints = [];
      const issues = [];

      cards.forEach((card, idx) => {
        const headline = card.querySelector('h2')?.textContent?.trim() || '';
        const summary = card.querySelector('p')?.textContent?.trim() || '';
        const entity = card.querySelector('h3')?.textContent?.trim() || '';
        const category = card.querySelector('.font-mono')?.textContent?.trim() || '';
        const sourceLink = card.querySelector('a[href*="http"]')?.getAttribute('href') || '';

        // Check specific post URLs (exclude profile/root links)
        if (sourceLink && !sourceLink.endsWith('.com/') && !sourceLink.endsWith('.org/') && !sourceLink.endsWith('/releases')) {
          if (postUrls.includes(sourceLink)) {
            issues.push(`Duplicate post source_url found in card ${idx + 1}: ${sourceLink}`);
          } else {
            postUrls.push(sourceLink);
          }
        }

        // Check fingerprint (entity + headline + first 40 chars of summary)
        const fp = `${entity}::${headline}::${summary.substring(0, 40)}`;
        if (contentFingerprints.includes(fp)) {
          issues.push(`Duplicate content fingerprint in card ${idx + 1} (${entity}): "${headline}"`);
        } else {
          contentFingerprints.push(fp);
        }
      });

      return { totalCards: cards.length, issues };
    });

    console.log(`Total signal cards rendered: ${duplicateReport.totalCards}`);
    if (duplicateReport.issues.length > 0) {
      console.error('❌ Duplicate content detected:');
      duplicateReport.issues.forEach(iss => console.error('   - ' + iss));
      totalErrors += duplicateReport.issues.length;
    } else {
      console.log(`✅ All ${duplicateReport.totalCards} cards have unique content. Zero duplicates!`);
    }

    // 3. Test Viewports and Element Spilling / Overflow
    console.log('\n--- Test 3: Overflow & Element Spilling across Viewports ---');

    for (const vp of VIEWPORTS) {
      console.log(`\nTesting viewport: ${vp.name} (${vp.width}x${vp.height})...`);
      await page.setViewport({ width: vp.width, height: vp.height });
      await new Promise(r => setTimeout(r, 400));

      const overflowReport = await page.evaluate(() => {
        const docEl = document.documentElement;
        const body = document.body;
        const windowWidth = window.innerWidth;
        const issues = [];

        // Check overall horizontal scroll
        const pageScrollWidth = Math.max(docEl.scrollWidth, body.scrollWidth);
        if (pageScrollWidth > windowWidth + 1) {
          issues.push(`Horizontal page scroll detected! pageScrollWidth=${pageScrollWidth} > windowWidth=${windowWidth}`);
        }

        // Check every card and all children inside it
        const cards = Array.from(document.querySelectorAll('#signals-container article'));
        cards.forEach((card, idx) => {
          const cardRect = card.getBoundingClientRect();

          // Check all descendant elements for spilling past the card boundary
          const allDescendants = card.querySelectorAll('*');
          allDescendants.forEach(el => {
            const rect = el.getBoundingClientRect();
            // Allow 1.5px tolerance for subpixel antialiasing
            if (rect.right > cardRect.right + 1.5) {
              const tag = el.tagName.toLowerCase();
              const cls = el.className ? `.${el.className.toString().split(' ')[0]}` : '';
              const text = (el.textContent || '').trim().substring(0, 25);
              issues.push(`Card ${idx + 1}: Element <${tag}${cls}> ("${text}") spills past right border! rect.right=${rect.right.toFixed(1)}, card.right=${cardRect.right.toFixed(1)} (diff: +${(rect.right - cardRect.right).toFixed(1)}px)`);
            }
          });
        });

        // Check grid columns
        const container = document.getElementById('signals-container');
        const gridCols = window.getComputedStyle(container).gridTemplateColumns.split(' ').length;

        return { issues, gridCols, pageScrollWidth, windowWidth };
      });

      console.log(`  Grid columns rendered: ${overflowReport.gridCols} (expected: ${vp.expectedCols})`);

      if (overflowReport.issues.length > 0) {
        console.error(`  ❌ Overflow issues detected at ${vp.name}:`);
        overflowReport.issues.forEach(iss => console.error('     - ' + iss));
        totalErrors += overflowReport.issues.length;
      } else {
        console.log(`  ✅ Zero elements spilling out of cards at ${vp.name}! Zero horizontal overflow.`);
      }
    }

    // 4. Test Interactive Filter Tabs & Search
    console.log('\n--- Test 4: Category Filtering & Search Interactions ---');
    const filterCategories = ['Bitcoin', 'Macro Plumbing & Balance Sheets', 'Compute, Power & The Grid', 'All Signals'];

    for (const cat of filterCategories) {
      const clicked = await page.evaluate((categoryName) => {
        const btn = Array.from(document.querySelectorAll('#category-filters button')).find(
          b => b.textContent.includes(categoryName)
        );
        if (btn) {
          btn.click();
          return true;
        }
        return false;
      }, cat);

      if (clicked) {
        await new Promise(r => setTimeout(r, 300));
        const countText = await page.$eval('#filtered-count', el => el.textContent);
        const visibleCards = await page.$$eval('#signals-container article', els => els.length);
        console.log(`  Filter "${cat}": ${visibleCards} cards visible (${countText.trim()})`);

        // Check overflow after filtering
        const filterOverflow = await page.evaluate(() => {
          const cards = Array.from(document.querySelectorAll('#signals-container article'));
          for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            const cardRect = card.getBoundingClientRect();
            for (const el of card.querySelectorAll('*')) {
              const r = el.getBoundingClientRect();
              if (r.right > cardRect.right + 1.5) {
                return `Card ${i + 1} element <${el.tagName}> overflows after filter: diff=+${(r.right - cardRect.right).toFixed(1)}px`;
              }
            }
          }
          return null;
        });

        if (filterOverflow) {
          console.error(`  ❌ Overflow under filter "${cat}": ${filterOverflow}`);
          totalErrors++;
        }
      }
    }

    // Reset filters
    await page.evaluate(() => {
      const allBtn = document.querySelector('#category-filters button[data-category="All Signals"]');
      if (allBtn) allBtn.click();
    });

  } catch (err) {
    console.error('💥 Fatal test suite error:', err);
    totalErrors++;
  } finally {
    await browser.close();
  }

  console.log('\n========================================');
  if (totalErrors === 0) {
    console.log('🎉 ALL AUTOMATED BROWSER TESTS PASSED! 🎉');
    console.log(' - Zero elements spilling out of containers');
    console.log(' - Zero duplicate content items');
    console.log(' - Clean multi-viewport responsive layout');
    console.log(' - Zero console errors');
    console.log('========================================\n');
    process.exit(0);
  } else {
    console.error(`❌ Automated tests failed with ${totalErrors} issue(s).`);
    console.log('========================================\n');
    process.exit(1);
  }
}

runTests();
