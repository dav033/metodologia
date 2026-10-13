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



  await go('/leads/construction',`document.body.innerText.includes('Fixture Active Lead')`);await clickText('Converted','button');await waitFor(`document.body.innerText.includes('Fixture Second Project')`);await pause(1200);
  const snapshot = () => evaluate(`([...document.querySelectorAll('button')].filter(n=>n.textContent.includes('Fixture Contact')).map(n=>({text:n.textContent.trim(),names:[...n.querySelectorAll('span')].map(s=>({text:s.textContent.trim(),opacity:getComputedStyle(s).opacity,visibility:getComputedStyle(s).visibility,overlay:s.hasAttribute('data-shared-element-overlay-active')}))})))`);
  console.log(JSON.stringify({stage:'initial',badges:await snapshot()}));
  await clickText('Fixture Contact','button');await waitFor(`location.pathname==='/contact/102'`);await pause(1200);
  await back('/leads/construction','Fixture Second Project');
  console.log(JSON.stringify({stage:'return',badges:await snapshot()}));
  await evaluate(`([...document.querySelectorAll('button')].filter(n=>n.textContent.includes('Fixture Contact'))[1]).click()`);
  await waitFor(`location.pathname==='/contact/102'`);await pause(1000);await back('/leads/construction','Fixture Second Project');
  console.log(JSON.stringify({stage:'second-return',badges:await snapshot()}));
} finally {socket?.close();browser.kill();}
