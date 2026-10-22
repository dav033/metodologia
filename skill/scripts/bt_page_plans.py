"""Plans view: list of every plan and a live, read-only detail page (milestones, tasks, attempts, models, accounts).

Pure functions: data in, HTML out. The live regions are `[data-k]` leaves inside `#live`; the inline script patches
only the leaves whose HTML changed and flashes them, so open attempt histories stay open.
"""
from __future__ import annotations

import re
from html import escape as e
from urllib.parse import quote

import bt_page_attempts as attempts_
import bt_page_diagnosis as dx
from bt_pages import layout

LEVELS = ("low", "medium", "high", "extreme")
LEVEL_ES = {"low": "baja", "medium": "media", "high": "alta", "extreme": "extrema"}
STATE_ES = {"pending": "pendiente", "ready": "lista", "running": "en curso", "verifying": "verificando",
            "completed": "completada", "rejected": "rechazada", "blocked": "bloqueada", "cancelled": "cancelada"}

CSS = """<style>
.pl{--lvl-low:#a6e3a1;--lvl-medium:#f9e2af;--lvl-high:#fab387;--lvl-extreme:#f38ba8;--mauve:#cba6f7;--lav:#b4befe}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]) .pl{--lvl-low:#2f7d32;--lvl-medium:#8a6a00;--lvl-high:#b4540a;--lvl-extreme:#b3193e;--mauve:#8839ef;--lav:#5b5fc7}}
:root[data-theme="light"] .pl{--lvl-low:#2f7d32;--lvl-medium:#8a6a00;--lvl-high:#b4540a;--lvl-extreme:#b3193e;--mauve:#8839ef;--lav:#5b5fc7}
.pl .pill{display:inline-block;font-size:12px;padding:1px 9px;border-radius:99px;border:1px solid var(--border);background:none;white-space:nowrap;cursor:default;transform:none}.pl .pill:hover{transform:none;border-color:var(--border)}
.pl .lvl-low{color:var(--lvl-low);border-color:var(--lvl-low)}.pl .lvl-medium{color:var(--lvl-medium);border-color:var(--lvl-medium)}
.pl .lvl-high{color:var(--lvl-high);border-color:var(--lvl-high)}.pl .lvl-extreme{color:var(--lvl-extreme);border-color:var(--lvl-extreme);font-weight:600}
.pl .top{display:flex;flex-wrap:wrap;align-items:flex-end;gap:14px 32px;margin:0 0 30px}
.pl .eyebrow{font:500 12px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
.pl .top h1{margin:0}.pl .seg{margin-left:auto;display:flex;gap:6px}
.pl .seg a{padding:7px 16px;border-radius:99px;border:1px solid var(--border);color:var(--muted);font-size:13.5px}
.pl .seg a:hover{text-decoration:none;color:var(--text);border-color:var(--accent)}
.pl .seg a.on{background:var(--accent);border-color:var(--accent);color:var(--on-accent);font-weight:700}
.pl .mosaic{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;align-items:stretch}
.pl .mosaic>p{grid-column:1/-1}
.pl .card{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:24px;display:flex;flex-direction:column;gap:18px;min-width:0}
.pl .card.wide{grid-column:span 2}
.pl .card .hd{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px}
.pl .card h2{margin:0;font-size:21px;font-weight:700;letter-spacing:-.01em}.pl .card h2 a{color:var(--text)}.pl .card h2 a:hover{color:var(--accent);text-decoration:none}
.pl .card .meta{margin:0 0 0 auto;font:400 12px var(--mono);color:var(--muted);text-align:right;white-space:nowrap}
.pl .card .meta .live{color:var(--info)}
.pl .tk{display:flex;justify-content:space-between;font:400 12px var(--mono);color:var(--muted);margin-bottom:8px}.pl .tk b{font-weight:500;color:var(--text)}
.pl .bar{height:8px;border-radius:4px;background:var(--code);overflow:hidden}
.pl .bar>i{display:block;height:100%;background:var(--accent);border-radius:4px}
.pl .chips{display:flex;flex-wrap:wrap;gap:8px}
.pl .chip{display:inline-flex;align-items:center;gap:7px;padding:4px 11px;border-radius:99px;background:var(--code);color:var(--text);font-size:12.5px;font-weight:600}
.pl .dot{width:8px;height:8px;border-radius:50%;background:var(--muted);display:block;flex:none}
.pl .st{display:inline-flex;align-items:center;gap:8px;font:400 12px var(--mono);color:var(--muted);white-space:nowrap}
.pl .dot.bad{background:var(--bad)}.pl .st.bad{color:var(--bad)}.pl .st.off .dot{background:var(--muted)}
.pl .dot.info{background:var(--info)}.pl .dot.warn{background:var(--warn)}.pl .dot.ok{background:var(--ok)}
.pl .dot.live{box-shadow:0 0 0 3px color-mix(in srgb,var(--info) 30%,transparent)}
.pl .rows{display:flex;flex-direction:column}
.pl .prow{display:grid;grid-template-columns:62px minmax(0,1fr) auto;gap:12px;align-items:center;padding:10px 0;border-top:1px solid var(--border)}
.pl .prow .id{font:400 12px var(--mono);color:var(--muted)}
.pl .prow a.t{color:var(--text);font-weight:500;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.pl .prow a.t:hover{color:var(--accent);text-decoration:none}
.pl .prow.done a.t{color:var(--muted);font-weight:400}
.pl .prow .st{display:flex;align-items:center;gap:8px;font:400 12px var(--mono);color:var(--muted);white-space:nowrap}
.pl .st.info{color:var(--info)}.pl .st.warn{color:var(--warn)}.pl .st.ok{color:var(--ok)}
.pl .card details>summary{cursor:pointer;color:var(--muted);font-size:13px;padding:10px 0 0;list-style:none;border-top:1px solid var(--border)}
.pl .card details>summary::before{content:"▸ "}.pl .card details[open]>summary::before{content:"▾ "}
.pl .card details>summary:hover{color:var(--text)}.pl .card details[open]{margin-top:-6px}
.pl .card details .rows{margin-top:6px}
.pl .sub{font:500 11px var(--mono);letter-spacing:.09em;text-transform:uppercase;color:var(--muted);padding:20px 0 4px}.pl .sub:first-child{padding-top:0}
.pl details.fin>summary{cursor:pointer;color:var(--muted);font-size:13px;padding:12px 0;list-style:none;border-top:1px solid var(--border)}
.pl details.fin>summary::before{content:"▸ "}.pl details.fin[open]>summary::before{content:"▾ "}.pl details.fin>summary:hover{color:var(--text)}
.pl .card .go{margin-top:auto;font-size:13.5px;font-weight:600}
@media (max-width:1000px){.pl .mosaic{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:640px){.pl .mosaic{grid-template-columns:1fr}.pl .card.wide{grid-column:auto}.pl .seg{margin-left:0}}
@media (max-width:640px){.pl .task{grid-template-columns:40px minmax(0,1fr)}.pl .task>*:not(.tid){grid-column:2;min-width:0}.pl .task .meta{white-space:normal;text-align:left;margin:0;overflow-wrap:anywhere}.pl .task .meta span{overflow-wrap:anywhere}}
.pl .ms{border:1px solid var(--border);border-radius:18px;background:var(--surface);margin:0 0 20px;padding:8px 24px 14px}
.pl .mh{display:flex;gap:8px 14px;align-items:center;flex-wrap:wrap;padding:14px 0;border-bottom:1px solid var(--border)}
.pl .mh b{font:500 12px var(--mono);color:var(--accent)}.pl .mh .mt{font-weight:700;font-size:17px;letter-spacing:-.01em}
.pl .mh .cnt{margin-left:auto;font:400 12px var(--mono);color:var(--muted)}.pl .mh .mbar{width:120px}
.pl .task{display:grid;grid-template-columns:48px minmax(0,1fr) auto;gap:6px 14px;align-items:start;padding:12px 0;border-bottom:1px solid var(--border)}
.pl .task:last-child{border-bottom:0}.pl .task .tid{font:500 12px var(--mono);color:var(--muted);padding-top:2px}
.pl .task .tt{font-weight:500}.pl .task .sub2{grid-column:2/-1}
.pl .tl{display:flex;gap:8px 10px;align-items:center;flex-wrap:wrap}
.pl .chip{display:inline-flex;align-items:center;gap:7px;padding:2px 10px;border-radius:99px;background:var(--code);color:var(--muted);font:400 11.5px var(--mono)}
.pl .meta{font-size:13px;color:var(--muted);margin:2px 0 0 0}.pl .meta b{color:var(--text);font-weight:600}
.pl details{margin-top:4px;font-size:13px}.pl details summary{cursor:pointer;color:var(--accent)}
.pl table.att{margin-top:6px;white-space:nowrap}.pl table.att td,.pl table.att th{padding:3px 12px 3px 0;font-size:12px}.pl .tscroll{overflow-x:auto}
.pl .amends{display:flex;gap:6px 14px;flex-wrap:wrap}.pl .amend{font:400 12px var(--mono);color:var(--warn)}.pl .amend s{color:var(--muted)}.pl details.evo{margin:0 0 18px}.pl details.evo ol{margin:8px 0 0 18px;padding:0;font:400 12.5px var(--mono);color:var(--muted)}
.pl .mchip{font:500 12px var(--mono);color:var(--lav)}.pl .muted{color:var(--muted)}.pl .blocked{color:var(--bad);margin-top:6px}.pl .blocked a{color:var(--bad);text-decoration:underline}.pl .working{color:var(--info)}.pl .working .dot{display:inline-block;margin-right:6px;vertical-align:middle}
.pl .phead{margin:0 0 28px}.pl .phead h1{margin:0 0 14px}.pl .phead .bar{margin-top:16px}
.pl .back{display:inline-block;margin:0 0 16px;font-size:13.5px}
.pl .flash-new{animation:plflash 1.6s ease-out}
@keyframes plflash{from{background:color-mix(in srgb,var(--mauve) 35%,transparent)}to{background:transparent}}
.pl .asks{display:grid;gap:12px}.pl .ask-pill{border-color:var(--warn);color:var(--warn);margin-left:6px;cursor:pointer}.pl .ask{border:1px solid var(--accent);border-radius:var(--radius);padding:12px 16px}.pl .ask .opt{margin:10px 0}.pl .ask textarea{width:100%;min-height:64px;box-sizing:border-box}.pl .ask button{min-height:44px;padding:8px 16px;border-radius:var(--radius);border:1px solid var(--accent);background:var(--surface);color:var(--text);cursor:pointer}.pl .ask button.primary{background:var(--accent);color:var(--on-accent)}
.pl .run-plan{margin:18px 0}.pl .run-plan button{min-height:44px;padding:10px 22px;font-size:1.05em;background:var(--accent);color:var(--on-accent);border:0;border-radius:var(--radius);cursor:pointer;font-weight:600}
.pl .danger{border:1px solid var(--bad);border-radius:var(--radius);padding:14px 18px;margin:18px 0}
.pl .msg{padding:12px 16px;border-radius:var(--radius);background:var(--accent-soft);color:var(--text);margin:0 0 20px}
.pl .task:target,.pl tr:target{outline:2px solid var(--accent);outline-offset:2px;border-radius:8px}
.pl .task .obj{margin:4px 0 0;color:var(--text);font-size:14px;line-height:1.5;max-width:90ch}
.pl .task .tmiss{margin:6px 0 0;padding:6px 10px;border-radius:8px;background:var(--bad-soft);color:var(--bad);font-size:13px}
.pl .tdet{margin:8px 0 0}.pl .tdet summary{cursor:pointer;font-size:13px;color:var(--accent)}
.pl .tdet h4{margin:12px 0 4px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.pl .tdet ol,.pl .tdet ul{margin:0;padding-left:20px;font-size:13.5px;line-height:1.5}
.pl .tdet ul.checks>li{margin:4px 0}.pl .tdet code{font:500 12.5px var(--mono);overflow-wrap:anywhere}
.pl h2.grp{color:var(--mauve)}.pl .live-dot{font-size:12px;color:var(--muted)}
</style>"""

