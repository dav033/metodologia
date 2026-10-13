import { spawn } from 'node:child_process';
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const width = Number(process.argv[2] ?? 1440);
const profile = `/tmp/maros-nav-check-${Date.now()}`;
const browser = spawn('/usr/bin/chromium', ['--headless', '--no-sandbox', '--disable-gpu', '--remote-debugging-port=9295', `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
let socket;
try {
  let targets;
  for (let i = 0; i < 80; i++) {
    try { targets = await (await fetch('http://127.0.0.1:9295/json')).json(); break; } catch { await pause(250); }
  }
  if (!targets) throw new Error('Chromium did not start');
  socket = new WebSocket(targets.find((target) => target.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve) => socket.addEventListener('open', resolve, { once: true }));
  let sequence = 0;
  const pending = new Map();
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    if (message.method === 'Fetch.requestPaused') {
      void call('Fetch.fulfillRequest', {requestId:message.params.requestId,responseCode:404,responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Access-Control-Allow-Origin',value:'http://localhost:3101'},{name:'Access-Control-Allow-Credentials',value:'true'}],body:Buffer.from(JSON.stringify({message:'Contact not found'})).toString('base64')});
      return;
    }
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


  await go('/contacts', `document.body.innerText.includes('Fixture Contact')`);
  await call('Fetch.enable',{patterns:[{urlPattern:'*/contacts/102/details',requestStage:'Request'}]});
  await evaluate(`(() => { const row=[...document.querySelectorAll('tr')].find(n=>n.textContent.includes('Fixture Contact'));row.focus();row.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true})); })()`);
  await waitFor(`location.pathname==='/contact/102' && document.body.innerText.includes('Error loading contact')`);
  console.log(JSON.stringify({stage:'contact-keyboard-404',errorVisible:await evaluate(`document.body.innerText.includes('Error loading contact')`),editableContact:await evaluate(`document.body.innerText.includes('Contact Information')`)}));
  await call('Fetch.disable');
  await go('/leads/construction',`document.body.innerText.includes('Fixture Active Lead')`);
  await clickText('Converted','button');await waitFor(`document.body.innerText.includes('Fixture Navigation Project')`);
  await evaluate(`(() => {const row=[...document.querySelectorAll('tr')].find(n=>n.textContent.includes('Fixture Navigation Project'));row.focus();row.dispatchEvent(new KeyboardEvent('keydown',{key:' ',bubbles:true}));})()`);
  await waitFor(`location.pathname==='/project/502' && document.body.innerText.includes('102C-1026')`);
  console.log(JSON.stringify({stage:'converted-keyboard-space',headings:await evaluate(`[...document.querySelectorAll('h1')].map(n=>n.textContent)`),nameVisible:await evaluate(`document.body.innerText.includes('Fixture Navigation Project')`)}));
} finally {socket?.close();browser.kill();}
