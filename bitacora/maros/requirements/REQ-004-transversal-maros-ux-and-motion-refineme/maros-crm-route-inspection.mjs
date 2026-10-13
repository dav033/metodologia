import { spawn } from 'node:child_process';
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const width=Number(process.argv[2]??1440);
const browser=spawn('/usr/bin/chromium',['--headless','--no-sandbox','--disable-gpu','--remote-debugging-port=9289',`--user-data-dir=/tmp/maros-crm-browser-${width}`,'about:blank'],{stdio:'ignore'});
let socket;
try {
  let targets;for(let i=0;i<50;i++){try{targets=await(await fetch('http://127.0.0.1:9289/json')).json();break;}catch{await pause(200);}}
  socket=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>socket.addEventListener('open',r,{once:true}));
  let seq=0;const pending=new Map();socket.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);if(p){pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(m.error):p.resolve(m.result);}}});
  const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;const timer=setTimeout(()=>{pending.delete(id);reject(Error(`CDP timeout ${method}`));},90000);pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params}));});
  const evaluate=async(expression)=>{const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
  const waitFor=async(expression)=>{for(let i=0;i<360;i++){if(await evaluate(expression))return;await pause(250);}throw Error(`Wait failed: ${expression}`);};
  await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:false});
  const requests=async(clear=false)=>(await(await fetch(`http://127.0.0.1:4101/__requests${clear?'?clear=1':''}`)).json());
  for(const entity of [{list:'/contacts',detail:'/contact/',name:'Contact',base:100},{list:'/company',detail:'/company/',name:'Company',base:200},{list:'/leads/construction',detail:'/lead/',name:'Lead',base:300}]){
    await call('Page.navigate',{url:`http://localhost:3101${entity.list}`});
    await waitFor(`document.body.innerText.includes('Fixture ${entity.name} 1')`);await pause(1000);
    for(const index of [1,2,1]){
      const title=`Fixture ${entity.name} ${index}`;const path=`${entity.detail}${entity.base+index}`;
      await requests(true);
      await evaluate(`(()=>{const title=${JSON.stringify(title)};const candidates=[...document.querySelectorAll('span,a')].filter(e=>e.textContent.trim()===title&&e.getBoundingClientRect().width>0);const source=candidates.find(e=>e.closest('tr,a,button'));const trigger=source?.closest('a,tr,button');if(!trigger)throw Error('Missing source');trigger.click()})()`);
      await waitFor(`location.pathname===${JSON.stringify(path)}&&[...document.querySelectorAll('h1')].some(e=>e.textContent.includes(${JSON.stringify(title)}))`);await pause(750);
      const entryRequests=await requests(true);
      const entryState=await evaluate(`({heading:[...document.querySelectorAll('h1')].map(e=>e.textContent),copies:document.querySelectorAll('[data-shared-element-overlay-copy]').length,markers:document.querySelectorAll('[data-shared-element-overlay-active]').length,wrongZero:document.body.innerText.includes('Estimate (QuickBooks) $0.00')})`);
      await evaluate(`(()=>{window.__returnFrames=[];const title=${JSON.stringify(title)};const start=performance.now();history.back();function tick(){const copy=[...document.querySelectorAll('[data-shared-element-overlay-copy]')].find(e=>e.textContent===title);const node=[...document.querySelectorAll('span,a')].find(e=>e.textContent.trim()===title&&e.getBoundingClientRect().width>0);window.__returnFrames.push({t:performance.now()-start,path:location.pathname,copy:!!copy,text:!!node,tables:document.querySelectorAll('table').length});if(performance.now()-start<1600)requestAnimationFrame(tick)}requestAnimationFrame(tick)})()`);
      await waitFor(`location.pathname===${JSON.stringify(entity.list)}&&document.body.innerText.includes(${JSON.stringify(title)})`);await pause(1700);
      const backRequests=await requests();const frames=await evaluate('window.__returnFrames');
      console.log(JSON.stringify({width,entity:entity.name,index,entryRequests,backRequests,entryState,return:{frames:frames.length,copyFrames:frames.filter(f=>f.copy).length,missingListFrames:frames.filter(f=>f.path===entity.list&&!f.text).length,maxTables:Math.max(...frames.map(f=>f.tables))}}));
    }
  }
} finally {socket?.close();browser.kill();}
