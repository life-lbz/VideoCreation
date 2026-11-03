const {chromium}=require('./playwright-runtime.cjs');
const assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({headless:true,channel:'msedge'});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}});await page.goto('http://127.0.0.1:4174/studio');await page.waitForLoadState('networkidle');
 await page.getByRole('button',{name:'云境白',exact:true}).click();await page.reload();await page.waitForLoadState('networkidle');assert.equal(await page.locator('html').getAttribute('data-frameflow-theme'),'cloud');
 await page.locator('#prompt').fill('自动验收：清晨海边公路，镜头缓慢推进');await page.getByRole('button',{name:'智能润色',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#prompt').value.includes('光影'));await page.getByRole('button',{name:'生成视频',exact:true}).click();await page.locator('video').waitFor({timeout:60000});assert.ok(await page.locator('video').getAttribute('src'));console.log('PASS theme persistence, enhance, estimate, submit, poll, result');
 await page.goto('http://127.0.0.1:4174/works');await page.waitForLoadState('networkidle');console.log('WORKS', (await page.locator('body').innerText()).slice(-900));
 await page.screenshot({path:'output/vben-works.png',fullPage:true});
 await page.goto('http://127.0.0.1:4174/billing');await page.waitForLoadState('networkidle');await page.getByRole('button',{name:'切换套餐',exact:true}).first().click();await page.getByRole('button',{name:/确\s*认/}).click();await page.waitForFunction(()=>document.body.innerText.includes('套餐已更新'));console.log('PASS plan switch');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
