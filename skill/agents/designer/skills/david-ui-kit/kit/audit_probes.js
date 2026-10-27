// Probes that audit_mockup.py injects into a rendered mockup: window.__audit.measure() reads one view/state/scene/theme,
// window.__audit.focus() judges the element the last Tab focused. Colours go through a canvas, so any CSS colour syntax
// (rgb, oklch, color-mix, color(srgb …)) is measured; a text colour that still cannot be read is reported, never skipped.
(() => {
  const cvs = document.createElement('canvas');
  cvs.width = cvs.height = 1;
  const cx = cvs.getContext('2d', { willReadFrequently: true });
  const cache = new Map();
  const parse = c => {
    if (!c || c === 'none' || c === 'transparent') return c === 'transparent' ? { r: 0, g: 0, b: 0, a: 0 } : null;
    if (cache.has(c)) return cache.get(c);
    let out = null;
    const m = c.match(/^rgba?\(([^)]+)\)$/);
    if (m) {
      const p = m[1].split(/[ ,/]+/).filter(Boolean).map(v => v.endsWith('%') ? parseFloat(v) / 100 : parseFloat(v));
      out = { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
    } else {
      cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#010203'; cx.fillStyle = c;
      if (cx.fillStyle !== '#010203') { cx.fillRect(0, 0, 1, 1); const d = cx.getImageData(0, 0, 1, 1).data; out = { r: d[0], g: d[1], b: d[2], a: d[3] / 255 }; }
    }
    cache.set(c, out);
    return out;
  };
  const over = (t, b) => ({ r: t.r * t.a + b.r * (1 - t.a), g: t.g * t.a + b.g * (1 - t.a), b: t.b * t.a + b.b * (1 - t.a), a: 1 });
  const lum = c => { const f = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const r2 = n => Math.round(n * 100) / 100;
  const WHITE = { r: 255, g: 255, b: 255, a: 1 };
  const label = el => {
    const c = (typeof el.className === 'string' && el.className.trim()) ? '.' + el.className.trim().split(/\s+/)[0] : '';
    const t = (el.textContent || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 40);
    return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + c + (t ? ' «' + t + '»' : '');
  };
  const bgOf = el => {
    const chain = [];
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') return null;
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) { chain.push(c); if (c.a >= 1) break; }
    }
    let base = WHITE;
    for (let i = chain.length - 1; i >= 0; i--) base = over(chain[i], base);
    return base;
  };

  // the planning chrome: the highest block that holds every planning select and nothing that looks like the product,
  // plus the short «mock data» notices next to it at the top level (what the plan page's preview crops away)
  const CONTENT = 'main, #app, [role=main], h1, h2, h3, form, table, article, section, dialog';
  function chromeParts() {
    const plan = ['view', 'state', 'scene', 'theme'].map(id => document.getElementById(id)).filter(s => s && s.tagName === 'SELECT');
    let chrome = null;
    for (let n = plan[0] && plan[0].parentElement; n && n !== document.body; n = n.parentElement) {
      if (!plan.every(s => n.contains(s))) continue;
      if (n.matches(CONTENT) || n.querySelector(CONTENT)) break;
      const tops = [...n.querySelectorAll('select, label')].filter(e => !e.parentElement.closest('select, label') || !n.contains(e.parentElement.closest('select, label')));
      const own = (n.textContent || '').length - tops.reduce((k, e) => k + (e.textContent || '').length, 0);
      if (own > 300) break;
      chrome = n;
    }
    const notes = [...document.body.children].filter(n => n !== chrome && !n.matches('main, #app, [role=main], footer') && !n.querySelector('main, #app, [role=main]') &&
      (n.textContent || '').trim().length < 400 && /ficticio|mockup|maqueta|simulan|planificaci|fictitious|mock data/i.test(n.textContent || ''));
    return el => (chrome && chrome.contains(el)) || notes.some(n => n.contains(el));
  }

  function measure() {
    const W = innerWidth;
    const inChrome = chromeParts();
    const opacityOf = el => { let o = 1; for (let n = el; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity); return o; };
    const disabled = el => !!el.closest('[disabled], [aria-disabled="true"], [data-disabled], fieldset:disabled') || el.matches(':disabled');
    const visible = el => { const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return false; const s = getComputedStyle(el); return s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.05; };
    const fixedLayer = el => { for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const p = getComputedStyle(n).position; if (p === 'fixed' || p === 'sticky') return n; } return null; };
    const scrolled = el => { for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) { const o = getComputedStyle(n).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden') return true; } return false; };
    const textRect = el => {
      let box = null;
      for (const n of el.childNodes) {
        if (n.nodeType !== 3 || !n.textContent.trim()) continue;
        const rg = document.createRange(); rg.selectNodeContents(n);
        for (const q of rg.getClientRects()) {
          if (q.width < 1) continue;
          box = box ? { left: Math.min(box.left, q.left), right: Math.max(box.right, q.right), top: Math.min(box.top, q.top), bottom: Math.max(box.bottom, q.bottom) } : { left: q.left, right: q.right, top: q.top, bottom: q.bottom };
        }
      }
      return box;
    };
    const out = { contrast: [], nontext: [], alignment: [], padding: [], overflow: [], unmeasured: [], native: [], unknown: 0, texts: 0,
      hasMain: !!document.querySelector('main, #app, [role=main]') };
    const SKIP = ['SCRIPT', 'STYLE', 'TEMPLATE', 'svg', 'path', 'line', 'rect', 'circle', 'polyline', 'g'];
    // an open modal makes the page behind it inert: measure the modal (and its ancestors), not what the overlay covers
    const modal = [...document.querySelectorAll('[role=dialog][aria-modal=true], [role=alertdialog], dialog[open]')].filter(visible).pop();
    const all = [...document.body.querySelectorAll('*')].filter(el => !inChrome(el) && !SKIP.includes(el.tagName) &&
      (!modal || modal.contains(el) || el.contains(modal)));
    // text fading out (an exiting toast or dialog) is not what the screen settles on: skip what is nearly transparent
    const faded = el => { let o = 1; for (let n = el; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity); return o < 0.2; };
    const vis = all.filter(el => visible(el) && !faded(el));

    // text contrast (placeholders and SVG text included)
    for (const el of vis) {
      const isField = ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) && !['checkbox', 'radio', 'hidden', 'range', 'color'].includes(el.type);
      const svgText = el.tagName === 'text';
      if (!(isField || textRect(el)) || disabled(el)) continue;
      const cs = getComputedStyle(el);
      const bg = bgOf(svgText ? el.closest('svg').parentElement : el);
      if (!bg) { out.unknown++; continue; }
      const check = (fgc, what) => {
        let fg = parse(fgc);
        if (!fg) { out.unmeasured.push({ el: label(el) + what, detail: `colour «${fgc}» could not be read` }); return; }
        const o = opacityOf(el); if (o < 0.99) fg = { ...fg, a: fg.a * o };
        const r = ratio(over(fg, bg), bg), size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
        const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;
        out.texts++;
        if (r < need) out.contrast.push({ el: label(el) + what, ratio: r2(r), need });
      };
      if (isField) {
        if (el.value || el.tagName === 'SELECT') check(cs.color, '');
        else if (el.placeholder) check(getComputedStyle(el, '::placeholder').color, ' (placeholder)');
      } else check(svgText ? cs.fill : cs.color, '');
    }

    // shadcn/ui parts drawn as shapes, not text boxes (real-library mockups mark them with data-slot)
    const SLOTS = '[data-slot=separator], [data-slot=skeleton], [data-slot=progress], [data-slot=progress-indicator], [data-slot=avatar], [data-slot=switch], [data-slot=checkbox], [data-slot=radio-group-item], [data-slot=slider]';
    // non-text: a form control needs an edge or a fill of 3:1 against what surrounds it
    const CONTROL = 'input:not([type=hidden]):not([type=range]):not([type=color]), select, textarea, [role=combobox], .select-trigger, [data-slot=select-trigger], [role=switch]';
    for (const el of vis) {
      if (!el.matches(CONTROL) || disabled(el)) continue;
      const cs = getComputedStyle(el), outer = bgOf(el.parentElement);
      if (!outer) continue;
      if ((el.type === 'checkbox' || el.type === 'radio') && cs.appearance !== 'none') { out.native.push({ el: label(el) }); continue; }
      const grp = el.closest('.input-group, [data-slot=input-group]');
      const host = grp && el.tagName === 'INPUT' && (parseFloat(cs.borderTopWidth) === 0 || parse(cs.borderTopColor)?.a === 0) ? grp : el;
      const hs = getComputedStyle(host), hostOuter = bgOf(host.parentElement) || outer;
      const fill = parse(hs.backgroundColor), fillR = fill && fill.a > 0 ? ratio(over(fill, hostOuter), hostOuter) : 1;
      const bc = parse(hs.borderTopColor);
      const edgeR = parseFloat(hs.borderTopWidth) >= 1 && hs.borderTopStyle !== 'none' && bc ? ratio(over(bc, hostOuter), hostOuter) : 1;
      if (Math.max(fillR, edgeR) < 3) out.nontext.push({ el: label(el), ratio: r2(Math.max(fillR, edgeR)) });
    }

    // alignment
    const onScreen = el => { const r = el.getBoundingClientRect(); return r.bottom > 0 && r.right > 0 && r.left < W; };
    const blocks = vis.filter(el => textRect(el) && onScreen(el) && !fixedLayer(el) &&
      !el.closest('header, nav, [role=banner], [role=navigation], aside, .sidebar, .app-header, .toaster, table, svg'));
    const framed = el => {                               // a fill or a border you can see
      const s = getComputedStyle(el), p = el.parentElement ? bgOf(el.parentElement) : null, b = parse(s.backgroundColor);
      const ownFill = b && b.a > 0.5 && p && ratio(over(b, p), p) > 1.1;
      const sides = p && ['Left', 'Right'].every(k => { const c = parse(s['border' + k + 'Color']);
        return parseFloat(s['border' + k + 'Width']) >= 1 && s['border' + k + 'Style'] !== 'none' && c && c.a > 0.1 && ratio(over(c, p), p) > 1.1; });
      return !!(ownFill || sides);
    };
    const interactive = el => el.closest('button, a, input, select, textarea, label, [role=button], .badge, .button');
    const frameOf = el => { for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) if (framed(n) || n.matches('form, [role=dialog], [role=alertdialog], main, section')) return n; return document.body; };
    const contentBox = n => { const r = n.getBoundingClientRect(), s = getComputedStyle(n);
      return { l: r.left + parseFloat(s.paddingLeft) + parseFloat(s.borderLeftWidth), r: r.right - parseFloat(s.paddingRight) - parseFloat(s.borderRightWidth) }; };
    const blockOf = (el, stop) => { let n = el; while (n && n !== stop && /^inline|^contents/.test(getComputedStyle(n).display) && n.parentElement) n = n.parentElement; return n; };
    const columns = vis.filter(el => { if (fixedLayer(el)) return false; const r = el.getBoundingClientRect();
      return r.width >= 240 && r.width <= W * 0.7 && Math.abs((r.left + r.right) / 2 - W / 2) <= 4 && el.querySelector('input, button, h1, h2, h3, p'); });
    const column = columns.sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
    if (column) {
      const c = column.getBoundingClientRect();
      for (const el of blocks) {
        if (column.contains(el) || el.contains(column)) continue;
        const t = textRect(el), mid = (t.left + t.right) / 2;
        if (Math.abs(t.left - c.left) > 8 && Math.abs(mid - (c.left + c.right) / 2) > 16)
          out.alignment.push({ el: label(el), detail: `centred column x ${Math.round(c.left)}–${Math.round(c.right)}, this text starts at x ${Math.round(t.left)}` });
      }
    }
    const groups = new Map();
    for (const el of blocks) {
      const btn = interactive(el);
      if (btn && (framed(btn) || btn.matches('input, select, textarea, .badge, [data-slot=badge]'))) continue;
      const f = frameOf(el);
      if (!groups.has(f)) groups.set(f, []);
      groups.get(f).push(el);
    }
    for (const [f, els] of groups) {
      const fb = contentBox(f);
      const kind = el => {                               // judged against the line's own block: an inline link counts too
        const t = textRect(el), mid = (t.left + t.right) / 2, b = contentBox(blockOf(el, f));
        if (t.left - fb.l > 12 && Math.abs(mid - (b.l + b.r) / 2) <= 6 && (b.r - b.l) - (t.right - t.left) > 24) return 'center';
        if (t.left - fb.l <= 6) return 'left';
        if (Math.abs(t.right - fb.r) <= 6 && t.left - fb.l > 24) return 'right';
        return 'other';
      };
      const kinds = els.map(kind), lefts = kinds.filter(k => k === 'left').length;
      els.forEach((el, i) => {
        if (kinds[i] !== 'center' || lefts < 2) return;
        const blk = blockOf(el, f);
        let wrap = blk; while (wrap.parentElement && wrap.parentElement !== f && wrap.parentElement.getBoundingClientRect().width <= blk.getBoundingClientRect().width + 1) wrap = wrap.parentElement;
        const sibs = els.filter((o, j) => j !== i && kinds[j] === 'center' && (wrap.parentElement || f).contains(o) && blockOf(o, f) !== blk &&
          Math.abs(o.getBoundingClientRect().top - el.getBoundingClientRect().bottom) < 48);
        if (!sibs.length) out.alignment.push({ el: label(el), detail: `one centred line among ${lefts} left-aligned lines of ${label(f).slice(0, 40)}` });
      });
      els.forEach((el, i) => {                            // a lone right-aligned line, not a label/value row
        if (kinds[i] !== 'right' || lefts < 2) return;
        const t = textRect(el), alone = !els.some((o, j) => { if (j === i) return false; const u = textRect(o); return u.top < t.bottom - 2 && u.bottom > t.top + 2; });
        if (alone) out.alignment.push({ el: label(el), detail: `one right-aligned line alone among ${lefts} left-aligned lines of ${label(f).slice(0, 40)}` });
      });
    }

    // padding: content of a framed box keeps off its edges; on a phone text keeps off the screen edge; field text off its edge
    for (const el of vis) {
      if (el.matches('html, body, main, #app, table, thead, tbody, tr, td, th, svg, hr, .separator, .skeleton, .progress, .progress-indicator, .avatar, .switch, .checkbox, .radio, img, iframe, canvas, ' + SLOTS)) continue;
      const s = getComputedStyle(el);
      if (el.matches('input:not([type=checkbox]):not([type=radio]), select, textarea')) {
        if (!el.matches('[type=color], [type=range], [type=file], [type=image]') && (el.value || el.placeholder || el.tagName === 'SELECT') && framed(el) && parseFloat(s.paddingLeft) + parseFloat(s.textIndent || 0) < 6)
          out.padding.push({ el: label(el), detail: `field text ${Math.round(parseFloat(s.paddingLeft))} px from its edge (needs 6)` });
        continue;
      }
      if (!framed(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 40 || r.height < 18 || r.width > W * 0.98) continue;
      if (s.overflowX !== 'visible' && el.scrollWidth > el.clientWidth + 1) continue;
      let box = null;
      const add = q => { if (q.right - q.left < 1 || q.bottom - q.top < 1) return; box = box ? { l: Math.min(box.l, q.left), r: Math.max(box.r, q.right), t: Math.min(box.t, q.top), b: Math.max(box.b, q.bottom) } : { l: q.left, r: q.right, t: q.top, b: q.bottom }; };
      const t0 = textRect(el); if (t0) add(t0);
      let clipped = false;                               // a horizontally scrolled table: its sides are judged by scrolling, not here
      const clip = (d, q) => {                          // what a scroll container hides is not on the frame's edge
        for (let n = d.parentElement; n && n !== el; n = n.parentElement) {
          const ns = getComputedStyle(n);
          if (ns.overflowX !== 'visible' && n.scrollWidth > n.clientWidth + 1) { clipped = true; const c = n.getBoundingClientRect(); q = { left: Math.max(q.left, c.left), right: Math.min(q.right, c.right), top: q.top, bottom: q.bottom }; }
        }
        return q;
      };
      const add0 = add;
      const addFor = (d, q) => add0(clip(d, q));
      for (const d of el.querySelectorAll('*')) {
        if (!visible(d) || fixedLayer(d) !== fixedLayer(el) || getComputedStyle(d).position === 'absolute') continue;
        const tr = textRect(d); if (tr) addFor(d, tr);
        // nested frames (a highlighted menu item, an input inside an input group) count by their text, not their box
        if (d.matches('input:not([type=checkbox]):not([type=radio]), select, textarea')) {
          const q = d.getBoundingClientRect(), ds = getComputedStyle(d);
          if (framed(d)) addFor(d, q); else addFor(d, { left: q.left + parseFloat(ds.paddingLeft), right: q.right - parseFloat(ds.paddingRight), top: q.top + q.height / 4, bottom: q.bottom - q.height / 4 });
        } else if (d.matches('img, .avatar, .badge, .switch, .checkbox, .radio, .skeleton, .progress, [data-slot=badge], ' + SLOTS)) addFor(d, d.getBoundingClientRect());
      }
      if (!box) continue;
      const gl = box.l - r.left - parseFloat(s.borderLeftWidth), gr = r.right - parseFloat(s.borderRightWidth) - box.r;
      const gt = box.t - r.top - parseFloat(s.borderTopWidth), gb = r.bottom - parseFloat(s.borderBottomWidth) - box.b;
      const small = r.height <= 28, control = r.height <= 48 && !small;
      const needX = small ? 6 : control ? 8 : 12, needY = small || control ? 0 : 8;
      if (!t0 && el.matches('button, .button, a') && Math.abs(gl - gr) <= 2) continue;          // icon-only button: centred glyph
      if ((!clipped && Math.min(gl, gr) < needX - 0.5) || Math.min(gt, gb) < needY - 0.5)
        out.padding.push({ el: label(el), detail: `content ${Math.round(Math.min(gl, gr))} px from the side, ${Math.round(Math.min(gt, gb))} px from top/bottom (needs ${needX}/${needY})` });
    }
    if (W <= 480) {
      for (const el of vis) {
        const t = textRect(el);
        if (!t || !onScreen(el) || fixedLayer(el) || scrolled(el)) continue;
        if (t.left < 12 || t.right > W - 12) out.padding.push({ el: label(el), detail: `text ${Math.round(Math.min(t.left, W - t.right))} px from the screen edge (needs 12)` });
      }
    }

    // overflow
    const sw = document.documentElement.scrollWidth - innerWidth;
    if (sw > 1) {
      const wide = all.filter(el => { const r = el.getBoundingClientRect(); if (r.right <= W + 1 || r.width < 2) return false; return !scrolled(el); });
      out.overflow.push({ px: sw, el: wide.slice(0, 3).map(label).join(', ') });
    }
    return out;
  }

  // transitions (a border easing to the ring colour) would be read mid-way: jump every finite animation to its end
  const settle = () => { for (const a of document.getAnimations()) { try { if (a.effect && a.effect.getComputedTiming().iterations !== Infinity) a.finish(); } catch (e) { /* not finishable */ } } };

  // focus: compare the focused element (and a :focus-within wrapper) with itself unfocused; only what changes counts
  function focus() {
    const el = document.activeElement;
    if (!el || el === document.body || el === document.documentElement) return null;
    if (chromeParts()(el)) return { skip: true };
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return { skip: true };
    const hosts = [el, el.parentElement, el.parentElement && el.parentElement.parentElement].filter(h => h && h !== document.body);
    const snap = () => hosts.map(h => { const s = getComputedStyle(h);
      return { ol: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) >= 1 ? s.outlineColor + ' ' + s.outlineWidth : '', olc: s.outlineColor,
               sh: s.boxShadow, bc: parseFloat(s.borderTopWidth) >= 1 && s.borderTopStyle !== 'none' ? s.borderTopColor : '', bg: s.backgroundColor }; });
    settle();
    const on = snap();
    el.blur(); settle();
    const off = snap();
    el.focus({ preventScroll: true }); settle();
    let best = 0, changed = false;
    hosts.forEach((h, i) => {
      const a = on[i], b = off[i], outer = bgOf(h.parentElement || h) || WHITE;
      const vs = c => { const x = parse(c); return x ? ratio(over(x, outer), outer) : 0; };
      if (a.ol && a.ol !== b.ol) { changed = true; best = Math.max(best, vs(a.olc)); }
      if (a.sh !== b.sh && a.sh !== 'none') { changed = true; for (const m of a.sh.matchAll(/(?:rgba?|hsla?|oklch|oklab|lab|lch|color)\([^)]*\)/g)) best = Math.max(best, vs(m[0])); }
      if (a.bc && a.bc !== b.bc) { changed = true; best = Math.max(best, vs(a.bc)); }
      if (a.bg !== b.bg) { changed = true; const c1 = parse(a.bg), c0 = parse(b.bg); if (c1 && c0) best = Math.max(best, ratio(over(c1, outer), over(c0, outer))); }
    });
    return { el: label(el), key: label(el), ratio: r2(best), changed };
  }

  window.__audit = { measure, focus };
})();
