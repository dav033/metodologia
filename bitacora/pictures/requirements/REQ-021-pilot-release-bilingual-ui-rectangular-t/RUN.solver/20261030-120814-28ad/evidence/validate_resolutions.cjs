const fs=require('fs'), path=require('path');
const ts=require('/home/david/dev/pictures-wt/asesor/node_modules/typescript');
const triggers=JSON.parse(fs.readFileSync('/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-120814-28ad/triggers.json'));
let count=0;
for(const {resolution:r} of triggers){
 if(!r)continue;
 const text=fs.readFileSync(path.join(__dirname,'reviewed',r.key+'.resolved'),'utf8');
 if(r.path.endsWith('.json')){
  const j=JSON.parse(text);if(j.status!=='blocked'||j.previousObservations[0].evidence.status!=='blocked')throw Error(r.path);
 }else{
  const src=ts.createSourceFile(r.path,text,ts.ScriptTarget.Latest,true,r.path.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS);
  if(src.parseDiagnostics.length)throw Error(r.path+': '+src.parseDiagnostics.map(d=>ts.flattenDiagnosticMessageText(d.messageText,' ')).join('\n'));
  count++;
 }
}
console.log(`${count} TS/TSX files parse; both blocked evidence observations retained.`);