JS = """<script>
(function(){
var live=document.getElementById('live'); if(!live) return;
var sel='[data-k]';
function leaves(n){return Array.prototype.slice.call(n.querySelectorAll(sel));}
// [data-v] holds values that tick while something runs (duration, tokens): they are patched in place, never a reason
// to replace a block and flash it (that blinked every few seconds and closed what the reader had open)
function sigOf(n){var c=n.cloneNode(true); Array.prototype.forEach.call(c.querySelectorAll('[data-v]'),function(x){x.textContent='';}); return c.outerHTML;}
function mark(n){n._full=n.outerHTML; n._sig=sigOf(n);}
leaves(live).forEach(mark);
function openIdx(n){return Array.prototype.map.call(n.querySelectorAll('details'),function(d){return d.open;});}
function apply(html){
  var t=document.createElement('template'); t.innerHTML=html;
  var nw=leaves(t.content), old=leaves(live);
  var same=nw.length===old.length&&nw.every(function(n,i){return n.dataset.k===old[i].dataset.k;});
  if(!same){live.replaceChildren(t.content); leaves(live).forEach(mark); return;}
  nw.forEach(function(n,i){
    var o=old[i], full=n.outerHTML, sig=sigOf(n); if(o._full===full) return;
    if(o._sig===sig){
      var ov=o.querySelectorAll('[data-v]'), nv=n.querySelectorAll('[data-v]');
      for(var j=0;j<ov.length&&j<nv.length;j++){if(ov[j].innerHTML!==nv[j].innerHTML) ov[j].innerHTML=nv[j].innerHTML;}
      o._full=full; return;
    }
    var opened=openIdx(o);
    o.replaceWith(n); mark(n);
    Array.prototype.forEach.call(n.querySelectorAll('details'),function(d,j){if(opened[j]) d.open=true;});
    n.classList.add('flash-new'); setTimeout(function(){n.classList.remove('flash-new');},1700);
  });
}
// a link to a task (#t-T4) or an attempt (#a-att-0007): open what hides it, bring it into view, mark it
function reveal(){var id=decodeURIComponent(location.hash.slice(1)); var n=id&&document.getElementById(id); if(!n) return;
  for(var p=n.parentElement;p;p=p.parentElement){if(p.tagName==='DETAILS') p.open=true;}
  if(n.classList.contains('task')) Array.prototype.forEach.call(n.querySelectorAll('details.tdet'),function(d){d.open=true;});
  n.scrollIntoView({block:'center'}); n.classList.add('flash-new'); setTimeout(function(){n.classList.remove('flash-new');},1700);}
reveal(); window.addEventListener('hashchange',reveal);
var dot=document.getElementById('live-dot');
function state(t){if(dot) dot.textContent=t;}
function refresh(){fetch(live.dataset.api,{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){if(d.html) apply(d.html);}).catch(function(){});}
var poll=null;
function startPoll(){if(!poll){poll=setInterval(refresh,3000); state('● sondeo cada 3 s');}}
function stopPoll(){if(poll){clearInterval(poll); poll=null;}}
if(/[?&]live=0(&|$)/.test(location.search)){ /* static page: screenshots and tests */ }
else if(window.EventSource){
  var es=new EventSource(live.dataset.events);
  es.onopen=function(){stopPoll(); state('● en vivo'); refresh();};
  es.onerror=function(){startPoll();};
  es.addEventListener(live.dataset.event,function(ev){try{apply(JSON.parse(ev.data).html);}catch(x){}});
} else {startPoll();}
})();
</script>"""


