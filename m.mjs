const {recomendarPorCategoria:r}=await import(process.argv[2]+"/src/lib/biblioteca-sempertex/recomendaciones-categoria.ts");
const {bibliotecaVisible}=await import(process.argv[2]+"/src/lib/biblioteca-sempertex/biblioteca.ts");
const reales=bibliotecaVisible();
const out=[];
for (const m of ["sin flores de papel","sin globos de colores","sin dorado en la boda","sin rosa para una boda","sin luces de navidad","sin personajes de disney","sin letras de globo","sin dorado por favor","sin guirnaldas de papel crepe","sin nombre de ella"]) for (const cat of ["boda","cumpleaños"]) {const x=r(reales,{categoria:cat,mensaje:m,tematica:undefined}); out.push([m,cat,x.ideas.map(i=>i.id).join(","),x.ideas.map(i=>i.coincidencia).join(",")]);}
console.log(JSON.stringify(out));
