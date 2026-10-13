import { spawn } from 'node:child_process';
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const width = Number(process.argv[2] ?? 1440);
const profile = `/tmp/maros-nav-check-${Date.now()}`;
const browser = spawn('/usr/bin/chromium', ['--headless', '--no-sandbox', '--disable-gpu', '--remote-debugging-port=9294', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
let socket;
try {
  let targets;
  for (let i = 0; i < 80; i++) {
    try { targets = await (await fetch('http://127.0.0.1:9294/json')).json(); break; } catch { await pause(250); }
  }
  if (!targets) throw new Error('Chromium did not start');
  socket = new WebSocket(targets.find((target) => target.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve) => socket.addEventListener('open', resolve, { once: true }));
  let sequence = 0;
  const pending = new Map();
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if (!message.id) return;
    const promise = pending.get(message.id);
    if (!promise) return;
    pending.delete(message.id);
    clearTimeout(promise.timer);
    message.error ? promise.reject(message.error) : promise.resolve(message.result);
  });
  const call = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 90000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async (expression) => {
    const result = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const waitFor = async (expression, timeout = 60000) => {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      if (await evaluate(expression)) return;
      await pause(900);
    }
    console.log(JSON.stringify({stage:'wait-debug',url:await evaluate('location.href'),body:await evaluate('document.body.innerText')})); throw new Error(`Wait failed: ${expression}`);
  };
  await call('Emulation.setDeviceMetricsOverride', { width, height: 1000, deviceScaleFactor: 1, mobile: false });
  await call('Page.enable');
  const go = async (path, readyExpression) => {
    await call('Page.navigate', { url: `http://localhost:3101${path}` });
    await waitFor(`location.pathname === ${JSON.stringify(path)} && (${readyExpression})`);
    await pause(700);
  };
  const clearRequests = () => fetch('http://127.0.0.1:4101/__requests?clear=1');
  const requests = async () => (await (await fetch('http://127.0.0.1:4101/__requests')).json());
  const clickText = async (text, selector) => evaluate(`(() => { const wanted = ${JSON.stringify(text)}; const values = [...document.querySelectorAll(${JSON.stringify(selector)})].filter((node) => node.getBoundingClientRect().width > 0 && node.textContent.trim().includes(wanted)); const node = values[0]; if (!node) throw new Error('Missing clickable text: ' + wanted); const trigger = node.closest('a,button,[role="link"],tr'); if (!trigger) throw new Error('No trigger for: ' + wanted); trigger.click(); return { trigger: trigger.tagName, text: trigger.textContent.trim().slice(0, 100) }; })()`);
  const back = async (path, readyText) => {
    await evaluate(`(() => { window.__motionFrames = []; const started = performance.now(); history.back(); const sample = () => { const copies = [...document.querySelectorAll('[data-shared-element-overlay-copy]')].filter((node) => node.getBoundingClientRect().width > 0); const title = copies[0]; window.__motionFrames.push({ elapsed: performance.now() - started, path: location.pathname, title: title?.textContent ?? null, texts: copies.map(node=>node.textContent), opacity: title ? getComputedStyle(title).opacity : null, transform: title ? getComputedStyle(title).transform : null, tables: document.querySelectorAll('table').length }); if (performance.now() - started < 1000) requestAnimationFrame(sample); }; requestAnimationFrame(sample); })()`);
    await waitFor(`location.pathname === ${JSON.stringify(path)} && document.body.innerText.includes(${JSON.stringify(readyText)})`);
    await pause(1150);
    return evaluate('window.__motionFrames');
  };


  const scenario=async(params='clear=1')=>fetch('http://127.0.0.1:4101/__scenario?'+params);
  const cases=[
    {source:'/',title:'Fixture Navigation Project',number:'102C-1026',target:'/project/502',delay:'/projects/v2/all',loaded:'Read-only fixture project'},
    {source:'/reports/clients',title:'Fixture Contact',target:'/contact/102',delay:'/contacts/102/details',loaded:'Fixture Navigation Project'},
    {source:'/reports/stale-leads',title:'Fixture Navigation Project',number:'102C-1026',target:'/lead/302',delay:'/leads/302',loaded:'fixture@example.invalid'},
  ];
  for(const item of (process.argv[3] === 'retry' ? [] : cases)){
    await scenario();await scenario('delay='+encodeURIComponent(item.delay)+'&ms=3500');
    await go(item.source, `document.body.innerText.includes('${item.title}')`);
    if(item.source.includes('stale')){await clickText('30 days','button');await waitFor(`location.search.includes('days=30')`);await pause(500);}
    await clearRequests();await clickText(item.title,'a');await waitFor(`location.pathname==='${item.target}'`);await pause(900);
    const pendingState=await evaluate(`({headings:[...document.querySelectorAll('h1')].map(node=>node.textContent),body:document.body.innerText,activeCopies:[...document.querySelectorAll('[data-shared-element-overlay-copy]')].map(node=>node.textContent)})`);
    console.log(JSON.stringify({stage:'pending-source',width,source:item.source,hasTitle:pendingState.body.includes(item.title),hasNumber:!item.number||pendingState.body.includes(item.number),headings:pendingState.headings,activeCopies:pendingState.activeCopies,requests:await requests()}));
    await waitFor(`document.body.innerText.includes('${item.loaded}')`);await pause(500);await clearRequests();const frames=await back(item.source,item.title);
    console.log(JSON.stringify({stage:'pending-return',width,source:item.source,requests:await requests(),texts:[...new Set(frames.flatMap(frame=>frame.texts))],state:await evaluate(`({url:location.href,copies:document.querySelectorAll('[data-shared-element-overlay-copy]').length,active:document.querySelectorAll('[data-shared-element-overlay-active]').length,selected30:[...document.querySelectorAll('button')].find(node=>node.textContent.trim()==='30 days')?.getAttribute('aria-pressed')})`)}));
  }
  await scenario();await scenario('fail='+encodeURIComponent('/contacts/102/details'));
  await go('/contacts',`document.body.innerText.includes('Fixture Contact')`);await clickText('Fixture Contact','tr');
  await waitFor(`location.pathname==='/contact/102' && [...document.querySelectorAll('[role="alert"]')].some(node=>node.textContent.includes('Retry'))`);
  console.log(JSON.stringify({stage:'contact-relations-error',width,titleVisible:await evaluate(`document.body.innerText.includes('Fixture Contact')`),body:await evaluate(`document.body.innerText.slice(-700)`)}));
  await scenario();await clickText('Retry','button');await waitFor(`document.body.innerText.includes('Fixture Navigation Project') && ![...document.querySelectorAll('[role="alert"]')].some(node=>node.textContent.includes('Retry'))`);
  console.log(JSON.stringify({stage:'contact-relations-retry',width,recovered:true}));
  await scenario('fail='+encodeURIComponent('/projects/v2/all'));await go('/projects/construction',`document.body.innerText.includes('Couldn’t load projects')`);
  console.log(JSON.stringify({stage:'project-list-error',width,emptySuccess:await evaluate(`document.body.innerText.includes('No projects found')`)}));
  await scenario();await clickText('Try again','button');await waitFor(`document.body.innerText.includes('Fixture Navigation Project') && !document.body.innerText.includes('Couldn’t load projects')`);
  console.log(JSON.stringify({stage:'project-list-retry',width,recovered:true}));
} finally {
  await fetch('http://127.0.0.1:4101/__scenario?clear=1');
  socket?.close();
  browser.kill();
}