def _pill(cls: str, text: str) -> str:
    return f'<span class="pill {e(cls)}">{e(text)}</span>'


def level_badge(level: str | None) -> str:
    return _pill(f"lvl-{level}", LEVEL_ES.get(level, level)) if level in LEVELS else ""


STATE_TONE = {"completed": "ok", "running": "info", "verifying": "info", "ready": "warn", "blocked": "bad", "rejected": "bad"}


def state_badge(state: str | None) -> str:
    tone = STATE_TONE.get(state or "", "off")
    return f'<span class="st {tone}"><i class="dot {tone}"></i>{e(STATE_ES.get(state or "", state or "—"))}</span>'


def bar(done: int, total: int) -> str:
    pct = round(100 * done / total) if total else 0
    return f'<div class="bar" title="{done}/{total}"><i style="width:{pct}%"></i></div>'


def _purl(project: str, req: str) -> str:
    return f"/plans/{quote(project)}/{quote(req)}"


FINISHED = ("done", "superseded", "cancelled", "archived")
STATUS_ES = {"approved": "aprobado", "in-progress": "en curso", "in progress": "en curso", "review": "en revisión",
             "paused": "pausado", "draft": "borrador", "clarifying": "aclarando", "blocked": "bloqueado",
             "stopped": "detenido", "launched": "lanzado", "planned": "planificado"}
TONE = (("info", ("approved", "in-progress", "in progress", "launched", "running", "verifying")),
        ("warn", ("review", "paused", "draft", "clarifying", "blocked", "stopped")),
        ("ok", ("done", "completed")))
FEATURED_ROWS, CARD_ROWS = 5, 3


