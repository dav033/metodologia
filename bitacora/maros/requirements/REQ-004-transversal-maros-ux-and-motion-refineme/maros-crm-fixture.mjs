import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
const permissions=[...readFileSync('/home/david/dev/maros/maros-next/src/shared/auth/permissions.ts','utf8').matchAll(/"([a-z]+:(?:read|write|delete))"/g)].map(m=>m[1]);
const companies=[1,2].map(id=>({id:200+id,name:`Fixture Company ${id}`,type:'OTHER',isCustomer:true,isClient:true,notes:[],attachments:[]}));
const contacts=[1,2].map(id=>({id:100+id,name:`Fixture Contact ${id}`,occupation:'Owner',email:`contact${id}@example.invalid`,isCustomer:true,isClient:true,companyId:200+id,company:companies[id-1],notes:[],attachments:[]}));
const leads=[1,2].map(id=>({id:300+id,name:`Fixture Lead ${id}`,leadNumber:`10${id}-1026`,status:'NEW_LEAD',contact:contacts[id-1],projectType:{id:1,name:'Construction'},inReview:false,location:'Fixture location',notes:[],attachments:[],financial:{found:false,estimatedAmount:0}}));
let requests=[];
createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost');const path=url.pathname;
  res.setHeader('Access-Control-Allow-Origin','http://localhost:3101');res.setHeader('Access-Control-Allow-Credentials','true');res.setHeader('Access-Control-Allow-Headers','content-type');res.setHeader('Content-Type','application/json');
  if(req.method==='OPTIONS'){res.writeHead(204);res.end();return;}
  if(req.method!=='GET'){res.writeHead(405);res.end('{"error":"Read-only fixtures"}');return;}
  if(path==='/__requests'){res.end(JSON.stringify(requests));if(url.searchParams.has('clear'))requests=[];return;}
  requests.push(path);let data=[];
  if(path==='/users/me')data={id:1,email:'fixture@example.invalid',name:'Fixture User',picture:null,role:{id:1,name:'Fixture'},permissions};
  else if(path==='/contacts/all')data=contacts;
  else if(path.match(/^\/contacts\/\d+\/details$/)){const contact=contacts.find(c=>c.id===Number(path.split('/')[2]));data={...contact,leads:leads.filter(l=>l.contact.id===contact?.id),stats:{totalLeads:1,totalProjects:0,activeProjects:0,completedProjects:0}};}
  else if(path.startsWith('/contacts/company/'))data=contacts.filter(c=>c.companyId===Number(path.split('/').at(-1)));
  else if(path.match(/^\/contacts\/\d+$/))data=contacts.find(c=>c.id===Number(path.split('/').at(-1)));
  else if(path==='/companies/all')data=companies;
  else if(path.match(/^\/companies\/\d+$/))data=companies.find(c=>c.id===Number(path.split('/').at(-1)));
  else if(path==='/customers')data={contacts,companies};
  else if(['/leads/type','/leads/review','/leads/lost'].includes(path))data=leads;
  else if(path.match(/^\/leads\/\d+$/))data=leads.find(l=>l.id===Number(path.split('/').at(-1)));
  else if(path==='/project-types/all')data=[{id:1,name:'Construction'}];
  res.end(JSON.stringify(data??null));
}).listen(4101,'127.0.0.1',()=>console.log('Read-only CRM fixture API on 4101'));
