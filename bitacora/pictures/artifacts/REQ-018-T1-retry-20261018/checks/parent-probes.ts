import { bibliotecaVisible } from "../pictures/src/lib/biblioteca-sempertex/biblioteca";
import { recomendarPorCategoria, preferenciasDeTexto } from "../pictures/src/lib/biblioteca-sempertex/recomendaciones-categoria";
const base=bibliotecaVisible()[0]!;
const idea=(titulo:string,tematica:string)=>({...base,id:"probe",titulo,tematica,eventos:["Boda"],edad:null});
const cases=[
 {name:"multiword lexical style",candidate:idea("Aro arcoíris","Arcoíris"),query:{categoria:"Boda",mensaje:"quiero tema arco iris"},expected:1},
 {name:"negative theme marker",candidate:idea("Aro gótico","Gótico"),query:{categoria:"Boda",mensaje:"no quiero temática gótica"},expected:0},
 {name:"stored only-colours marker",candidate:idea("Aro blanco y dorado","Blanco y dorado"),query:{categoria:"Boda",tematica:"solo blanco y dorado"},expected:1}
];
console.log(JSON.stringify(cases.map(c=>({name:c.name,expected:c.expected,actual:recomendarPorCategoria([c.candidate],c.query).ideas.length,preferences:preferenciasDeTexto(c.query)})),null,2));