def _short(status: str | None) -> str:
    """Plan statuses are free text in some repos; keep the leading word(s). The full text stays as tooltip."""
    text = (status or "").strip()
    head = re.split(r"\s+(?:[(—-]|\d{4}-\d{2})", text, maxsplit=1)[0].strip()
    return head if len(head) <= 16 else head[:15] + "…"


def _finished(r: dict) -> bool:
    return not r["active"] and (r["plan_status"] or "").lower().startswith(FINISHED)


def _plain_title(title: str | None, req_id: str) -> str:
    return re.sub(r"^REQ-\d+\s*[—–:-]\s*", "", title or "") or req_id


def _tone(status: str | None) -> str:
    low = (status or "").lower()
    return next((t for t, words in TONE if low.startswith(words)), "off")


def _label(r: dict) -> str:
    word = _short(r["run_status"] if r["active"] else r["plan_status"]).lower()
    return STATUS_ES.get(word, word) or "sin estado"


def index_fragment(rows: list[dict], filt: str = "all") -> str:
    by_project: dict[str, list[dict]] = {}
    for r in rows:
        by_project.setdefault(r["project"], []).append(r)
    # live runs first, then the most open work; the first card is the wide one
    ordered = sorted(by_project.items(), key=lambda kv: (-sum(r["active"] for r in kv[1]),
                                                        -sum(not _finished(r) for r in kv[1]), kv[0]))
    if not ordered:
        return '<p class="muted" data-k="none">No hay planes que mostrar.</p>'
    return "".join(_card(name, rs, wide=i == 0 and len(ordered) > 2) for i, (name, rs) in enumerate(ordered))


def _card(name: str, rows: list[dict], wide: bool) -> str:
    live = [r for r in rows if r["active"]]
    work = live + [r for r in rows if not r["active"] and not _finished(r)]
    fin = [r for r in rows if _finished(r)]
    done = sum(r["progress"]["done"] for r in work)
    total = sum(r["progress"]["total"] for r in work)
    pct = round(100 * done / total) if total else 0
    work.sort(key=lambda r: (not r["active"], -(r["progress"]["done"] / r["progress"]["total"]
                                                    if r["progress"]["total"] else 0), r["req_id"]))
    counts: dict[str, list] = {}
    for r in work:
        counts.setdefault(_label(r), [_tone(r["plan_status"]), 0])[1] += 1
    chips = "".join(f'<span class="chip"><i class="dot {t}"></i>{e(lab)} · {n}</span>' for lab, (t, n) in counts.items())
    if fin:
        chips += f'<span class="chip"><i class="dot ok"></i>terminados · {len(fin)}</span>'
    meta = f'{len(rows)} {"plan" if len(rows) == 1 else "planes"} · {len(work)} {"abierto" if len(work) == 1 else "abiertos"}' + (
        f' · <span class="live">{len(live)} en ejecución</span>' if live else "")
    shown = FEATURED_ROWS if wide else CARD_ROWS
    rest = work[shown:] + fin
    more = (f'<details><summary>Ver el resto ({len(rest)})</summary><div class="rows">'
            f'{"".join(_row(r) for r in rest)}</div></details>' if rest else "")
    return (f'<article class="card{" wide" if wide else ""}" data-k="c-{e(name)}"><div class="hd">'
            f'<h2><a href="/p/{quote(name)}">{e(name)}</a></h2><div class="meta">{meta}</div></div>'
            f'<div><div class="tk"><span>tareas hechas</span><b>{done} / {total}</b></div>'
            f'<div class="bar"><i style="width:{pct}%"></i></div></div>'
            f'<div class="chips">{chips}</div>'
            f'<div class="rows">{"".join(_row(r) for r in work[:shown])}</div>{more}'
            f'<a class="go" href="/p/{quote(name)}">Abrir proyecto →</a></article>')


def _row(r: dict) -> str:
    done, total = r["progress"]["done"], r["progress"]["total"]
    title = _plain_title(r["title"], r["req_id"])
    tone = "info" if r["active"] else _tone(r["plan_status"])
    trail = f"{done}/{total}" if total else e(_label(r))
    return (f'<div class="prow{" done" if _finished(r) else ""}"><span class="id">{e(r["req_id"])}</span>'
            f'<a class="t" href="{_purl(r["project"], r["req_id"])}" title="{e(title)}">{e(title)}</a>'
            f'<span class="st {tone}" title="{e(r["plan_status"] or "")}"><i class="dot {tone}{" live" if r["active"] else ""}">'
            f'</i>{trail}</span>{_asks_pill(r)}</div>')


def _asks_pill(r: dict) -> str:
    n = r.get("asks") or 0
    if not n:
        return ""
    return (f'<a class="pill ask-pill" href="{_purl(r["project"], r["req_id"])}#asks" '
            f'title="Esperando tu decisión">⚠ {n}</a>')


def index_page(rows: list[dict], filt: str, trash: dict[str, list[dict]], token: str, msg: str = "") -> str:
    shown = [r for r in rows if r["active"]] if filt == "active" else rows
    live_n = sum(1 for r in rows if r["active"])
    tabs = "".join(f'<a href="/plans?filter={k}"{" class=on" if filt == k else ""}>{v} · {n}</a>'
                   for k, v, n in (("active", "En ejecución", live_n), ("all", "Todos", len(rows))))
    body = (f'<div class="pl">{_flash(msg)}<div class="top"><div><p class="eyebrow">{len(rows)} planes · '
            f'{len({r["project"] for r in rows})} proyectos <span class="live-dot" id="live-dot"></span></p>'
            f'<h1>Planes</h1></div><div class="seg">{tabs}</div></div>'
            f'<div id="live" class="mosaic" data-api="/api/plans?filter={e(filt)}&html=1" data-events="/events?filter={e(filt)}" '
            f'data-event="plans">{index_fragment(shown, filt)}</div>{_trash(trash, token)}</div>{CSS}{JS}')
    return layout("Planes", body, [("Planes", "/plans")])


