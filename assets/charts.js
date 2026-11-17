/* Hand-rolled SVG charts.
 *
 * No charting library: the site has to work offline once installed, and a
 * library loaded from a CDN would be the one thing that could not be cached
 * reliably. Every chart here draws from the history file in the browser.
 *
 * Shared conventions, applied to every chart:
 *   - thin marks with 4px rounded ends anchored to the baseline
 *   - a 2px surface gap between adjacent bars
 *   - recessive gridlines and axes, text in ink colors rather than series colors
 *   - a hover tooltip on every mark
 *   - a table view under each chart, so nothing is color-alone
 */

const SVG_NS = "http://www.w3.org/2000/svg";

const el = (name, attrs = {}) => {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== null && value !== undefined) {
      node.setAttribute(key, String(value));
    }
  }
  return node;
};

/* ---- tooltip --------------------------------------------------------- */

let tip;

function tooltip() {
  if (!tip) {
    tip = document.createElement("div");
    tip.className = "tooltip";
    tip.setAttribute("role", "status");
    document.body.append(tip);
  }
  return tip;
}

/** Give a mark a hover tooltip with a generous hit target. */
function hoverable(node, html) {
  node.addEventListener("pointerenter", (event) => {
    const box = tooltip();
    box.innerHTML = html;
    box.classList.add("on");
    move(event);
  });
  node.addEventListener("pointermove", move);
  node.addEventListener("pointerleave", () => {
    tooltip().classList.remove("on");
  });

  function move(event) {
    const box = tooltip();
    const pad = 14;
    let x = event.clientX + pad;
    let y = event.clientY + pad;
    const rect = box.getBoundingClientRect();
    if (x + rect.width > innerWidth - 8) x = event.clientX - rect.width - pad;
    if (y + rect.height > innerHeight - 8) y = event.clientY - rect.height - pad;
    box.style.left = `${Math.max(8, x)}px`;
    box.style.top = `${Math.max(8, y)}px`;
  }
}

const ttRow = (key, value) =>
  `<div><span class="tt-k">${esc(key)}</span> <span class="tt-v">${esc(value)}</span></div>`;

export function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ---- scales and chrome ---------------------------------------------- */

/** Round a maximum up to a friendly axis top and pick ~4 ticks. */
function niceTicks(max) {
  if (max <= 0) return { top: 1, ticks: [0, 1] };
  const raw = max / 4;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || mag * 10;
  const top = Math.ceil(max / step) * step;
  const ticks = [];
  for (let t = 0; t <= top + 1e-9; t += step) ticks.push(Math.round(t * 100) / 100);
  return { top, ticks };
}

function gridAndAxis(svg, { left, right, top, bottom }, ticks, axisTop, fmt = (v) => v) {
  for (const value of ticks) {
    const y = bottom - (value / axisTop) * (bottom - top);
    svg.append(
      el("line", {
        x1: left, x2: right, y1: y, y2: y,
        stroke: "var(--grid)", "stroke-width": 1,
        "shape-rendering": "crispEdges",
      }),
    );
    const label = el("text", {
      x: left - 8, y: y + 4,
      "text-anchor": "end",
      fill: "var(--muted)",
      "font-size": 11,
      "font-variant-numeric": "tabular-nums",
    });
    label.textContent = fmt(value);
    svg.append(label);
  }
  svg.append(
    el("line", {
      x1: left, x2: right, y1: bottom, y2: bottom,
      stroke: "var(--axis)", "stroke-width": 1,
      "shape-rendering": "crispEdges",
    }),
  );
}

/** A bar with rounded far end, anchored flat to the baseline. */
function barPath(x, y, w, h, r = 4) {
  const radius = Math.max(0, Math.min(r, w / 2, h));
  if (h <= 0.5) return `M${x} ${y + h} h${w}`;
  return [
    `M${x} ${y + h}`,
    `V${y + radius}`,
    `Q${x} ${y} ${x + radius} ${y}`,
    `H${x + w - radius}`,
    `Q${x + w} ${y} ${x + w} ${y + radius}`,
    `V${y + h}`,
    "Z",
  ].join(" ");
}

function hBarPath(x, y, w, h, r = 4) {
  const radius = Math.max(0, Math.min(r, h / 2, w));
  if (w <= 0.5) return `M${x} ${y} v${h}`;
  return [
    `M${x} ${y}`,
    `H${x + w - radius}`,
    `Q${x + w} ${y} ${x + w} ${y + radius}`,
    `V${y + h - radius}`,
    `Q${x + w} ${y + h} ${x + w - radius} ${y + h}`,
    `H${x}`,
    "Z",
  ].join(" ");
}

function frame(width, height) {
  const svg = el("svg", {
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    role: "img",
    preserveAspectRatio: "xMinYMid meet",
  });
  return svg;
}

function mount(host, svg, title) {
  host.innerHTML = "";
  const label = el("title");
  label.textContent = title;
  svg.prepend(label);
  host.append(svg);
}

/* ---- table view ------------------------------------------------------ */

