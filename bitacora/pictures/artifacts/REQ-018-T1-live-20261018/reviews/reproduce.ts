import assert from "node:assert/strict";
import { bibliotecaVisible } from "../pictures/src/lib/biblioteca-sempertex/biblioteca";
import { recomendarPorCategoria, preferenciasDeTexto } from "../pictures/src/lib/biblioteca-sempertex/recomendaciones-categoria";
import { ideasEstrictasDeCategoria } from "../pictures/src/lib/ia/guiado/ideas-guiadas";
const base = bibliotecaVisible()[0]!;
const boda = (titulo: string, tematica: string) => ({...base,id:"probe-wedding",titulo,tematica,eventos:["Boda"],edad:null});
const probes = [
  {id:"F1",description:"Style inferred from colour affinity",result:recomendarPorCategoria([boda("Arco negro y dorado","Negro y dorado")],{categoria:"Boda",tematica:"elegante"}).ideas.map(x=>x.id)},
  {id:"F2a",description:"Repeated negative marker retained as excluded literal",preferences:preferenciasDeTexto({mensaje:"sin flores y sin gótico"}),result:recomendarPorCategoria([boda("Arco gótico","Gótico")],{categoria:"Boda",mensaje:"sin flores y sin gótico"}).ideas.map(x=>x.id)},
  {id:"F2b",description:"Positive clause interpreted as exclusion",preferences:preferenciasDeTexto({mensaje:"sin negro y con dorado"}),result:recomendarPorCategoria([boda("Arco dorado","Dorado")],{categoria:"Boda",mensaje:"sin negro y con dorado"}).ideas.map(x=>x.id)},
  {id:"F3",description:"Explicit unknown style discarded",preferences:preferenciasDeTexto({mensaje:"quiero un estilo gótico"}),result:recomendarPorCategoria([boda("Arco dorado","Dorado")],{categoria:"Boda",mensaje:"quiero un estilo gótico"}).ideas.map(x=>x.id)},
  {id:"F4",description:"Negative gender becomes positive",result:ideasEstrictasDeCategoria({evento:"Baby shower",ultimoUsuario:"no quiero niña"}).ideas.map(x=>x.id),gender:ideasEstrictasDeCategoria({evento:"Baby shower",ultimoUsuario:"no quiero niña"}).genero}
];
assert.equal(probes[0]!.result.length,1);
assert.equal(probes[1]!.result.length,1);
assert.equal(probes[2]!.result.length,0);
assert.equal(probes[3]!.result.length,1);
assert.equal(probes[4]!.gender,"nina");
assert.ok(probes[4]!.result.includes("deco-real-29-arco-link-o-loon-fucsia-tulipanes"));
console.log(JSON.stringify({reproduced_defects:true,probes},null,2));
