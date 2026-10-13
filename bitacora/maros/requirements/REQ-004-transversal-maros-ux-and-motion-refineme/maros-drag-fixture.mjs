import http from 'node:http';
const base = await (await fetch('http://127.0.0.1:4101/tasks/board')).json();
const seed = base.columns.todo[0];
const statuses = ['backlog','todo','in_progress','blocked','done'];
const columns = Object.fromEntries(statuses.map((status,index)=>[status,Array.from({length:20},(_,i)=>({...seed,id:2000+index*20+i,title:`Drag fixture ${index*20+i}`,status}))]));
http.createServer(async(req,res)=>{
 res.setHeader('Access-Control-Allow-Origin','http://localhost:3101');res.setHeader('Access-Control-Allow-Credentials','true');res.setHeader('Content-Type','application/json');
 if(req.method==='OPTIONS'){res.writeHead(204);res.end();return;}
 if(req.method!=='GET'){res.writeHead(405);res.end('{}');return;}
 if(new URL(req.url,'http://localhost').pathname==='/tasks/board'){res.end(JSON.stringify({columns,doneTotalCount:20}));return;}
 const r=await fetch('http://127.0.0.1:4101'+req.url);res.writeHead(r.status);res.end(await r.text());
}).listen(4102,'127.0.0.1');
