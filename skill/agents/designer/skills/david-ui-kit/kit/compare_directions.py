"""Rendered design DNA comparison. Offline; exit 2 means NOT RUN, never a pass.

UV_OFFLINE=1 uv run --offline --with playwright python compare_directions.py A.html B.html C.html --json
Each direction's .json note must name eight axes and selectors proving four measurable claims.
"""
from __future__ import annotations

import argparse
import itertools
import json
import shutil
import sys
from pathlib import Path

PROBE = r"""() => {
 const root=document.querySelector('#app')||document.querySelector('main')||document.body;
 const all=[root,...root.querySelectorAll('*')].filter(e=>{
   const r=e.getBoundingClientRect(),s=getComputedStyle(e);
   return !e.closest('[data-mockup-chrome],.mockup-bar')&&r.width>2&&r.height>2&&s.display!=='none'&&s.visibility!=='hidden';
 });
 const styles=all.map(e=>getComputedStyle(e));
 const fonts=[...new Set(styles.map(s=>s.fontFamily))].sort();
 const shape=all.map(e=>{const r=e.getBoundingClientRect();return [e.tagName, Math.round(r.x/innerWidth*12),
 Math.round(r.y/innerHeight*12),Math.round(r.width/innerWidth*12),Math.round(r.height/innerHeight*12)].join(':')});
 const nav=all.filter(e=>e.matches('nav,[role=navigation],[role=tablist]')).map(e=>{
 const r=e.getBoundingClientRect();return [Math.round(r.x/innerWidth*6),Math.round(r.y/innerHeight*6),
 Math.round(r.width/innerWidth*6),Math.round(r.height/innerHeight*6),getComputedStyle(e).flexDirection].join(':')});
 const animations=document.getAnimations().map(a=>({duration:a.effect?.getTiming().duration,
 easing:a.effect?.getTiming().easing,frames:a.effect?.getKeyframes().map(k=>Object.keys(k).sort().join(','))}));
 const rules=[];const walk=rs=>{for(const r of rs){if(r.type===CSSRule.KEYFRAMES_RULE)rules.push(r.cssText);
 if(r.cssRules&&r.type!==CSSRule.KEYFRAMES_RULE)walk(r.cssRules)}};
 for(const sheet of document.styleSheets){try{walk(sheet.cssRules)}catch{}}
 return {fonts,shape,nav,motion:[...rules,...animations.map(a=>JSON.stringify(a))],
 density:all.length, sizes:[...new Set(styles.map(s=>s.fontSize))].sort()};
}"""

# Motion that already ran or runs by script leaves no computed style behind: a Framer Motion marker that scaled in on
# mount, a toggle whose chevron child carries the transition (pictures REQ-021 SP-6: A's `.group-marker`, C's
# `.band-toggle`, both hidden from the owner as "not shown"). Record every element that moved while the page was measured.
MOTION_LOG = r"""(() => {
 const moved=window.__btMoved=new Set();const add=e=>{if(e instanceof Element)moved.add(e)};
 const animate=Element.prototype.animate;Element.prototype.animate=function(...a){add(this);return animate.apply(this,a)};
 for(const type of ['transitionrun','animationstart'])addEventListener(type,e=>add(e.target),true);
 new MutationObserver(rows=>rows.forEach(r=>add(r.target))).observe(document,{subtree:true,attributes:true,attributeFilter:['style']});
})()"""

EVIDENCE = r"""claims => {
 const declared=e=>{const s=getComputedStyle(e);return e.getAnimations().length>0||s.animationName!=='none'||
  s.transitionDuration.split(',').some(v=>parseFloat(v)>0)};
 const moved=[...(window.__btMoved||[])];
 const result={};for(const [axis,selectors] of Object.entries(claims)){
 result[axis]=selectors.map(selector=>{try{const els=[...document.querySelectorAll(selector)];
 const visible=els.filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0});
 const animated=visible.some(e=>declared(e)||[...e.querySelectorAll('*')].some(declared)||moved.some(m=>e.contains(m)));
 return {selector,ok:visible.length>0&&(axis!=='motion'||animated)};
 }catch{return {selector,ok:false}}});}return result;
}"""


