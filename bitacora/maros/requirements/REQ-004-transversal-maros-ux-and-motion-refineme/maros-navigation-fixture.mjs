import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';

const permissions = [...readFileSync('/home/david/dev/maros/maros-next/src/shared/auth/permissions.ts', 'utf8').matchAll(/"([a-z]+:(?:read|write|delete))"/g)].map((match) => match[1]);
const company = { id: 202, name: 'Fixture Company', type: 'OTHER', isCustomer: true, isClient: true, notes: [], attachments: [] };
const contact = { id: 102, name: 'Fixture Contact', occupation: 'Owner', email: 'fixture@example.invalid', isCustomer: true, isClient: true, companyId: company.id, company, notes: [], attachments: [] };
const lead = {
  id: 302,
  leadNumber: '102C-1026',
  name: 'Fixture Navigation Project',
  startDate: '2026-10-01',
  location: 'Fixture location',
  addressLink: null,
  status: 'NEW_LEAD',
  leadType: 'construction',
  contact,
  projectType: { id: 1, name: 'Construction' },
  project: { id: 502 },
  conversion: { converted: true, projectId: 502 },
  notes: [],
  attachments: [],
  inReview: false,
  estimate: 125000,
  financial: { found: false, estimatedAmount: null },
};
const project = {
  id: 502,
  leadId: lead.id,
  lead,
  projectProgressStatus: 'IN_PROGRESS',
  invoiceStatus: 'PENDING',
  qboCustomerId: 'fixture-qbo',
  overview: 'Read-only fixture project',
  notes: [],
  attachments: [],
  client: { id: contact.id, type: 'contact', name: contact.name, isClient: true, isCustomer: true },
  financial: {
    projectNumber: lead.leadNumber,
    estimatedAmount: 125000,
    estimateCount: 1,
    invoicedAmount: 45000,
    invoiceCount: 1,
    paidAmount: 15000,
    outstandingAmount: 30000,
    paidPercentage: 33.3,
    estimateVsInvoicedDelta: 80000,
    payments: [],
  },
  paymentSummary: { count: 1, totalAmount: 15000, lastPaymentDate: '2026-10-10', hasDetails: true },
};
const secondLead = { ...lead, id: 303, leadNumber: '103-1026', name: 'Fixture Second Project', project: { id: 503 }, conversion: { converted: true, projectId: 503 } };
const secondProject = { ...project, id: 503, leadId: 303, lead: secondLead };
const activeLead = { ...lead, id: 304, leadNumber: '104-1026', name: 'Fixture Active Lead', project: null, conversion: { converted: false } };

const tasks = [601,602].map((id,index)=>({id,parentId:null,title:`Fixture Task ${index+1}`,kind:'general',status:'todo',priority:'normal',position:index,workspaceId:701,folderId:null,assignee:{id:1,name:'Fixture User',email:'fixture@example.invalid',picture:null},reporter:null,entityKind:null,entityId:null,entity:null,startDate:'2026-10-12',dueDate:'2026-10-13',blockedReason:null,completedAt:null,labels:[],subtasksTotal:0,subtasksDone:0,commentsCount:0,createdAt:'2026-10-12T12:00:00Z',updatedAt:'2026-10-12T12:00:00Z'}));
const taskDetails=tasks.map(task=>({...task,description:{type:'doc',content:[{type:'paragraph'}]},createdBy:null,attachments:[],managedFiles:[],subtasks:[],activity:[],comments:[],parties:[],watcherIds:[]}));
const workspaces=[701,702].map((id,index)=>({id,title:`Fixture Workspace ${index+1}`,workspaceType:'custom',systemKey:null,archivedAt:null,linkCount:0,folderCount:0,taskCount:2,fileCount:0,description:null,descriptionText:null,links:[],folders:[],files:[]}));
const notes=[801,802].map((id,index)=>({id,parentId:null,kind:'page',title:`Fixture Note ${index+1}`,icon:null,position:index,isFavorite:true,entityKind:null,entityId:null,visibility:'team',isShared:true,isPublished:false,deletedAt:null,createdAt:'2026-10-12T12:00:00Z',updatedAt:'2026-10-12T12:00:00Z',ownerId:1,lastEditedBy:null,tags:[],content:{type:'doc',content:[{type:'paragraph'}]},myAccess:'owner'}));
const scans=[901,902].map((id,index)=>({id:String(id),recordType:'invoice',fileName:`Fixture Invoice ${index+1}`,hasFile:false,contentType:'application/pdf',status:'needs_review',extractedData:null,qboSuggestions:{},errorMessage:null,projectNumber:null,comments:null,warnings:[],enteredAt:null,enteredBy:null,updatedBy:null,createdAt:'2026-10-12T12:00:00Z',updatedAt:'2026-10-12T12:00:00Z'}));