def project_plans(rows: list[dict], limit: int | None = None) -> str:
    """Plans of one project for the project page: live and open first, finished folded. `limit` keeps only open ones."""
    live = [r for r in rows if r["active"]]
    open_ = [r for r in rows if not r["active"] and not _finished(r)]
    fin = [r for r in rows if _finished(r)]
    if not rows:
        return '<p class="muted">Este proyecto todavía no tiene planes.</p>'
    parts = []
    for title, group in (("En ejecución", live), ("Abiertos", open_)):
        if group:
            shown = group[:limit] if limit else group
            head = "" if limit and not live else f'<div class="sub">{title}</div>'
            parts.append(f'{head}<div class="rows">{"".join(_row(r) for r in shown)}</div>')
    if fin and not limit:
        parts.append(f'<details class="fin"{"" if live or open_ else " open"}><summary>Terminados ({len(fin)})</summary>'
                     f'<div class="rows">{"".join(_row(r) for r in fin)}</div></details>')
    return f'<div class="pl">{"".join(parts) or "<p class=muted>Sin planes abiertos.</p>"}</div>{CSS}'


def _flash(msg: str) -> str:
    return f'<div class="msg">{e(msg)}</div>' if msg else ""


def _trash(trash: dict[str, list[dict]], token: str) -> str:
    items = []
    for project, entries in trash.items():
        for t in entries:
            items.append(
                f'<li>{e(project)} · {e(t["req_id"] or "?")} · <span class="muted">{e(t["deleted_at"] or "")}</span> '
                f'<form method="post" action="/plans/{quote(project)}/restore" style="display:inline">'
                f'<input type="hidden" name="token" value="{e(token)}"><input type="hidden" name="entry" value="{e(t["name"])}">'
                f'<button class="secondary" type="submit">Restaurar</button></form></li>')
    if not items:
        return ""
    return f'<h2 class="grp">Papelera</h2><ul class="plain">{"".join(items)}</ul>'


def detail_fragment(s: dict) -> str:
    plan, run, summ = s["plan"], s["run"], s["summary"]
    rev = plan["revision"] if plan["revision"] is not None else "—"
    head = (f'<div class="phead" data-k="head"><p class="eyebrow">{e(s["project"])} · {e(s["req_id"])}</p>'
            f'<h1>{e(_plain_title(s["title"], s["req_id"]))}</h1>'
            f'<div class="tl">{_pill("", "plan · " + str(plan["status"] or "—"))}'
            f'{_pill("", "ejecución · " + str(run["status"] or "sin ejecución"))}{_pill("", run["authority"])}'
            f'<span class="chip">rev {e(str(rev))}</span><span class="chip">sha {e((plan["sha256"] or "—")[:10])}</span>'
            f'{level_badge(summ["difficulty"])}</div>{unclassified_banner(s)}{bar(summ["tasks_done"], summ["tasks_total"])}'
            f'<div class="meta">{summ["tasks_done"]}/{summ["tasks_total"]} tareas · '
            f'{summ["milestones_done"]}/{summ["milestones_total"]} hitos</div></div>')
    parts = [head, _timeline(s)]
    asks = {r["task"]: r for r in s.get("decisions") or [] if r.get("task")}
    for m in s["milestones"]:
        parts.append(f'<div class="ms">{_milestone_head(m)}{"".join(_task(t, asks) for t in m["tasks"])}</div>')
    return "".join(parts)


def _milestone_head(m: dict) -> str:
    return (f'<div class="mh" data-k="mh-{e(str(m["id"]))}"><b>{e(str(m["id"]))}</b><span class="mt">{e(m["title"] or "")}</span>'
            f'{level_badge(m["difficulty"])}{state_badge(m["state"])}'
            f'<span class="cnt">{m["progress"]["done"]}/{m["progress"]["total"]}</span>'
            f'<div class="mbar">{bar(m["progress"]["done"], m["progress"]["total"])}</div></div>')


FIELD_ES = {"complexity": "complejidad", "scope": "alcance", "risk": "riesgo", "coupling": "acoplamiento",
            "confidence": "confianza", "estimated_minutes": "estimación (min)"}


def _value_es(field: str, value) -> str:
    return LEVEL_ES.get(value, str(value)) if field == "complexity" else str(value)


def _amended(t: dict) -> str:
    """`complejidad ~~media~~ → alta · 22:40 · por el agente` for each amendment of the task, evidence on hover."""
    rows = []
    for a in t.get("amendments") or []:
        who = "el agente" if a["proposed_by"] == "agent" else "el dueño"
        proof = e("; ".join(a["evidence"]) or a["reason"])
        rows.append(f'<sl-tooltip content="{proof}"><span class="amend">{e(FIELD_ES.get(a["field"], a["field"]))} '
                    f'<s>{e(_value_es(a["field"], a["from"]))}</s> → <b>{e(_value_es(a["field"], a["to"]))}</b> · '
                    f'{e(a["at"][11:16])} · por {who}</span></sl-tooltip>')
    return f'<div class="meta amends">{"".join(rows)}</div>' if rows else ""


def _timeline(s: dict) -> str:
    items = (s.get("evolution") or {}).get("timeline") or []
    if len(items) < 2 and not (s.get("evolution") or {}).get("amendments"):
        return ""
    rows = []
    for it in items:
        when = e(str(it["at"] or "")[:16].replace("T", " "))
        if it["kind"] == "revision":
            rows.append(f'<li><b>revisión {it["revision"]}</b> congelada · {when}</li>')
        else:
            rows.append(f'<li>{e(it["task"])}: {e(FIELD_ES.get(it["field"], it["field"]))} <s>{e(_value_es(it["field"], it["from"]))}</s>'
                        f' → {e(_value_es(it["field"], it["to"]))} · {when} · {"agente" if it["proposed_by"] == "agent" else "dueño"}'
                        f'{" · r" + str(it["revision"]) if it.get("revision") else ""}</li>')
    return f'<details class="evo"><summary>Evolución del plan ({len(items)})</summary><ol>{"".join(rows)}</ol></details>'


