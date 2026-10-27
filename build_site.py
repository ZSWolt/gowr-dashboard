#!/usr/bin/env python3
"""Build the GOWR dashboard as a static site for GitHub Pages.

page.html  - the dashboard page (the same markup the claude.ai dashboard ran)
data/*.json - copied from ~/gow/scratch/dash (written by ~/gow/dash_build.py)
index.html - generated: page.html wrapped with the theme and a small `dash` shim
"""
import json
import os
import shutil
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.expanduser("~/gow/scratch/dash")
DATASETS = ["badframes", "branches", "coverage", "daily", "fixes", "frames", "functions",
            "graphics", "hypotheses", "liverun", "map", "process", "runs", "schedule",
            "status", "tokens", "usage", "usage_history"]

HEAD = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GOWR on AnyPS5</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600&family=Frank+Ruhl+Libre:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
:root {
  --font-anthropic-sans: "Heebo", system-ui, sans-serif;
  --font-anthropic-serif: "Frank Ruhl Libre", Georgia, serif;
  --color-bg: #faf9f5; --color-panel: #ffffff; --color-fg: #1f1e1d; --color-fg-muted: #6b6a66;
  --color-border-line: #e5e3dc; --color-ok: #2f7d4f; --color-warn: #b7791f; --color-bad: #c0392b;
  --cds-text-secondary: var(--color-fg-muted); --cds-border: var(--color-border-line);
  --cds-surface-popover: var(--color-panel); --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.12);
  --cds-chart-grid: #ecebe6; --cds-chart-axis: #8a8984; --cds-chart-muted: #c9c7bf;
  --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 12px; --cds-gap-lg: 20px;
  --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 16px;
  --cds-radius: 10px; --cds-dur-slow: 400ms;
  --cds-font-size-caption: 12px; --cds-font-size-body: 14px; --cds-font-size-heading: 16px; --cds-font-size-title: 26px;
  --cds-font-weight-medium: 500;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #1f1e1d; --color-panel: #2a2927; --color-fg: #f0eee6; --color-fg-muted: #a3a19a;
    --color-border-line: #3a3936; --color-ok: #5fb37f; --color-warn: #e0a64a; --color-bad: #e5675a;
    --cds-chart-grid: #34332f; --cds-chart-axis: #8a8984; --cds-chart-muted: #55534e;
    --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.5);
  }
}
html, body { margin: 0; background: var(--color-bg); color: var(--color-fg); }
#dash-root { max-width: 1200px; margin: 0 auto; padding: 24px 16px 48px; box-sizing: border-box; }
#dash-built { max-width: 1200px; margin: 0 auto; padding: 0 16px 24px; font: 12px var(--font-anthropic-sans); color: var(--color-fg-muted); }
</style>
<script>
/* Minimal stand-in for the claude.ai dashboard runtime: loads data/<id>.json. */
(function () {
  var store = {}, calcs = {}, handlers = [], pending = {};
  function rowsOf(v) {
    if (Array.isArray(v)) return v;
    if (v && typeof v === "object") for (var k of ["rows", "data", "results"]) if (Array.isArray(v[k])) return v[k];
    return v;
  }
  function columnsOf(rows) {
    var cols = [];
    if (Array.isArray(rows)) rows.forEach(function (r) {
      if (r && typeof r === "object") Object.keys(r).forEach(function (k) { if (cols.indexOf(k) < 0) cols.push(k); });
    });
    return cols;
  }
  function result(status, data, message) {
    var d = status === "ok" ? data : [];
    return { status: status, data: d, rows: Array.isArray(d) ? d : [], value: d,
             columns: columnsOf(d), message: message || "", refreshing: false, meta: [] };
  }
  function fire() { handlers.forEach(function (fn) { try { fn(); } catch (e) { console.error(e); } }); }
  function load(id) {
    if (pending[id]) return;
    pending[id] = true;
    fetch("data/" + encodeURIComponent(id) + ".json", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status === 404 ? "missing" : "HTTP " + r.status); return r.json(); })
      .then(function (j) { store[id] = result("ok", rowsOf(j)); })
      .catch(function (e) { store[id] = result(String(e.message) === "missing" ? "missing" : "error", null, String(e.message)); })
      .then(fire);
  }
  var dash = {
    colors: ["#2f6bdf", "#d97757", "#2f7d4f", "#b7791f", "#8e5bd0", "#c0392b", "#1f9aa8", "#7a7a72"],
    data: function (id) {
      if (calcs[id]) {
        var c = calcs[id], args = [];
        for (var i = 0; i < c.inputs.length; i++) {
          var d = dash.data(c.inputs[i]);
          if (d.status !== "ok") return result(d.status === "error" ? "error" : "loading");
          args.push(d.data);
        }
        try { return result("ok", c.fn.apply(null, args)); } catch (e) { return result("error", null, String(e)); }
      }
      if (!store[id]) { load(id); return result("loading"); }
      return store[id];
    },
    onData: function (fn) { handlers.push(fn); try { fn(); } catch (e) { console.error(e); } },
    calc: function (id, spec) { calcs[id] = { inputs: spec.inputs || [], fn: spec.fn }; },
    loader: function () {}, refresh: function () {},
    params: function () { return {}; }, setParams: function () {}, resetParams: function () {}, setLink: function () {}
  };
  window.dash = dash;
  var w = window.innerWidth;
  window.addEventListener("resize", function () { if (Math.abs(window.innerWidth - w) > 20) { w = window.innerWidth; fire(); } });
})();
</script>
</head>
<body>
<div id="dash-root">
"""

TAIL = """
</div>
<div id="dash-built">BUILT_LABEL</div>
</body>
</html>
"""


def main():
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    copied, missing = [], []
    for name in DATASETS:
        src = os.path.join(DASH, name + ".json")
        if os.path.exists(src):
            with open(src) as f:
                json.load(f)  # refuse to publish a broken file
            shutil.copyfile(src, os.path.join(HERE, "data", name + ".json"))
            copied.append(name)
        else:
            missing.append(name)
    with open(os.path.join(HERE, "page.html"), encoding="utf-8") as f:
        page = f.read()
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(HEAD + page + TAIL.replace("BUILT_LABEL", "עודכן: " + stamp))
    print(f"built index.html; data: {len(copied)} files" + (f"; not found locally: {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
