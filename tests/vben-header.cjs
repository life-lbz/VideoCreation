const { chromium } = require('./playwright-runtime.cjs');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch({ headless: true, channel: 'msedge' });
 try {
 const page = await browser.newPage({viewport:{width:1440,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:4173/dashboard');await page.waitForLoadState('networkidle');
 assert.ok(await page.locator('img[src="/frameflow-mark.svg"]').count());
 await page.getByRole('button',{name:'查看可用额度与套餐账单'}).click();await page.waitForURL('**/billing');
 await page.screenshot({path:'output/vben-header-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.reload();await page.waitForLoadState('networkidle');
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await page.screenshot({path:'output/vben-header-mobile.png',fullPage:true});
 assert.deepEqual(errors,[]);console.log('PASS logo, billing entry, desktop/mobile overflow, runtime errors');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