def _unclassified(t: dict) -> str:
    """A task with no difficulty must say so: a plan that "comes without difficulties" is a broken contract."""
    return _pill("bad", "sin clasificar") if t.get("complexity") is None and t.get("state") == "pending" else ""


def unclassified_banner(s: dict) -> str:
    plan, summ = s["plan"], s["summary"]
    missing = sum(1 for m in s["milestones"] for t in m["tasks"] if t.get("complexity") is None)
    if not missing or plan.get("status") not in ("draft", "review", "approved", None) or s["run"]["authority"] != "none":
        return ""
    why = "no tiene PLAN.json" if not plan.get("has_contract") else "su PLAN.json no está clasificado"
    return (f'<div class="warnbox" data-k="unclassified"><b>Plan sin clasificar:</b> {missing} de {summ["tasks_total"]} '
            f'tareas no tienen dificultad ({why}). No se puede aprobar ni lanzar así. Para clasificarlo y ejecutarlo: '
            f'<code>bitacora --project {e(s["project"])} go {e(s["req_id"])}</code></div>')


def _missing_detail(t: dict) -> list[str]:
    """What a task must say and does not: a task nobody can read is a defect of the plan, shown as one."""
    d = t.get("detail")
    if d is None:
        return ["el plan no tiene PLAN.json: no hay objetivo, criterios ni verificación"]
    return [text for key, text in (("objective", "objetivo"), ("acceptance_criteria", "criterios de aceptación"),
                                   ("verification", "verificación")) if not d.get(key)]


def _detail(t: dict) -> str:
    d = t.get("detail") or {}
    missing = _missing_detail(t)
    warn = (f'<div class="tmiss">Falta en el plan: {e(", ".join(missing))}.</div>' if missing else "")
    objective = f'<div class="obj">{e(d["objective"])}</div>' if d.get("objective") else ""
    parts = []
    if d.get("acceptance_criteria"):
        parts.append("<h4>Criterios de aceptación</h4><ol>" + "".join(f"<li>{e(c)}</li>" for c in d["acceptance_criteria"]) + "</ol>")
    if d.get("verification"):
        by_command: dict[str, list[dict]] = {}
        for check in d["verification"]:
            by_command.setdefault(check["value"], []).append(check)
        rows = "".join(f'<li><code>{e(cmd)}</code><ul>' + "".join(
            f'<li>{e(c["purpose"] or "—")}{f" <span class=muted>· {e(c["category"])}</span>" if c.get("category") else ""}</li>'
            for c in checks) + "</ul></li>" for cmd, checks in by_command.items())
        parts.append(f"<h4>Verificación</h4><ul class=\"checks\">{rows}</ul>")
    if d.get("expected_paths"):
        parts.append("<h4>Archivos</h4><ul class=\"paths\">" + "".join(f"<li><code>{e(p)}</code></li>" for p in d["expected_paths"]) + "</ul>")
    facts = [f'repositorio <b>{e(str(d["repository"]))}</b>' if d.get("repository") else "",
             f'estimado <b>{e(str(d["estimated_minutes"]))} min</b>' if d.get("estimated_minutes") is not None else "",
             f'cubre <b>{e(", ".join(d["covers"]))}</b>' if d.get("covers") else "",
             f'recursos compartidos <b>{e(", ".join(d["shared_resources"]))}</b>' if d.get("shared_resources") else ""]
    facts = " · ".join(f for f in facts if f)
    if facts or d.get("estimate_rationale"):
        parts.append(f'<p class="meta">{facts}</p>' + (f'<p class="meta">{e(d["estimate_rationale"])}</p>' if d.get("estimate_rationale") else ""))
    body = f'<details class="tdet"><summary>Detalle de la tarea</summary>{"".join(parts)}</details>' if parts else ""
    return objective + warn + body


def _blocked_note(t: dict, asks: dict) -> str:
    """On a blocked task row: that it waits for the owner, the first line of the error and where to answer."""
    r = asks.get(t["id"])
    if t.get("state") != "blocked" and not (r and r.get("source") == "review"):
        return ""
    if not r:
        return '<div class="meta blocked"><b>Bloqueada.</b> El sistema no tiene aún una tarjeta para esta tarea.</div>'
    first = next((x for x in (r.get("error") or "").splitlines() if x.strip()), "")
    return (f'<div class="meta blocked"><b>Espera por ti:</b> {e(dx.headline(r) or r.get("needs") or r["what"])}'
            f'{f" <br>Error: <code>{e(first[:240])}</code>" if first else ""}'
            f' <a href="#d-{e(r["id"])}">Ver el origen y cómo solucionarlo</a></div>')


def _task(t: dict, asks: dict | None = None) -> str:
    chips = "".join(f'<span class="chip">tras {e(a)}</span>' for a in t["after"])
    assigned = attempts_.assigned_line(t.get("route"))
    current = f'<div class="meta">{assigned}</div>' if assigned else ""
    working = _working(t)
    return (f'<div class="task" id="t-{e(str(t["id"]))}" data-k="t-{e(str(t["id"]))}">'
            f'<span class="tid">{e(str(t["id"]))}</span>'
            f'<div><div class="tt">{e(t["title"] or "")}</div>{_detail(t)}'
            f'<div class="tl" style="margin-top:6px">{level_badge(t["complexity"]) or _unclassified(t)}'
            f'{_pill("bad", "sin detalle") if _missing_detail(t) else ""}'
            f'<span class="chip">{t["attempts"]} intentos</span>{chips}</div>{_amended(t)}{current}{working}{_blocked_note(t, asks or {})}'
            f'{attempts_.attempts_table(t["history"])}</div>{state_badge(t["state"])}</div>')


