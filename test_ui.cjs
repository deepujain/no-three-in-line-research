const { chromium } = require('playwright');
const path = require('path');
const assert = require('assert/strict');
(async () => {
  const browser = await chromium.launch({ channel: process.env.CHROME_CHANNEL || 'chrome', headless:true });
  try {
    for (const [width,height] of [[1440,900],[1280,720],[736,700],[390,844],[320,568]]) {
      const page = await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
      const errors=[];
      page.on('pageerror', e=>errors.push(e.message));
      await page.goto('file://'+path.join(__dirname,'index.html'));
      const snapshot=await page.evaluate(()=>window.researchView.snapshot());
      assert.equal(snapshot.count,156);assert.equal(snapshot.n,79);assert.equal(snapshot.approaches,10);
      const {candidate:c,pair:[a,b]}=snapshot.conflict;
      assert.equal((b[0]-a[0])*(c[1]-a[1]),(b[1]-a[1])*(c[0]-a[0]));
      await page.getByRole('button',{name:'Why adding a point fails'}).click();
      assert.equal(await page.getByRole('button').getAttribute('aria-pressed'),'true');
      await page.getByRole('button',{name:'Show verified arrangement'}).click();
      await page.getByRole('button').focus();await page.keyboard.press('Space');
      assert.equal(await page.evaluate(()=>window.researchView.snapshot().showConflict),true);
      await page.getByRole('button').click();
      const dims=await page.evaluate(()=>({w:innerWidth,h:innerHeight,sw:document.documentElement.scrollWidth,sh:document.documentElement.scrollHeight,canvas:document.getElementById('board').getBoundingClientRect().toJSON()}));
      assert.ok(dims.sw<=width,`horizontal overflow ${width}: ${JSON.stringify(dims)}`);
      assert.ok(dims.sh<=height,`vertical overflow ${width}: ${JSON.stringify(dims)}`);
      assert.ok(dims.canvas.width>=160);
      assert.deepEqual(errors,[]);
      if(process.env.SCREENSHOT_DIR) await page.screenshot({path:path.join(process.env.SCREENSHOT_DIR,`no-three-${width}.png`),fullPage:true});
      console.log(`${width}x${height}: passed`);
      await page.close();
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