/** The accessible twin of a chart: the same numbers as a table. */
export function tableView(host, columns, rows, summaryText = "Show the numbers") {
  const details = document.createElement("details");
  details.className = "table-view";
  const summary = document.createElement("summary");
  summary.textContent = summaryText;
  details.append(summary);

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = column;
    headRow.append(th);
  }
  thead.append(headRow);
  table.append(thead);

  const tbody = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const cell of row) {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.append(td);
    }
    tbody.append(tr);
  }
  table.append(tbody);
  details.append(table);
  host.append(details);
}

export function legend(host, keys) {
  const box = document.createElement("div");
  box.className = "legend";
  for (const { label, color } of keys) {
    const key = document.createElement("span");
    key.className = "key";
    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.background = color;
    const text = document.createElement("span");
    text.textContent = label;
    key.append(swatch, text);
    box.append(key);
  }
  host.append(box);
}

/* ---- charts ---------------------------------------------------------- */

/**
 * Vertical bars over a time axis, one or two series.
 *
 * @param {{label: string, color: string, values: number[]}[]} series
 */
export function timeBars(host, labels, series, { title, valueName = "postings" } = {}) {
  const pad = { left: 44, right: 12, top: 12, bottom: 34 };
  const n = Math.max(labels.length, 1);
  const slotW = Math.max(18, Math.min(64, 760 / n));
  const width = Math.max(320, pad.left + pad.right + slotW * n);
  const height = 260;
  const svg = frame(width, height);

  const max = Math.max(1, ...series.flatMap((s) => s.values));
  const { top: axisTop, ticks } = niceTicks(max);
  const plotBottom = height - pad.bottom;
  const plotHeight = plotBottom - pad.top;

  gridAndAxis(svg, { left: pad.left, right: width - pad.right, top: pad.top, bottom: plotBottom }, ticks, axisTop);

  const gap = 2; // surface gap between adjacent fills
  const groupW = slotW - 8;
  const barW = Math.max(3, (groupW - gap * (series.length - 1)) / series.length);

  labels.forEach((label, i) => {
    const slotX = pad.left + i * slotW + 4;
    series.forEach((s, j) => {
      const value = s.values[i] || 0;
      const h = (value / axisTop) * plotHeight;
      const x = slotX + j * (barW + gap);
      const y = plotBottom - h;
      const path = el("path", { d: barPath(x, y, barW, h), fill: s.color });
      svg.append(path);

      // A transparent hit area the full height of the plot, so short bars and
      // zero days are still easy to hover.
      const hit = el("rect", {
        x, y: pad.top, width: barW, height: plotHeight, fill: "transparent",
      });
      hoverable(
        hit,
        `<div><strong>${esc(label)}</strong></div>` +
          ttRow(`${s.label}:`, `${value} ${valueName}`),
      );
      svg.append(hit);
    });

    // Thin out date labels so they never collide.
    const every = Math.ceil((labels.length * 58) / Math.max(1, width - pad.left));
    if (i % every === 0 || i === labels.length - 1) {
      const text = el("text", {
        x: slotX + groupW / 2,
        y: plotBottom + 18,
        "text-anchor": "middle",
        fill: "var(--muted)",
        "font-size": 11,
      });
      text.textContent = label.slice(5); // MM-DD
      svg.append(text);
    }
  });

  mount(host, svg, title || "Bar chart");
}

/** Horizontal bars for a ranked category list. */
export function rankedBars(host, items, { title, color = "var(--series-1)", valueName = "postings", labelWidth = 190 } = {}) {
  const rowH = 26;
  const pad = { left: labelWidth, right: 46, top: 6, bottom: 22 };
  const width = 760;
  const height = pad.top + pad.bottom + rowH * Math.max(items.length, 1);
  const svg = frame(width, height);

  const max = Math.max(1, ...items.map((d) => d.value));
  const plotLeft = pad.left;
  const plotRight = width - pad.right;
  const plotWidth = plotRight - plotLeft;

  items.forEach((item, i) => {
    const y = pad.top + i * rowH;
    const barH = rowH - 2 - 2; // 2px surface gap between neighbouring bars
    const w = (item.value / max) * plotWidth;

    svg.append(el("path", { d: hBarPath(plotLeft, y + 1, w, barH), fill: color }));

    const label = el("text", {
      x: plotLeft - 10,
      y: y + barH / 2 + 5,
      "text-anchor": "end",
      fill: "var(--text-2)",
      "font-size": 12,
    });
    label.textContent = item.label.length > 30 ? `${item.label.slice(0, 29)}…` : item.label;
    svg.append(label);

    // Direct value label: selective labelling means the ranked list gets one
    // per bar, which is what makes the axis unnecessary here.
    const value = el("text", {
      x: plotLeft + w + 8,
      y: y + barH / 2 + 5,
      fill: "var(--text-2)",
      "font-size": 12,
      "font-variant-numeric": "tabular-nums",
    });
    value.textContent = item.value;
    svg.append(value);

    const hit = el("rect", {
      x: plotLeft, y, width: plotWidth, height: rowH, fill: "transparent",
    });
    hoverable(
      hit,
      `<div><strong>${esc(item.label)}</strong></div>` +
        ttRow("", `${item.value} ${valueName}`),
    );
    svg.append(hit);
  });

  mount(host, svg, title || "Ranked bar chart");
}