def _working(t: dict) -> str:
    cur = t["attempt"]
    if not cur or not cur.get("live"):
        return ""
    return (f'<div class="meta working"><i class="dot info live"></i> trabajando: '
            f'{attempts_.model_chip(cur.get("provider"), cur.get("model_requested"), cur.get("effort"))} · '
            f'{e(cur.get("account") or "—")} · <span data-v>{attempts_.fmt_duration(cur.get("duration_s"))}</span> · '
            f'<span data-v>{attempts_.tokens_html(cur.get("tokens"))}</span></div>')


def detail_page(s: dict, token: str, msg: str = "") -> str:
    project, req = s["project"], s["req_id"]
    base = _purl(project, req)
    body = (f'<div class="pl"><a class="back" href="/plans">← Planes</a> <span class="live-dot" id="live-dot"></span>{_flash(msg)}'
            f'<div id="live" data-api="/api/plans/{quote(project)}/{quote(req)}?html=1" '
            f'data-events="/events?plan={quote(project)}/{quote(req)}" data-event="plan">{detail_fragment(s)}</div>'
            f'{_decisions(s, base, token)}{_recovery(s, base, token)}{_healing(s, base, token)}{_run_form(s, base, token)}{_actions(s, base, token)}</div>{CSS}{JS}')
    return layout(f"{req} · Plan", body, [("Planes", "/plans"), (project, f"/p/{quote(project)}")])


RECOVERY_STATE_ES = {"diagnosing": "diagnosticando", "applying": "preparando correcciones", "executing": "ejecutando",
                     "auditing": "reauditando", "succeeded": "resuelto", "blocked": "bloqueado", "escalated": "te necesita",
                     "stopped": "detenido"}


def _recovery(s: dict, base: str, token: str) -> str:
    """Diagnostic recovery (REQ-029 R7): the durable cycles with their exact blocker, and the owner's stop / opt-in controls,
    both bound to the run's stop generation. Text comes from run files: all escaped."""
    r = s.get("recovery")
    if not r:
        return ""
    form = lambda action, label, extra="", cls="": (  # noqa: E731
        f'<form method="post" action="{base}/recovery" style="display:inline"><input type="hidden" name="token" value="{e(token)}">'
        f'<input type="hidden" name="action" value="{action}"><input type="hidden" name="stop_generation" '
        f'value="{e(str(r.get("stop_generation")))}">{extra}<button type="submit" class="{cls}">{label}</button></form>')
    cycles = []
    for c in r.get("cycles") or []:
        result = c.get("result") or {}
        state = "detenido" if r.get("held") and c.get("state") in ("diagnosing", "applying", "executing", "auditing") \
            else RECOVERY_STATE_ES.get(str(c.get("state")), str(c.get("state")))
        why = result.get("blocker") or ", ".join(result.get("blockers") or ())
        cycles.append(f'<li><span class="pill">{e(state)}</span> caso <code>{e(str(c.get("lineage_id"))[:12])}</code> · ciclo '
                      f'<code>{e(str(c.get("cycle_token"))[:12])}</code>{" · " + e(str(why)) if why else ""}</li>')
    enable = ""
    if not r.get("active") and r.get("preview_digest"):
        enable = form("enable", "Activar para este run", f'<input type="hidden" name="preview" value="{e(str(r["preview_digest"]))}">')
    stop = form("stop", "Detener recuperación", cls="danger") if r.get("active") else ""
    note = "" if r.get("active") else ('<p class="muted">Vista previa: abrir esta página no activa nada. Activarlo exige este botón, '
                                       'ligado a la vista previa de arriba y a la generación de stop actual.</p>')
    blocker = f'<p class="muted">{e(str(r["blocker"]))}</p>' if r.get("blocker") else ""
    return (f'<h2 id="recovery">Recuperación diagnóstica</h2><div class="ask"><p>{_pill("", "activa" if r.get("active") else "solo vista previa")} '
            f'{enable}{stop}</p>{note}{blocker}'
            f'{"<ul>" + "".join(cycles) + "</ul>" if cycles else "<p class=muted>Ningún ciclo todavía: se abre solo cuando los reintentos y remediaciones ordinarios se agotan.</p>"}</div>')


def _healing(s: dict, base: str, token: str) -> str:
    """Autocuración: what the scheduler fixed by itself, what it gave up on, and the owner's stop / revert (REQ-029 R7).
    Every text comes from run files, so everything is escaped."""
    h = s.get("healing")
    if not h:
        return ""
    on = bool(h.get("enabled"))
    limits = h.get("limits") or {}
    toggle = "stop" if on else "start"
    form = lambda action, label, extra="", cls="": (  # noqa: E731
        f'<form method="post" action="{base}/heal" style="display:inline"><input type="hidden" name="token" value="{e(token)}">'
        f'<input type="hidden" name="action" value="{action}">{extra}<button type="submit" class="{cls}">{label}</button></form>')
    cases = []
    for cid, c in sorted((h.get("cases") or {}).items(), key=lambda kv: str(kv[1].get("task"))):
        undo = form("revert", "Deshacer", f'<input type="hidden" name="case" value="{e(cid)}">') \
            if c.get("revision") and c.get("status") != "reverted" else ""
        cases.append(f'<li><b>{e(str(c.get("task")))}</b> · {e(str(c.get("class")))} · '
                     f'<span class="pill">{e(str(c.get("status")))}</span> {e(str(c.get("repair") or "sin reparación segura"))}'
                     f'{" · r" + e(str(c["revision"])) if c.get("revision") else ""} {undo}</li>')
    recent = []
    for r in h.get("recent") or []:
        recent.append(f'<li>{e(str(r.get("task") or "—"))} · {e(str(r.get("class")))} · '
                      f'{"automático" if r.get("source") == "auto" else "a mano"} · {e(str(r.get("repair") or ""))[:140]} · '
                      f'{e(str(r.get("result")))}'
                      f'{" · " + e(str(round(r["minutes_lost"]))) + " min" if r.get("minutes_lost") else ""}</li>')
    return (f'<h2 id="healing">Autocuración</h2><div class="ask"><p>{_pill("", "activa" if on else "detenida")} '
            f'{e(str(h.get("actions", 0)))}/{e(str(limits.get("actions", "—")))} acciones · '
            f'tope {e(str(limits.get("per_task", "—")))} cambios de plan por tarea {form(toggle, "Detener" if on else "Activar", cls="primary" if not on else "")}</p>'
            f'{"<ul>" + "".join(cases) + "</ul>" if cases else "<p class=muted>Sin casos todavía.</p>"}'
            f'{"<details><summary>Últimas intervenciones</summary><ul>" + "".join(recent) + "</ul></details>" if recent else ""}</div>')


