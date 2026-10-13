import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
const require = createRequire('/home/david/dev/maros/maros-next/package.json');
await require('esbuild').build({entryPoints:['/tmp/maros-shared-overlay-inspection.tsx'],outfile:'/tmp/maros-shared-overlay-bundle.js',bundle:true,platform:'browser',jsx:'automatic',alias:{'@':'/home/david/dev/maros/maros-next/src'},nodePaths:['/home/david/dev/maros/maros-next/node_modules'],define:{'process.env.NODE_ENV':'"development"'}});
const server=createServer(async(req,res)=>{res.setHeader('Content-Type',req.url==='/bundle.js'?'text/javascript':'text/html');res.end(req.url==='/bundle.js'?await readFile('/tmp/maros-shared-overlay-bundle.js'):'<style>.inline-block{display:inline-block}[data-shared-element-overlay-active="true"]{opacity:0!important}body{font-family:Arial}</style><div id="root"></div><script src="/bundle.js"></script>');}).listen(3199,'127.0.0.1');
const browser=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-gpu','--remote-debugging-port=9288','--user-data-dir=/tmp/maros-shared-overlay-profile','about:blank'],{stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let socket;
try {
  let targets; for(let i=0;i<40;i++){try{targets=await(await fetch('http://127.0.0.1:9288/json')).json();break;}catch{await pause(250);}}
  socket=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>socket.addEventListener('open',r,{once:true}));
  let seq=0;const pending=new Map();socket.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}});
  const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
  const evaluate=async(expression)=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  await call('Page.navigate',{url:'http://127.0.0.1:3199'});await pause(1500);
  const inspect=async(label,action)=>{const frames=await evaluate(`new Promise(resolve=>{const frames=[];const start=performance.now();document.querySelector('${action}').click();function tick(){const copy=document.querySelector('[data-shared-element-overlay-copy]');const source=document.querySelector('[data-shared-element-overlay-active]');frames.push({t:performance.now()-start,copies:document.querySelectorAll('[data-shared-element-overlay-copy]').length,hidden:!!source,visible:!!copy&&getComputedStyle(copy).opacity==='1',x:copy?.getBoundingClientRect().x,y:copy?.getBoundingClientRect().y});if(performance.now()-start<750)requestAnimationFrame(tick);else resolve(frames)}requestAnimationFrame(tick)})`);console.log(JSON.stringify({label,animatedFrames:frames.filter(f=>f.copies).length,maxCopies:Math.max(...frames.map(f=>f.copies)),visibleFrames:frames.filter(f=>f.visible).length,final:frames.at(-1),first:frames.find(f=>f.copies),last:frames.filter(f=>f.copies).at(-1)}));};
  await inspect('entry-1','#toggle');await inspect('return-1','#toggle');await evaluate("document.querySelector('#next').click()");await pause(100);await inspect('entry-2','#toggle');await inspect('return-2','#toggle');
  await inspect('duplicate-source-2','#alias-2');await inspect('duplicate-source-return','#alias-back');await inspect('default-source-after-alias','#alias-default');await inspect('default-source-return','#alias-back');
  await evaluate("document.querySelector('#toggle').click()");await pause(80);await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});await pause(100);console.log(JSON.stringify({label:'reduced-motion-change',state:await evaluate("({copies:document.querySelectorAll('[data-shared-element-overlay-copy]').length,markers:document.querySelectorAll('[data-shared-element-overlay-active]').length})")}));
} finally {socket?.close();browser.kill();server.close();}