/** A distribution of whole-day buckets, with the median called out. */
export function histogram(host, buckets, { title, color = "var(--series-1)", markerValue = null, markerLabel = "" } = {}) {
  const pad = { left: 44, right: 14, top: 26, bottom: 40 };
  const n = Math.max(buckets.length, 1);
  const slotW = Math.max(20, Math.min(56, 700 / n));
  const width = Math.max(320, pad.left + pad.right + slotW * n);
  const height = 250;
  const svg = frame(width, height);

  const max = Math.max(1, ...buckets.map((b) => b.value));
  const { top: axisTop, ticks } = niceTicks(max);
  const plotBottom = height - pad.bottom;
  const plotHeight = plotBottom - pad.top;

  gridAndAxis(svg, { left: pad.left, right: width - pad.right, top: pad.top, bottom: plotBottom }, ticks, axisTop);

  const barW = slotW - 2 - 2;

  buckets.forEach((bucket, i) => {
    const x = pad.left + i * slotW + 2;
    const h = (bucket.value / axisTop) * plotHeight;
    const y = plotBottom - h;
    svg.append(el("path", { d: barPath(x, y, barW, h), fill: color }));

    const hit = el("rect", { x, y: pad.top, width: barW, height: plotHeight, fill: "transparent" });
    hoverable(
      hit,
      `<div><strong>${esc(bucket.label)} days open</strong></div>` +
        ttRow("", `${bucket.value} postings`),
    );
    svg.append(hit);

    const text = el("text", {
      x: x + barW / 2, y: plotBottom + 17,
      "text-anchor": "middle", fill: "var(--muted)", "font-size": 11,
    });
    text.textContent = bucket.label;
    svg.append(text);
  });

  if (markerValue !== null && markerValue !== undefined) {
    const index = buckets.findIndex((b) => b.key === markerValue);
    if (index >= 0) {
      const x = pad.left + index * slotW + 2 + barW / 2;
      svg.append(
        el("line", {
          x1: x, x2: x, y1: pad.top - 6, y2: plotBottom,
          stroke: "var(--series-2)", "stroke-width": 2,
          "stroke-dasharray": "4 3",
        }),
      );
      const text = el("text", {
        x, y: pad.top - 11,
        "text-anchor": "middle", fill: "var(--series-2)",
        "font-size": 11, "font-weight": 650,
      });
      text.textContent = markerLabel;
      svg.append(text);
    }
  }

  const axisLabel = el("text", {
    x: pad.left + (width - pad.left - pad.right) / 2,
    y: height - 6,
    "text-anchor": "middle", fill: "var(--muted)", "font-size": 11,
  });
  axisLabel.textContent = "Days from first seen to removed";
  svg.append(axisLabel);

  mount(host, svg, title || "Histogram");
}

/**
 * A single proportion: one bar split into the share and the remainder.
 * The headline number lives beside it as a hero figure, not inside the chart.
 */
export function shareBar(host, { part, whole, partLabel, restLabel, title }) {
  const width = 760;
  const height = 74;
  const svg = frame(width, height);
  const barH = 30;
  const y = 14;
  const fraction = whole > 0 ? part / whole : 0;
  const partW = Math.max(0, Math.round(fraction * width));
  const gap = 2;

  if (partW > 0) {
    svg.append(el("path", { d: hBarPath(0, y, Math.max(partW - gap, 1), barH), fill: "var(--series-1)" }));
  }
  if (partW < width) {
    svg.append(
      el("path", {
        d: hBarPath(partW, y, width - partW, barH),
        fill: "var(--grid)",
      }),
    );
  }

  const hitPart = el("rect", { x: 0, y, width: Math.max(partW, 1), height: barH, fill: "transparent" });
  hoverable(hitPart, `<div><strong>${esc(partLabel)}</strong></div>` + ttRow("", `${part} of ${whole}`));
  svg.append(hitPart);

  const hitRest = el("rect", { x: partW, y, width: Math.max(width - partW, 1), height: barH, fill: "transparent" });
  hoverable(hitRest, `<div><strong>${esc(restLabel)}</strong></div>` + ttRow("", `${whole - part} of ${whole}`));
  svg.append(hitRest);

  const left = el("text", { x: 0, y: y + barH + 18, fill: "var(--text-2)", "font-size": 12 });
  left.textContent = `${partLabel} — ${part}`;
  svg.append(left);

  const right = el("text", {
    x: width, y: y + barH + 18,
    "text-anchor": "end", fill: "var(--text-2)", "font-size": 12,
  });
  right.textContent = `${restLabel} — ${whole - part}`;
  svg.append(right);

  mount(host, svg, title || "Share");
}