def _confirm_form(base: str, action: str, token: str, req: str, label: str, warning: str) -> str:
    return (f'<form method="post" action="{base}/{action}" class="danger"><p>{warning}</p>'
            f'<input type="hidden" name="token" value="{e(token)}">'
            f'<input type="text" name="confirm" placeholder="Escribe {e(req)} para confirmar" autocomplete="off" required>'
            f'<p><button type="submit">{label}</button></p></form>')


def _decisions(s: dict, base: str, token: str) -> str:
    """Everything the plan waits on from its owner, answerable here: decision requests and open question rounds."""
    out = []
    project, req = s["project"], s["req_id"]
    for n in s.get("open_rounds") or []:
        out.append(f'<div class="ask"><b>Ronda {n} de preguntas abierta.</b> '
                   f'<a href="/p/{quote(project)}/req/{quote(req)}?tab=rounds">Responder</a></div>')
    for r in s.get("decisions") or []:
        flag = ' <span class="pill bad">nadie puede responder por ti</span>' if r.get("unskippable") else ""
        prefill = dx.note_for(r)
        opts = []
        for o in r.get("options") or []:
            star = " (recomendada)" if o["id"] == r.get("recommended") else ""
            needs = o["id"] in ("retry_with_note", "review_pass", "review_fail", "rework_findings")
            text = prefill if o["id"] == "retry_with_note" else ""
            note = (f'<textarea name="reason" required placeholder="Escribe tu indicación o razón">{e(text)}</textarea>'
                    if needs else "")
            cls = "primary" if o["id"] == r.get("recommended") else ""
            opts.append(f'<form method="post" action="{base}/decide" class="opt">'
                        f'<input type="hidden" name="token" value="{e(token)}">'
                        f'<input type="hidden" name="request" value="{e(r["id"])}">'
                        f'<input type="hidden" name="option" value="{e(o["id"])}">{note}'
                        f'<button type="submit" class="{cls}">{e(o["label"])}{star}</button>'
                        f'<p class="muted">{e(o["consequence"])}</p></form>')
        again = (r.get("agent") or {}).get("state") == "done"
        ask = (f'<form method="post" action="{base}/diagnose" style="display:inline">'
               f'<input type="hidden" name="token" value="{e(token)}"><input type="hidden" name="request" value="{e(r["id"])}">'
               f'<button type="submit" class="dx-ask">{"Pedir otra vez al agente" if again else "Pedir diagnóstico al agente"}</button></form>')
        first = [f for f, o in zip(opts, r.get("options") or []) if o["id"] == r.get("recommended")]
        rest = [f for f, o in zip(opts, r.get("options") or []) if o["id"] != r.get("recommended")]
        more = f'<details class="dx-more"><summary>Otras opciones ({len(rest)})</summary>{"".join(rest)}</details>' if rest else ""
        code = f' <span class="muted" style="font-weight:400;font-size:12px">· {e(r.get("reason", ""))}</span>' if r.get("reason") else ""
        out.append(f'<div class="ask" id="d-{e(r["id"])}"><h3>{e(r["title"].split(":")[0])}{code}{flag}</h3>{dx.html(r, ask)}'
                   f'{"".join(first)}{more}</div>')
    if not out:
        return ""
    waiting = any((r.get("agent") or {}).get("state") == "running" for r in s.get("decisions") or [])
    reload = ('<script>setTimeout(function(){var a=document.activeElement;'
              'if(!a||a.tagName!=="TEXTAREA")location.reload();},8000)</script>') if waiting else ""
    return f'<h2 id="asks">Esperando tu decisión</h2><div class="asks">{"".join(out)}</div>{reload}'


def _run_form(s: dict, base: str, token: str) -> str:
    act = s.get("run_action")
    if not act:
        return ""
    return (f'<form method="post" action="{base}/run" class="run-plan">'
            f'<input type="hidden" name="token" value="{e(token)}">'
            f'<input type="hidden" name="expected" value="{e(act["action"])}">'
            f'<button type="submit" class="primary">▶ {e(act["label"])}</button></form>')


def _actions(s: dict, base: str, token: str) -> str:
    req = s["req_id"]
    cancel = _confirm_form(base, "cancel", token, req, "Cancelar plan",
                           "<b>Cancelar es irreversible:</b> una tarea cancelada no se reabre nunca. "
                           "El plan no se puede editar; solo cancelar o borrar.")
    delete = _confirm_form(base, "delete", token, req, "Mover a la papelera",
                           "<b>Borrar</b> mueve PLAN.md, PLAN.json, plan-revisions, HANDOFF.md y RUN a la papelera "
                           "del proyecto (recuperable). Exige que la ejecución no esté activa.")
    return f'<h2>Acciones</h2>{cancel}{delete}'