const requestLog = [];
const empty = [];
const readOnlyResponse = (path) => {
  if (path === '/users/me') return { id: 1, email: 'fixture@example.invalid', name: 'Fixture User', picture: null, role: { id: 1, name: 'Fixture Admin' }, permissions };
  if (path === '/crm/customers') return { contacts: [contact], companies: [company] };
  if (path === '/contacts/all') return [contact];
  if (path === '/contacts/102/details') return { ...contact, leads: [lead], stats: { totalLeads: 1, totalProjects: 1, activeProjects: 1, completedProjects: 0 } };
  if (path === '/contacts/company/202') return [contact];
  if (path === '/companies/all') return [company];
  if (path === '/companies/202') return company;
  if (path === '/leads/type') return [activeLead];
  if (path === '/leads/converted') return [lead, secondLead];
  if (path === '/leads/review' || path === '/leads/lost') return empty;
  if (path === '/leads/302' || path === '/leads/302/details') return lead;
  if (path === '/project-types/all') return [{ id: 1, name: 'Construction' }];
  if (path === '/projects/v2/all' || path === '/projects/all' || path === '/projects/completed' || path === '/projects/lost') return [project, secondProject];
  if (path === '/projects/financials') return [project, secondProject].map(value => ({ id: value.id, qbo: { data: null, error: { code: 'fixture', message: 'Read-only fixture' } } }));
  if (path === '/projects/503' || path === '/projects/503/details') return secondProject;
  if (path === '/projects/503/cost-breakdown') return { projectId: 503, categories: [], total: 0 };
  if (path === '/projects/502' || path === '/projects/502/details') return project;
  if (path === '/projects/502/cost-breakdown') return { projectId: project.id, categories: [], total: 0 };
  if (path === '/analytics/project-health') return [{ projectId: project.id, projectNumber: lead.leadNumber, projectName: lead.name, status: 'IN_PROGRESS', grossMarginPercent: 25, backlogAmount: 30000, riskLevel: 'medium', reasons: ['Fixture health alert'] }];
  if (path === '/analytics/top-clients') return [{ jobId: String(project.id), customerName: contact.name, projectNumber: lead.leadNumber, totalInvoiced: 45000, totalPaid: 15000, totalOutstanding: 30000, invoiceCount: 1 }];
  if (path === '/projects/receivables') return { asOf: '2026-10-12', projects: [{ id: project.id, leadNumber: lead.leadNumber, name: lead.name, billedAmount: 45000, collectedAmount: 15000, outstandingAmount: 30000, billedAt: '2026-10-10', endDate: null, daysOutstanding: 2, agingBucket: 'current' }], totals: { current: { projectCount: 1, outstandingAmount: 30000, unbilledProjectCount: 0 }, '31_60': { projectCount: 0, outstandingAmount: 0, unbilledProjectCount: 0 }, '61_90': { projectCount: 0, outstandingAmount: 0, unbilledProjectCount: 0 }, over_90: { projectCount: 0, outstandingAmount: 0, unbilledProjectCount: 0 }, unknown: { projectCount: 0, outstandingAmount: 0, unbilledProjectCount: 0 } }, grandTotal: { projectCount: 1, outstandingAmount: 30000, unbilledProjectCount: 0 } };
  if(path === '/tasks') return {items:tasks,totalCount:2,nextCursor:null};
  if (path === '/tasks/board') return { columns: {todo:tasks}, doneTotalCount: 0 };
  if(path === '/tasks/mine') return {overdue:[],today:tasks,thisWeek:[],later:[],noDueDate:[]};
  if(path === '/tasks/schedule') return tasks;
  if(/^\/tasks\/(601|602)$/.test(path)) return taskDetails.find(task=>task.id===Number(path.split('/').at(-1)));
  if(path === '/task-workspaces') return {items:workspaces,totalCount:2,page:1,limit:50};
  if(/^\/task-workspaces\/(701|702)$/.test(path)) return workspaces.find(workspace=>workspace.id===Number(path.split('/').at(-1)));
  if(path === '/notes' || path === '/notes/favorites' || path === '/notes/shared-with-me') return notes;
  if(/^\/notes\/(801|802)$/.test(path)) return notes.find(note=>note.id===Number(path.split('/').at(-1)));
  if(path === '/invoice-scans') return scans;
  if(/^\/invoice-scans\/(901|902)$/.test(path)) return scans.find(scan=>scan.id===path.split('/').at(-1));
  if (path.startsWith('/tasks/')) return empty;
  if (path.startsWith('/notes/')) return empty;
  if (path.startsWith('/analytics/')) return empty;
  return empty;
};

createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const origin = req.headers.origin;
  if (origin === 'http://localhost:3101') res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Headers', 'content-type');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Vary', 'Origin');
  res.setHeader('Content-Type', 'application/json');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
  if (req.method !== 'GET') { res.writeHead(405); res.end(JSON.stringify({ error: 'Read-only fixture' })); return; }
  if (url.pathname === '/__requests') { res.end(JSON.stringify(requestLog)); if (url.searchParams.has('clear')) requestLog.length = 0; return; }
  requestLog.push(`${url.pathname}${url.search}`);
  res.end(JSON.stringify(readOnlyResponse(url.pathname) ?? null));
}).listen(4101, '127.0.0.1', () => console.log('Read-only navigation fixture on 127.0.0.1:4101'));