def similarity(a: list, b: list) -> float:
    """Multiset overlap preserves repeated geometry (unlike a set of tag names)."""
    from collections import Counter
    x, y = Counter(a), Counter(b)
    union = sum((x | y).values())
    return sum((x & y).values()) / union if union else 1.0


def compare_dna(items: list[dict]) -> dict:
    pairs = []
    for a, b in itertools.combinations(items, 2):
        layout = similarity(a["shape"], b["shape"])
        type_same = a["fonts"] == b["fonts"] and similarity(a["sizes"], b["sizes"]) >= .85
        nav_same = a["nav"] == b["nav"]
        motion_same = similarity(a["motion"], b["motion"]) >= .8
        density_same = min(a["density"], b["density"]) >= .9 * max(a["density"], b["density"])
        # Directions share the product's tokens and fonts, so typography is reported but never counts: distinctness
        # comes from layout, navigation, density and motion. A colour/font swap on the same geometry always fails.
        collisions = int(nav_same) + int(motion_same) + int(layout >= .7) + int(density_same)
        ok = layout < .85 and collisions < 3
        pairs.append({"a": a["id"], "b": b["id"], "ok": ok, "layout_similarity": round(layout, 3),
                      "same_typography": type_same, "same_navigation": nav_same, "same_motion": motion_same,
                      "same_density": density_same})
    evidence_ok = all(all(x["ok"] for xs in i["evidence"].values() for x in xs) for i in items)
    missing = [f"{i['id']}: {x.get('selector', '?')}" for i in items for xs in i["evidence"].values() for x in xs if not x["ok"]]
    return {"schema_version": 1, "ok": evidence_ok and all(p["ok"] for p in pairs), "pairs": pairs,
            "evidence_ok": evidence_ok, "missing_evidence": missing[:12], "directions": items}


def measure(paths: list[Path]) -> dict:
    from playwright.sync_api import sync_playwright
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which("chromium"))
        try:
            for path in paths:
                note = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
                evidence = note.get("evidence", {})
                if any(not isinstance(evidence.get(k), list) or not evidence[k] for k in
                       ("layout", "navigation", "typography", "motion")):
                    raise ValueError(f"{path.name}: missing measurable axis claims")
                page = browser.new_page(viewport={"width": 1280, "height": 900}, reduced_motion="no-preference")
                page.add_init_script(MOTION_LOG)
                errors = []
                page.on("pageerror", lambda err, errors=errors: errors.append(str(err)))
                page.route("http://**/*", lambda route: route.abort())
                page.route("https://**/*", lambda route: route.abort())
                page.goto(path.resolve().as_uri())
                page.wait_for_timeout(150)
                dna = page.evaluate(PROBE)       # the first screen is what the layout/navigation/type measures read
                claims = page.evaluate(EVIDENCE, evidence)
                # A claim may live on another screen (a dock that only shows in the app views): it holds when it is
                # visible in ANY view, so walk the view select and keep the best result per selector.
                views = page.eval_on_selector("#view", "s => [...s.options].filter(o => !o.disabled).map(o => o.value)") \
                    if page.query_selector("#view") else []
                for view in views:
                    page.select_option("#view", view)
                    page.wait_for_timeout(60)
                    more = page.evaluate(EVIDENCE, evidence)
                    for axis, rows in more.items():
                        for old_row, new_row in zip(claims[axis], rows):
                            old_row["ok"] = old_row["ok"] or new_row["ok"]
                if errors or dna["density"] < 3:
                    raise ValueError(f"{path.name}: mockup crashed or rendered nothing: {errors[:1]}")
                dna.update(id=path.name, evidence=claims)
                items.append(dna)
                page.close()
        finally:
            browser.close()
    return compare_dna(items)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        result = measure(args.paths)
        code = 0 if result["ok"] else 1
    except Exception as exc:  # noqa: BLE001 - browser/tool failures become explicit NOT RUN, never success
        result, code = {"ok": False, "error": f"COMPARE NOT RUN: {exc}"}, 2
    print(json.dumps(result, ensure_ascii=False) if args.json else
          ("RESULT: PASS" if result["ok"] else "RESULT: FAIL") + "\n" + json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
