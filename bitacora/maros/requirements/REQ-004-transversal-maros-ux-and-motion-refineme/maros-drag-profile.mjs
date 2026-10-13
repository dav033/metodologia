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



  await go('/tasks',`document.querySelectorAll('[data-task-card-id]').length===100`);
  await call('Performance.enable');
  const handle=await evaluate(`(()=>{const n=document.querySelector('[data-task-card-id] button[aria-label="Drag task"]');n.scrollIntoView({block:'center'});const r=n.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  await call('Input.dispatchMouseEvent',{type:'mouseMoved',x:handle.x,y:handle.y});await pause(500);
  await call('Input.dispatchMouseEvent',{type:'mousePressed',x:handle.x,y:handle.y,button:'left',clickCount:1});
  await call('Input.dispatchMouseEvent',{type:'mouseMoved',x:handle.x+10,y:handle.y,buttons:1});await pause(300);
  const before=await call('Performance.getMetrics');
  await call('Profiler.enable');await call('Profiler.start');
  await evaluate(`(()=>{window.__dragFrames=[];window.__dragMeasure=true;let last=performance.now();const tick=t=>{window.__dragFrames.push(t-last);last=t;if(window.__dragMeasure)requestAnimationFrame(tick)};requestAnimationFrame(tick)})()`);
  const started=Date.now();
  for(let i=0;i<120;i++){await call('Input.dispatchMouseEvent',{type:'mouseMoved',x:handle.x+50+(i%60)*5,y:handle.y+35+Math.sin(i/10)*20,buttons:1});await pause(16);}
  const duration=Date.now()-started;
  const after=await call('Performance.getMetrics');const {profile}=await call('Profiler.stop');
  const frames=await evaluate(`(()=>{window.__dragMeasure=false;return window.__dragFrames})()`);
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  await call('Input.dispatchMouseEvent',{type:'mouseReleased',x:handle.x+50,y:handle.y+35,button:'left',clickCount:1});
  const sorted=frames.filter(n=>n>0).sort((a,b)=>a-b);const metric=(m,k)=>m.metrics.find(n=>n.name===k)?.value??0;
  const nodes=new Map(profile.nodes.map(n=>[n.id,n]));const samples={};for(const id of profile.samples??[]){const name=nodes.get(id)?.callFrame.functionName??'unknown';samples[name]=(samples[name]??0)+1;}
  console.log(JSON.stringify({width,cards:100,durationMs:duration,frames:frames.length,medianFrameMs:sorted[Math.floor(sorted.length*.5)],p95FrameMs:sorted[Math.floor(sorted.length*.95)],framesOver50ms:frames.filter(n=>n>50).length,scriptDurationMs:(metric(after,'ScriptDuration')-metric(before,'ScriptDuration'))*1000,layoutDurationMs:(metric(after,'LayoutDuration')-metric(before,'LayoutDuration'))*1000,topSamples:Object.entries(samples).sort((a,b)=>b[1]-a[1]).slice(0,12)}));
} finally {socket?.close();browser.kill();}
