const {chromium}=require('./playwright-runtime.cjs');
const assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({headless:true,channel:'msedge'});try{const p=await b.newPage({viewport:{width:1440,height:1000}});const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto('http://127.0.0.1:4174/settings/video-providers');await p.waitForLoadState('networkidle');
const card=p.locator('.ant-card').filter({has:p.locator('.ant-card-head-title',{hasText:'Luma'})});assert.equal(await p.locator('.provider-grid .ant-card').count(),4);
await p.locator('#key-luma').fill('smoke-only-not-real-key');await card.getByRole('button',{name:'保存密钥'}).click();await p.waitForFunction(()=>document.querySelector('#key-luma').value==='');await card.getByText('已配置',{exact:true}).waitFor();assert.equal(await p.locator('#key-luma').inputValue(),'');
const data=await p.request.get('http://127.0.0.1:4174/api/video-providers');assert.ok(!(await data.text()).includes('smoke-only-not-real-key'));
await card.getByRole('button',{name:/移\s*除/,exact:false}).click();await p.getByRole('button',{name:'移除配置',exact:true}).click();await card.getByText('待配置',{exact:true}).waitFor();
await p.screenshot({path:'output/video-providers.png',fullPage:true});await p.setViewportSize({width:390,height:844});await p.reload();await p.waitForLoadState('networkidle');assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);console.log('PASS four fixed providers, encrypted save/redacted read, cleared key field, remove, mobile, no runtime errors');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
