const { chromium } = require('./playwright-runtime.cjs');
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto('http://127.0.0.1:4174/dashboard');await page.waitForLoadState('networkidle');
 console.log('DASHBOARD', (await page.locator('body').innerText()).slice(0,2200));
 await page.screenshot({path:'output/vben-dashboard.png',fullPage:true});
 for(const route of ['studio','works','billing','templates','assets']){await page.goto('http://127.0.0.1:4174/'+route);await page.waitForLoadState('networkidle');console.log('ROUTE',route,(await page.locator('body').innerText()).slice(-500));}
 await page.setViewportSize({width:390,height:844});await page.goto('http://127.0.0.1:4174/studio');await page.waitForLoadState('networkidle');await page.screenshot({path:'output/vben-mobile.png',fullPage:true});
 console.log('OVERFLOW',await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth));console.log('ERRORS',JSON.stringify(errors));
 await browser.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
