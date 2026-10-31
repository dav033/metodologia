import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

export const accountStyles = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:Geist Mono;src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme="light"]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--acento-suave:#ece3fb;--sobre-acento:#ffffff;--exito:#1f7a55;--exito-suave:#dcf5e9;--error:#b23a45;--error-suave:#ffeaec;--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);--destructive:var(--error);--shadow-float:0 18px 40px -12px rgb(28 20 37 / .28);color-scheme:light}
.dark,[data-theme="dark"]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--acento-suave:#241f3d;--sobre-acento:#120b24;--exito:#78d6a8;--exito-suave:#173b31;--error:#ff979f;--error-suave:#43252a;--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);--destructive:var(--error);--shadow-float:0 18px 40px -12px rgb(0 0 0 / .7);color-scheme:dark}
body{margin:0;font-family:Geist,ui-sans-serif,system-ui,sans-serif;font-size:15px;line-height:1.5;background:var(--fondo);color:var(--texto)}
*{box-sizing:border-box}h1,h2,p,dl,dd{margin:0}button,input,select{font:inherit}svg{flex-shrink:0}
.app{--press:90ms;--settle:460ms;--quick:180ms;--ease-press:cubic-bezier(.4,0,.7,1);--ease-settle:cubic-bezier(.34,1.42,.64,1);--stagger:55ms;min-height:calc(100svh - var(--mockup-bar-h));display:flex;flex-direction:column}
.app[data-profile="natural"]{--settle:300ms;--quick:150ms;--stagger:35ms;--ease-settle:cubic-bezier(.3,1.18,.6,1)}
.app[data-profile="subtle"]{--settle:170ms;--quick:110ms;--stagger:15ms;--ease-settle:cubic-bezier(.2,.8,.2,1)}
[data-reduced-motion] .app *,[data-reduced-motion] .app{animation:none!important;transition:none!important}
[data-tab-hidden] .app *{animation-play-state:paused!important}
/* ---- shared signed-in account bar (MenuCuenta) ---- */
.account-bar{min-height:64px;display:flex;align-items:center;justify-content:flex-end;border-bottom:1px solid var(--borde-suave);padding:0 32px}
.account-menu{position:relative;z-index:50}
.menu-trigger{display:flex;align-items:center;gap:8px;min-height:44px;max-width:min(260px,calc(100vw - 32px));padding:0 14px 0 8px;border-radius:999px;border:1px solid var(--borde);background:var(--superficie);color:var(--texto);font-size:14px;font-weight:500;cursor:pointer;transition:transform var(--press) var(--ease-press),border-color var(--quick) ease,box-shadow var(--quick) ease}
.menu-trigger:hover{border-color:var(--acento)}
.menu-trigger:active{transform:scale(.95)}
.menu-trigger[aria-expanded="true"]{border-color:var(--acento);box-shadow:0 0 0 3px var(--acento-suave)}
.menu-trigger:focus-visible,.menu-link:focus-visible,.lang-btn:focus-visible,.signout:focus-visible{outline:2px solid var(--acento);outline-offset:2px}
.menu-trigger .name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.menu-trigger .chev{color:var(--texto-suave);transition:transform var(--settle) var(--ease-settle)}
.menu-trigger[aria-expanded="true"] .chev{transform:rotate(180deg)}
.initial{display:grid;place-items:center;flex-shrink:0;border-radius:999px;background:var(--acento-suave);color:var(--acento);font-weight:650;width:28px;height:28px;font-size:12px}
.menu-panel{position:absolute;right:0;top:calc(100% + 8px);width:304px;max-width:calc(100vw - 32px);background:var(--popover);border:1px solid var(--borde);border-radius:24px;padding:16px;box-shadow:var(--shadow-float);transform-origin:top right;font-size:14px}
.menu-who{display:grid;grid-template-columns:40px minmax(0,1fr);gap:12px;align-items:start}
.menu-who .initial{width:40px;height:40px;font-size:16px}
.menu-name{font-weight:600;overflow-wrap:anywhere;line-height:1.35}
.menu-email{font-size:13px;color:var(--texto-suave);overflow-wrap:anywhere;margin-top:2px}
.access-chip{display:inline-flex;gap:6px;align-items:baseline;margin-top:10px;padding:3px 12px;border-radius:999px;background:var(--superficie-2);font-size:13px;max-width:100%}
.access-chip span{color:var(--texto-suave)}.access-chip b{font-weight:600;overflow-wrap:anywhere}
.menu-lang{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid var(--borde-suave);font-size:13px;color:var(--texto-suave)}
.lang-pair{display:flex;gap:4px}
.lang-btn{min-height:36px;min-width:44px;border-radius:10px;border:1px solid var(--borde);background:var(--superficie);color:var(--texto);font-size:12px;font-weight:650;cursor:pointer;transition:transform var(--press) var(--ease-press),background-color var(--quick) ease}
.lang-btn:active{transform:scale(.92)}
.lang-btn[aria-pressed="true"]{background:var(--acento);color:var(--sobre-acento);border-color:var(--acento)}
.menu-links{display:grid;gap:2px;margin-top:12px;padding-top:8px;border-top:1px solid var(--borde-suave)}
.menu-link,.signout{display:flex;align-items:center;min-height:44px;padding:0 12px;border-radius:12px;color:var(--acento);font-weight:550;text-decoration:none;border:0;background:none;text-align:left;cursor:pointer;transition:transform var(--press) var(--ease-press),background-color var(--quick) ease}
.menu-link:hover{background:var(--acento-suave)}
.menu-link:active,.signout:active{transform:scale(.97)}
.menu-link[aria-current="page"]{color:var(--texto);background:var(--superficie-2)}
.signout{color:var(--texto);margin-top:6px;border-top:1px solid var(--borde-suave);border-radius:0 0 12px 12px;padding-top:4px}
.signout:hover{background:var(--superficie-suave)}
.signout:disabled{opacity:.65;cursor:progress}
.menu-alert{font-size:12px;color:var(--error);padding:4px 12px 0}
/* ---- page column (CabeceraCuentas + NavegacionCuentas) ---- */
.column{width:100%;max-width:676px;margin:0 auto;padding:32px 28px 48px;flex:1}
.cabecera{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 0}
.brand{display:flex;align-items:center;gap:12px;min-width:0;font-size:14px;font-weight:600;letter-spacing:.02em}
.brand-ring{display:grid;place-items:center;width:32px;height:32px;border-radius:999px;border:2px solid var(--acento);flex-shrink:0}
.brand-ring i{width:8px;height:8px;border-radius:999px;background:var(--acento)}
.brand .co{font-weight:400;color:var(--texto-suave)}
.idioma{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--texto-suave)}
.idioma select{min-height:40px;border-radius:14px;border:1px solid var(--texto-tenue);background:var(--superficie);color:var(--texto);padding:4px 10px}
.page-title{font-size:24px;font-weight:600;letter-spacing:-.02em;line-height:1.25}
.page-sub{margin-top:8px;font-size:14px;color:var(--texto-suave)}
.route-nav{display:flex;flex-wrap:wrap;gap:8px 20px;border-bottom:1px solid var(--borde-suave);padding:12px 0;margin-bottom:24px;font-size:14px}
.route-nav a{color:var(--texto-suave);text-decoration:none}.route-nav a:hover{color:var(--texto)}
.route-nav a[aria-current="page"]{color:var(--texto);font-weight:600}
/* ---- v2 identity sheet: one paper, ruled rows, password edited in place ---- */
.ficha{background:var(--superficie);border:1px solid var(--borde-suave);border-radius:32px;overflow:hidden;animation:settle-in var(--settle) var(--ease-settle) both}
@keyframes settle-in{0%{opacity:.001;transform:translateY(14px) scale(.985)}100%{opacity:1;transform:none}}
.ficha h2{font-size:13px;font-weight:600;color:var(--texto-suave);padding:24px 28px 0}
.plate{display:grid;grid-template-columns:64px minmax(0,1fr);gap:20px;align-items:center;padding:16px 28px 24px}
.plate .initial{width:64px;height:64px;font-size:26px;animation:press-settle calc(var(--settle) + 120ms) var(--ease-settle) both}
@keyframes press-settle{0%{transform:scale(.82)}55%{transform:scale(1.04)}100%{transform:scale(1)}}
.id-pair{display:grid;gap:10px;min-width:0}
.id-pair dt{font-size:12px;color:var(--texto-suave)}
.id-name{font-size:20px;font-weight:600;line-height:1.3;letter-spacing:-.01em;overflow-wrap:anywhere}
.id-email{font-size:15px;overflow-wrap:anywhere}
.fila{display:grid;grid-template-columns:132px minmax(0,1fr) auto;gap:16px;align-items:center;min-height:64px;padding:12px 28px;border-top:1px solid var(--borde-suave);animation:row-in var(--settle) var(--ease-settle) both;animation-delay:calc(var(--i,0) * var(--stagger))}
@keyframes row-in{0%{opacity:.001;transform:translateX(-10px)}100%{opacity:1;transform:none}}
.fila .k{font-size:13px;color:var(--texto-suave)}
.fila .v{font-weight:550;overflow-wrap:anywhere;min-width:0}
.rows{margin:0}
.fila .masked{letter-spacing:.2em;color:var(--texto-suave);font-weight:600}
.fila[data-editing="true"]{background:var(--superficie-suave)}
.fila-pass{transition:background-color var(--quick) ease}
.act{min-height:44px!important;height:auto!important;padding:10px 18px!important;border-radius:999px!important;font-weight:600!important;font-size:14px!important;white-space:normal!important;transition:transform var(--press) var(--ease-press),background-color var(--quick) ease,border-color var(--quick) ease!important}
.act:active{transform:scale(.95)!important}
.act[data-variant="primary"]{background:var(--acento)!important;color:var(--sobre-acento)!important;border:1px solid var(--acento)!important}
.act[data-variant="primary"]:hover{background:var(--acento-hover)!important}
.act[data-variant="outline"]{background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important}
.act[data-variant="outline"]:hover{border-color:var(--acento)!important}
.act[data-variant="quiet"]{background:transparent!important;color:var(--acento)!important;border:1px solid transparent!important}
.act:focus-visible{outline:2px solid var(--acento)!important;outline-offset:2px}
.drawer{overflow:hidden;background:var(--superficie-suave);border-top:1px dashed var(--borde)}
.editor{display:grid;gap:18px;padding:20px 28px 28px}
.editor .field{display:grid;gap:8px;animation:field-in var(--settle) var(--ease-settle) both;animation-delay:calc(var(--i,0) * var(--stagger))}
@keyframes field-in{0%{opacity:.001;transform:translateY(-8px)}100%{opacity:1;transform:none}}
.field label{font-size:14px;font-weight:600}
[data-slot=input].pw{height:48px;border-radius:18px;border:1px solid var(--texto-tenue);background:var(--superficie);color:var(--texto);padding:0 16px;font-size:16px;box-shadow:none;transition:border-color var(--quick) ease,box-shadow var(--quick) ease,transform var(--press) var(--ease-press)}
[data-slot=input].pw:focus-visible{border-color:var(--acento);box-shadow:0 0 0 3px var(--acento-suave);outline:none}
[data-slot=input].pw[aria-invalid=true]{border-color:var(--error);animation:nudge 260ms var(--ease-press)}
@keyframes nudge{0%,100%{transform:none}30%{transform:translateX(-4px)}65%{transform:translateX(3px)}}
.field-help{display:block;position:relative;font-size:13px;color:var(--texto-suave)}
.field-help[data-ok="true"]{color:var(--exito)}
.field-help svg{position:absolute;left:-19px;top:3px;width:14px;height:14px;animation:press-settle var(--settle) var(--ease-settle) both}
.field-error{display:block;position:relative;font-size:13px;color:var(--error);text-align:left}
.field-error svg{position:absolute;left:-20px;top:2px;width:15px;height:15px}
.meter{height:4px;border-radius:999px;background:var(--superficie-2);overflow:hidden}
.meter i{display:block;height:100%;background:var(--acento);border-radius:999px;transform-origin:left;transition:transform var(--quick) var(--ease-settle)}
.meter[data-ok="true"] i{background:var(--exito)}
.summary{display:flex;gap:10px;align-items:flex-start;border-radius:18px;padding:12px 16px;font-size:14px;background:var(--error-suave);color:var(--error)}
.summary svg{width:18px;height:18px;margin-top:1px}
.editor-actions{display:flex;flex-wrap:wrap;gap:12px;align-items:center;animation:field-in var(--settle) var(--ease-settle) both;animation-delay:calc(var(--i,0) * var(--stagger))}
.spin{animation:spin .9s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
.sealed{grid-column:1/-1;display:flex;gap:10px;align-items:flex-start;padding:12px 16px;border-radius:18px;background:var(--exito-suave);color:var(--exito);font-size:14px;animation:seal var(--settle) var(--ease-settle) both}
@keyframes seal{0%{opacity:.001;transform:scale(.96)}100%{opacity:1;transform:none}}
.seal-check{width:18px;height:18px;margin-top:1px}
.seal-check path{stroke-dasharray:24;stroke-dashoffset:24;animation:draw calc(var(--settle) + 140ms) var(--ease-press) 120ms forwards}
@keyframes draw{to{stroke-dashoffset:0}}
[data-reduced-motion] .seal-check path{stroke-dashoffset:0}
.skeleton-rows{display:grid;gap:16px;padding:28px}
.skeleton-rows [data-slot=skeleton]{background:var(--superficie-2);border-radius:12px}
.unchanged{border:1px dashed var(--borde);border-radius:24px;padding:24px;color:var(--texto-suave);font-size:14px;animation:settle-in var(--settle) var(--ease-settle) both}
.foot{margin-top:24px;font:12px/1.5 'Geist Mono',monospace;color:var(--texto-suave)}
@media (max-width:1023px){.account-bar{padding:0 24px}}
@media (max-width:639px){
 .account-bar{padding:0 16px}
 .column{padding:20px 20px 40px}
 .cabecera{flex-wrap:wrap}
 .ficha{border-radius:24px}
 .ficha h2{padding:20px 20px 0}
 .plate{grid-template-columns:48px minmax(0,1fr);gap:14px;padding:14px 20px 20px}
 .plate .initial{width:48px;height:48px;font-size:20px}
 .id-name{font-size:18px}
 .fila{grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;padding:12px 20px}
 .fila .k{grid-column:1/-1}
 .fila-pass .act{grid-column:1/-1;width:100%}
 .editor{padding:18px 20px 24px}
 .editor-actions .act{flex:1 1 100%}
 .menu-panel{position:fixed;left:16px;right:16px;top:calc(var(--mockup-bar-h) + 72px);width:auto;max-width:none}
 .menu-trigger{max-width:calc(100vw - 32px)}
}
`;
