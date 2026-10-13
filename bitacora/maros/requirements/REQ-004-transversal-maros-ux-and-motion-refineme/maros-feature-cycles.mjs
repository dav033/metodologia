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
      await pause(150);
    }
    console.log(JSON.stringify({stage:'wait-debug',url:await evaluate('location.href'),body:await evaluate('document.body.innerText')})); throw new Error(`Wait failed: ${expression}`);
  };
  await call('Emulation.setDeviceMetricsOverride', { width, height: 1000, deviceScaleFactor: 1, mobile: false });
  await call('Page.enable');
  const go = async (path, readyExpression) => {
    await call('Page.navigate', { url: `http://localhost:3101${path}` });
    await waitFor(`location.pathname === ${JSON.stringify(path.split("?")[0])} && (${readyExpression})`);
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


  const cases=[
    {source:'/tasks/workspaces', titles:['Fixture Workspace 1','Fixture Workspace 2'],ids:[701,702],selector:'a',detail:'/tasks/workspaces/'},
    {source:'/notes',titles:['Fixture Note 1','Fixture Note 2'],ids:[801,802],selector:'li.group a',detail:'/notes/'},
    {source:'/notes/favorites',titles:['Fixture Note 1','Fixture Note 2'],ids:[801,802],selector:'li.group a',detail:'/notes/'},
    {source:'/notes/shared',titles:['Fixture Note 1','Fixture Note 2'],ids:[801,802],selector:'li.group a',detail:'/notes/'},
    {source:'/finance/invoices',titles:['Fixture Invoice 1','Fixture Invoice 2'],ids:[901,902],selector:'a',detail:'/finance/invoices/'},
    ...['list','board','mine','calendar'].map(view=>({source:'/tasks?view='+view,titles:['Fixture Task 1','Fixture Task 2'],ids:[601,602],selector:'button,[role="button"]',modal:true})),
  ];
  const selected=process.argv[3];
  for(const item of cases.filter(item=>!selected || (selected === 'taskviews' ? item.modal : item.source.includes(selected)))){
    await go(item.source, `document.body.innerText.includes('${item.titles[0]}')`);
    await waitFor(`[...document.querySelectorAll('${item.selector}')].some(node=>node.getBoundingClientRect().width>0 && node.textContent.includes('${item.titles[0]}'))`);
    for(const index of [0,1,0]){
      await clearRequests();
      await clickText(item.titles[index],item.selector);
      await waitFor(item.modal?`new URLSearchParams(location.search).get('task')==='${item.ids[index]}' && !!document.querySelector('[role="dialog"]')`:`location.pathname==='${item.detail}${item.ids[index]}'`);
      await waitFor(item.modal ? `!!document.querySelector('[data-task-title]') && document.querySelector('[data-task-title]').value === '${item.titles[index]}'` : `document.body.innerText.includes('${item.titles[index]}') && !document.body.innerText.includes('Loading workspace…')`);
      await pause(1800);
      const entry=await requests();
      const detailState=await evaluate(`({text:document.body.innerText.slice(-700),error:document.body.innerText.includes('Algo no salió')})`);
      await clearRequests();
      const frames = item.modal ? (await evaluate(`history.back()`), []) : await back(item.source.split('?')[0],item.titles[index]);
      await waitFor(item.modal?`!new URLSearchParams(location.search).has('task')`:`location.pathname==='${item.source.split('?')[0]}'`);
      await waitFor(`document.body.innerText.includes('${item.titles[index]}') && !document.querySelector('[role="dialog"]')`);
      await pause(1300);
      console.log(JSON.stringify({width,source:item.source,id:item.ids[index],entry,backRequests:await requests(),detailState,overlayTexts:[...new Set(frames.flatMap(frame=>frame.texts))],overlayFrames:frames.filter(frame=>frame.title).length,settled:await evaluate(`({url:location.href,copies:document.querySelectorAll('[data-shared-element-overlay-copy]').length,dialogs:document.querySelectorAll('[role="dialog"]').length,titleVisible:document.body.innerText.includes('${item.titles[index]}')})`)}));
    }
  }
} finally {
  socket?.close();
  browser.kill();
}
