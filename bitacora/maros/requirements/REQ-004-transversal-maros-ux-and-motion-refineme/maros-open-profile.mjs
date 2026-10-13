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
  const requestPaths = [];
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if(message.method==='Network.requestWillBeSent' && message.params.request.url.startsWith('http://127.0.0.1:4102')) requestPaths.push(new URL(message.params.request.url).pathname);
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



  if(process.argv[3]==='reduce') await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await go('/tasks',`document.querySelectorAll('[data-task-card-id]').length===100`);
  await call('Performance.enable');await call('Network.enable');
  for(const stage of ['cold','warm']){
    const before=await call('Performance.getMetrics');requestPaths.length=0;
    await evaluate(`(()=>{window.__openFrames=[];const start=performance.now();const sample=()=>{const dialog=document.querySelector('[data-task-detail-dialog]');const r=dialog?.getBoundingClientRect();const title=dialog?.querySelector('[data-task-title]')??dialog?.querySelector('h2:not(.sr-only)');let opacity=1;for(let n=title;n&&n!==dialog;n=n.parentElement)opacity*=Number(getComputedStyle(n).opacity);const surface=dialog?.querySelector('[aria-hidden="true"]');const sr=surface?.getBoundingClientRect();window.__openFrames.push({ms:performance.now()-start,y:r?.y,height:r?.height,width:r?.width,title:title?.value??title?.textContent,opacity,surfaceY:sr?.y,surfaceHeight:sr?.height});if(performance.now()-start<2200)requestAnimationFrame(sample)};requestAnimationFrame(sample);document.querySelector('[data-task-card-id="2000"] button[data-task-open]').click()})()`);
    await waitFor(`!!document.querySelector('[data-task-title]')`);await pause(2400);
    const frames=await evaluate('window.__openFrames');const after=await call('Performance.getMetrics');
    const visible=frames.filter(f=>f.height);const early=visible[0];const end=visible.at(-1);const firstTitle=frames.find(f=>f.title&&f.opacity>.5);const metric=(m,k)=>m.metrics.find(n=>n.name===k)?.value??0;
    console.log(JSON.stringify({stage,width,reduced:process.argv[3]==='reduce',requests:requestPaths,firstDialogMs:early?.ms,firstTitleMs:firstTitle?.ms,initialHeight:early?.height,finalHeight:end?.height,initialY:early?.y,finalY:end?.y,heightRange:[Math.min(...visible.map(f=>f.height)),Math.max(...visible.map(f=>f.height))],scriptDurationMs:(metric(after,'ScriptDuration')-metric(before,'ScriptDuration'))*1000,frames:frames.length,firstSurface:visible.find(f=>f.surfaceHeight),lastSurface:visible.at(-1)}));
    await evaluate(`[...document.querySelectorAll('[data-task-detail-dialog] button')].find(n=>n.textContent.trim()==='Close').click()`);await waitFor(`!location.search.includes('task=')`);await pause(1000);
  }
} finally {socket?.close();browser.kill();}
