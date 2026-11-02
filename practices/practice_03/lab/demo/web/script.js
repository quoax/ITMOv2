let current = { offset: 0, limit: 20, sort: "asc" };
let inFlight = null;
let lastErrorDetails = null;

async function api(path, body, signal) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });
  let json = null;
  try {
    json = await res.json();
  } catch (_) {
    json = {};
  }
  if (!res.ok) {
    const err = new Error((json && json.error && (json.error.message || json.error.code)) || "Request failed");
    err.status = res.status;
    err.payload = json;
    throw err;
  }
  return json;
}

function setLoading(loading) {
  const root = document.querySelector("main");
  root.classList.toggle("loading", !!loading);
}

function updateURL() {
  const url = new URL(window.location.href);
  url.searchParams.set("offset", String(current.offset));
  url.searchParams.set("limit", String(current.limit));
  url.searchParams.set("sort", current.sort);
  history.replaceState(null, "", url);
}

function parseURL() {
  const url = new URL(window.location.href);
  const offset = parseInt(url.searchParams.get("offset") || "0", 10);
  const limit = parseInt(url.searchParams.get("limit") || "20", 10);
  const sort = url.searchParams.get("sort") || "asc";
  current.offset = isNaN(offset) || offset < 0 ? 0 : offset;
  current.limit = isNaN(limit) || limit < 1 || limit > 100 ? 20 : limit;
  current.sort = (sort === "asc" || sort === "desc") ? sort : "asc";
}

async function refresh() {
  // cancel previous
  if (inFlight) inFlight.abort();
  const ac = new AbortController();
  inFlight = ac;
  setLoading(true);
  document.querySelector("#error").textContent = "";
  lastErrorDetails = null;
  document.querySelector("#sort").value = current.sort;
  try {
    const q = new URLSearchParams({
      offset: String(current.offset),
      limit: String(current.limit),
      sort: current.sort,
    });
    const data = await api(`/api/v1/subscribers?${q.toString()}`, undefined, ac.signal);
    renderList(data.items, data.total);
  } catch (err) {
    if (err.name === "AbortError") return; // silent
    const errorEl = document.querySelector("#error");
    const hintsEl = document.querySelector('#hints');
    errorEl.textContent = err.message || "Ошибка";
    // highlight invalid params when 400
    document.querySelector('#pager').classList.remove('invalid');
    document.querySelector('#sort').classList.remove('invalid');
    if (err.status === 400 && err.payload && err.payload.error && err.payload.error.details) {
      const d = err.payload.error.details;
      const fixes = [];
      if (d.limit) fixes.push("limit → [1,100]");
      if (d.offset) fixes.push("offset ≥ 0");
      if (d.sort) fixes.push("sort ∈ {asc, desc}");
      if (d.limit || d.offset) document.querySelector('#pager').classList.add('invalid');
      if (d.sort) document.querySelector('#sort').classList.add('invalid');
      if (fixes.length) {
        hintsEl.innerHTML = `Некорректные параметры запроса. Предлагается: ${fixes.join(', ')}. <button id="apply-fixes">Применить исправления</button>`;
        const btn = document.querySelector('#apply-fixes');
        if (btn) btn.onclick = () => {
          current.limit = Math.max(1, Math.min(100, current.limit));
          current.offset = Math.max(0, current.offset);
          current.sort = (current.sort === 'desc') ? 'desc' : 'asc';
          document.querySelector('#pager').classList.remove('invalid');
          document.querySelector('#sort').classList.remove('invalid');
          updateURL(); refresh();
        };
      } else {
        hintsEl.textContent = '';
      }
    } else {
      // 5xx or network
      const retryBtn = document.createElement('button');
      retryBtn.textContent = 'Повторить';
      retryBtn.onclick = () => refresh();
      const cancelBtn = document.createElement('button');
      cancelBtn.textContent = 'Отмена';
      cancelBtn.onclick = () => { /* nothing */ };
      const hints = document.querySelector('#hints');
      hints.innerHTML = '';
      hints.append(retryBtn, cancelBtn);
    }
  } finally {
    setLoading(false);
  }
}

function renderList(items, total) {
  // Edge: when no items but total > 0 and offset > 0, jump to last page
  if (items.length === 0 && total > 0 && current.offset > 0) {
    const pageCount = Math.ceil(total / current.limit);
    current.offset = Math.max((pageCount - 1) * current.limit, 0);
    updateURL();
    refresh();
    return;
  }
  const filter = document.querySelector("#filter").value.toLowerCase();
  const list = document.querySelector("#list");
  list.innerHTML = "";
  for (const it of items) {
    if (filter && !String(it.email).toLowerCase().includes(filter)) continue;
    const li = document.createElement("li");
    li.textContent = `${it.email} (${new Date(it.created_at).toLocaleString()})`;
    list.appendChild(li);
  }
  // summary
  const summary = document.querySelector("#summary");
  const X = total > 0 ? current.offset + 1 : 0;
  const Y = current.offset + items.length;
  summary.textContent = `Показано ${X}–${Y} из ${total}`;
  // pager
  const pagesEl = document.querySelector("#pages");
  pagesEl.innerHTML = "";
  const pageCount = total > 0 ? Math.ceil(total / current.limit) : 1;
  const currentPage = Math.floor(current.offset / current.limit) + 1;
  const windowSize = 5;
  let start = Math.max(1, currentPage - Math.floor(windowSize / 2));
  let end = Math.min(pageCount, start + windowSize - 1);
  start = Math.max(1, Math.min(start, Math.max(1, end - windowSize + 1)));
  for (let p = start; p <= end; p++) {
    const b = document.createElement("button");
    b.textContent = String(p);
    if (p === currentPage) b.disabled = true;
    b.onclick = () => { current.offset = (p - 1) * current.limit; updateURL(); refresh(); };
    pagesEl.appendChild(b);
  }
  const first = document.querySelector('button[data-act="first"]');
  const prev = document.querySelector('button[data-act="prev"]');
  const next = document.querySelector('button[data-act="next"]');
  const last = document.querySelector('button[data-act="last"]');
  first.disabled = prev.disabled = (current.offset === 0);
  next.disabled = last.disabled = (current.offset + current.limit >= total);
}

document.querySelector("#add-form").onsubmit = async (e) => {
  e.preventDefault();
  const name = document.querySelector("#name").value;
  const status = document.querySelector("#status");
  setLoading(true);
  try {
    await api("/api/subscribe", { name });
    status.textContent = "Добавлено";
  } catch (err) {
    status.textContent = err.message;
  } finally {
    setLoading(false);
    await refresh();
  }
};

document.querySelector("#filter").oninput = debounce(refresh, 200);
document.querySelector("#sort").onchange = () => { current.sort = document.querySelector("#sort").value; current.offset = 0; updateURL(); refresh(); };
document.querySelector('button[data-act="first"]').onclick = () => { current.offset = 0; updateURL(); refresh(); };
document.querySelector('button[data-act="prev"]').onclick = () => { current.offset = Math.max(current.offset - current.limit, 0); updateURL(); refresh(); };
document.querySelector('button[data-act="next"]').onclick = () => { current.offset = current.offset + current.limit; updateURL(); refresh(); };
document.querySelector('button[data-act="last"]').onclick = () => { const totalText = document.querySelector("#summary").textContent; /* last will recompute after fetch */ current.offset = Number.MAX_SAFE_INTEGER; updateURL(); refresh(); };

function debounce(fn, ms) { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); }; }

parseURL();
updateURL();
refresh();

// Error remediation UI per UI spec (SHOULD): allow user to clip params to valid range
// no extra mutation observer; remediation handled directly in catch
