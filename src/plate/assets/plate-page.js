// Plate page runtime: draws one figure on a physical-size artboard, then runs the print checks.
// Reuses the SubScout chart components from the built site's runtime/ folder.
import { theme, units, UNITS, refreshUnits } from "../../runtime/js/subscout.js";
import { lineChart, stackedBars, bubbles, heatmap, divergingBars, barChart, dotStrip, geoMap, networkChart } from "../../runtime/js/charts.js";

const P = JSON.parse(document.getElementById("pl-payload").textContent);
const q = new URLSearchParams(location.search);
const cfg = P.plate;
theme.set(q.get("theme") || "light");
units.set(q.get("units") || P.units || "sm3");
refreshUnits();

const board = document.getElementById("board");
const el = document.getElementById("pl-chart");
const legendEl = document.getElementById("pl-legend");
board.dataset.density = cfg.density;
board.dataset.legend = cfg.legend;
board.style.width = `${cfg.w}px`;
board.style.height = `${cfg.h}px`;
board.style.transform = `scale(${cfg.zoom})`;
document.documentElement.style.setProperty("--pl-zoom", cfg.zoom);

// Legend slot: top (under the title), rail (right-hand column), bottom (above the footer).
const slot = board.querySelector(`.pl-slot-${cfg.legend}`) || board.querySelector(".pl-slot-top");
slot.appendChild(legendEl);

const spec = P.fig.spec;
const U = () => UNITS[units.get()];
const o = {
  label: spec.title?.replace(/<[^>]+>/g, "") ?? "", legendEl, spec, groups: spec.groups || P.groups,
  unitLabel: () => (spec.unit_label ? spec.unit_label.replace("{unit}", U().short) : ""),
  height: () => el.clientHeight, export: true, print: true,
  pixelRatio: (window.devicePixelRatio || 1) * cfg.zoom,  // device pixels per layout pixel, for canvas figures
};

async function makeChart() {
  const data = P.fig.data;
  switch (spec.type) {
    case "line": return lineChart(el, data, { ...o, yFormat: spec.y_format, unitScaled: !!spec.volume });
    case "stack": return stackedBars(el, data, { ...o, colours: spec.colours, unitScaled: !!spec.volume });
    case "bubble": return bubbles(el, data, spec.groups || [], o);
    case "heat": return heatmap(el, data, { ...o, valueLabel: spec.value_label ?? "" });
    case "diverging": return divergingBars(el, data, o);
    case "bars": return barChart(el, data, o);
    case "dots": return dotStrip(el, data, o);
    case "map": return geoMap(el, spec, P.datasets, o);
    case "network": return networkChart(el, data, o);
    case "custom": {
      const names = [].concat(spec.data ?? []);
      const ds = Object.fromEntries(names.map((n) => [n, P.datasets[n]]));
      const m = await import(new URL(`../../${spec.module}`, location.href).href);
      return (m.default ?? m.create)(el, ds, { ...o, units: U, states: P.states.map((s) => s.state) });
    }
    default: return null;
  }
}

// ---- print checks: reported to the renderer, never silently ignored
function qa() {
  const issues = [];
  const z = cfg.zoom, b = board.getBoundingClientRect();
  const minPt = cfg.min_pt;
  const seen = new Set();
  for (const t of board.querySelectorAll("*")) {
    const own = [...t.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!own) continue;
    const cs = getComputedStyle(t);
    if (cs.display === "none" || cs.visibility === "hidden") continue;
    const pt = parseFloat(cs.fontSize) * z * 0.75;
    if (pt < minPt) {
      const key = `${t.tagName}:${Math.round(pt * 10)}`;
      if (!seen.has(key)) { seen.add(key); issues.push({ kind: "small-text", pt: +pt.toFixed(1), text: t.textContent.trim().slice(0, 40) }); }
    }
    const r = t.getBoundingClientRect();
    if (r.width && (r.right > b.right + 1 || r.left < b.left - 1 || r.bottom > b.bottom + 1 || r.top < b.top - 1))
      issues.push({ kind: "outside-board", text: t.textContent.trim().slice(0, 40) });
  }
  if (board.scrollHeight > board.clientHeight + 1) issues.push({ kind: "content-overflow", by_px: board.scrollHeight - board.clientHeight });
  for (const need of ["Source", "Confidence"]) {
    if (![...board.querySelectorAll(".pl-foot b")].some((x) => x.textContent === need)) issues.push({ kind: "missing-fact", fact: need });
  }
  return issues;
}

(async () => {
  const st = P.states[Math.min(P.states.length - 1, Math.max(0, +(q.get("state") ?? P.states.length - 1)))];
  if (st.state.title) document.getElementById("pl-title").innerHTML = st.state.title;
  const chart = await makeChart();
  chart?.draw(el.clientWidth, st.state, { animate: false });
  await document.fonts.ready;
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 200))));
  window.__plateQA = qa();
  document.body.dataset.ready = "1";
})();
