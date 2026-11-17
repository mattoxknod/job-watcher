/* Loading the two data files and doing the work in the browser.
 *
 * Both files are fetched from the network when the computer is online. The
 * service worker keeps the last copy it saw, so when the computer is offline
 * the same fetches are served from that cache and the pages still open with
 * the last data they loaded.
 */

const DATA = {
  history: "./data/history.csv",
  status: "./data/status.json",
};

/* ---- CSV ------------------------------------------------------------- */

/** Parse RFC 4180 CSV. Titles carry commas and quotes, so this handles both. */
export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;

  // Strip a UTF-8 byte order mark and normalise line endings.
  const src = text.replace(/^﻿/, "");

  for (let i = 0; i < src.length; i += 1) {
    const ch = src[i];

    if (quoted) {
      if (ch === '"') {
        if (src[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        field += ch;
      }
      continue;
    }

    if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && src[i + 1] === "\n") i += 1;
      row.push(field);
      field = "";
      rows.push(row);
      row = [];
    } else {
      field += ch;
    }
  }

  if (field !== "" || row.length) {
    row.push(field);
    rows.push(row);
  }

  if (!rows.length) return [];
  const header = rows[0];
  return rows
    .slice(1)
    .filter((r) => r.length > 1)
    .map((r) => {
      const record = {};
      header.forEach((key, idx) => {
        record[key] = r[idx] === undefined ? "" : r[idx];
      });
      return record;
    });
}

/* ---- dates ----------------------------------------------------------- */

/** A YYYY-MM-DD string as a UTC day number, so differences are whole days. */
export function dayNumber(iso) {
  if (!iso) return null;
  const ms = Date.parse(`${iso}T00:00:00Z`);
  return Number.isNaN(ms) ? null : Math.round(ms / 86400000);
}

export function daysBetween(fromIso, toIso) {
  const a = dayNumber(fromIso);
  const b = dayNumber(toIso);
  if (a === null || b === null) return null;
  return b - a;
}

export function isoFromDayNumber(day) {
  return new Date(day * 86400000).toISOString().slice(0, 10);
}

/** Every date from the first to the last, so a quiet day still shows as zero. */
export function dateRange(firstIso, lastIso) {
  const a = dayNumber(firstIso);
  const b = dayNumber(lastIso);
  if (a === null || b === null || b < a) return [];
  const out = [];
  for (let d = a; d <= b; d += 1) out.push(isoFromDayNumber(d));
  return out;
}

export function formatDate(iso) {
  if (!iso) return "";
  const ms = Date.parse(`${iso}T00:00:00Z`);
  if (Number.isNaN(ms)) return iso;
  return new Date(ms).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function formatRunTime(value) {
  if (!value) return "unknown";
  const ms = Date.parse(value);
  if (Number.isNaN(ms)) return value;
  return new Date(ms).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

/* ---- loading --------------------------------------------------------- */

/** Every column the history writes as "true"/"false" text. */
const BOOLEAN_COLUMNS = ["in_role", "first_run", "mech_role", "entry_level"];

/**
 * Turn the boolean columns into real booleans once, at load.
 *
 * This matters more than it looks: the CSV carries the string "false", and a
 * non-empty string is truthy in JavaScript, so a column left as text would
 * read as true on every row.
 */
function hydrate(row) {
  for (const column of BOOLEAN_COLUMNS) {
    row[column] = row[column] === "true";
  }
  return row;
}

export async function loadData() {
  const [historyRes, statusRes] = await Promise.all([
    fetch(DATA.history, { cache: "no-cache" }),
    fetch(DATA.status, { cache: "no-cache" }),
  ]);

  if (!historyRes.ok) throw new Error(`history.csv: ${historyRes.status}`);
  if (!statusRes.ok) throw new Error(`status.json: ${statusRes.status}`);

  const [historyText, status] = await Promise.all([
    historyRes.text(),
    statusRes.json(),
  ]);

  const history = parseCsv(historyText).map(hydrate);
  return { history, status };
}

/* ---- derived numbers ------------------------------------------------- */

/** The last day the pipeline ran, taken from the history itself. */
export function lastRunDate(history) {
  let latest = "";
  for (const row of history) {
    if (row.last_seen > latest) latest = row.last_seen;
    if (row.removed_date > latest) latest = row.removed_date;
  }
  return latest;
}

export function firstRunDate(history) {
  let earliest = "";
  for (const row of history) {
    if (!earliest || (row.first_seen && row.first_seen < earliest)) {
      earliest = row.first_seen;
    }
  }
  return earliest;
}

export const isOpen = (row) => row.status === "open";

/** Days a posting has been open, counted to the last run. */
export function daysOpen(row, asOf) {
  const end = row.status === "removed" ? row.removed_date : asOf;
  return daysBetween(row.first_seen, end);
}

export function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2;
}

export function countBy(rows, key) {
  const counts = new Map();
  for (const row of rows) {
    const value = (typeof key === "function" ? key(row) : row[key]) || "";
    if (!value) continue;
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return [...counts.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value || a.label.localeCompare(b.label));
}

/* ---- shared page chrome --------------------------------------------- */

/** Mark the current page in the nav and show the offline flag. */
export function initChrome() {
  const here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav a").forEach((link) => {
    const target = link.getAttribute("href");
    if (target === here || (here === "" && target === "index.html")) {
      link.setAttribute("aria-current", "page");
    }
  });

  const paint = () => {
    document.body.classList.toggle("is-offline", !navigator.onLine);
  };
  paint();
  addEventListener("online", paint);
  addEventListener("offline", paint);

  if ("serviceWorker" in navigator) {
    // A new service worker takes over as soon as it installs, which means the
    // page being read was served from the previous version's cache. Reloading
    // once on handover swaps it for the deployed one, so a visit after a
    // deploy never leaves someone looking at the old page.
    let reloading = false;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (reloading) return;
      reloading = true;
      location.reload();
    });

    addEventListener("load", () => {
      navigator.serviceWorker.register("./sw.js").catch(() => {
        /* The pages work without it; only offline support is lost. */
      });
    });
  }
}

export function showError(node, error) {
  node.innerHTML = "";
  const box = document.createElement("div");
  box.className = "error";
  box.textContent = `Could not load the data files (${error.message}). If this is the first visit, the site needs to be online once.`;
  node.append(box);
}
