import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { LayoutGroup } from 'motion/react';
import { SharedEntityName } from '/home/david/dev/maros/maros-next/src/components/shared/SharedEntityName';
import { SharedEntitySourceProvider } from '/home/david/dev/maros/maros-next/src/shared/presentation/SharedEntitySourceContext';

function App() {
  const [detail, setDetail] = useState(false);
  const [id, setId] = useState(1);
  return <LayoutGroup><button id="toggle" onClick={() => setDetail(!detail)}>Toggle</button><button id="next" onClick={() => setId(id === 1 ? 2 : 1)}>Next entity</button>{detail ? <section key={`detail-${id}`} style={{margin:'40px 0 0 300px',fontSize:32}}><SharedEntityName layoutId={`title-${id}`} transitionRole="detail">Entity {id}</SharedEntityName></section> : <section key={`list-${id}`} style={{marginTop:350,width:260,height:40,overflow:'auto',fontSize:14}}><SharedEntityName layoutId={`title-${id}`}>Entity {id}</SharedEntityName></section>}</LayoutGroup>;
}
function Aliases() {
  const [detail, setDetail] = useState(false);
  return <SharedEntitySourceProvider><LayoutGroup>{detail ? <><button id="alias-back" onClick={()=>setDetail(false)}>Back</button><h1 style={{position:'absolute',left:700,top:50}}><SharedEntityName layoutId="same-company" transitionRole="detail">Same company</SharedEntityName></h1></> : <div>{[1,2].map(id=><button id={`alias-${id}`} key={id} style={{position:'absolute',left:700,top:200+id*100}} onClick={()=>setDetail(true)}><SharedEntityName layoutId="same-company" sourceInstance={`row-${id}`}>Same company</SharedEntityName></button>)}<button id="alias-default" style={{position:'absolute',left:700,top:550}} onClick={()=>setDetail(true)}><SharedEntityName layoutId="same-company">Same company</SharedEntityName></button></div>}</LayoutGroup></SharedEntitySourceProvider>;
}
createRoot(document.getElementById('root')!).render(<><App/><Aliases/></>);
