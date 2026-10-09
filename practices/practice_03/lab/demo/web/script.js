async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Request failed");
  return json;
}

async function refresh() {
  const data = await api("/api/subscribers");
  const filter = document.querySelector("#filter").value.toLowerCase();
  const list = document.querySelector("#list");
  list.innerHTML = "";
  for (const name of data.subscribers) {
    if (filter && !name.toLowerCase().includes(filter)) continue;
    const li = document.createElement("li");
    li.textContent = name;
    const btn = document.createElement("button");
    btn.textContent = "Удалить";
    btn.onclick = async () => {
      await api("/api/unsubscribe", { name });
      await refresh();
    };
    li.appendChild(btn);
    list.appendChild(li);
  }
}

document.querySelector("#add-form").onsubmit = async (e) => {
  e.preventDefault();
  const name = document.querySelector("#name").value;
  const status = document.querySelector("#status");
  try {
    await api("/api/subscribe", { name });
    status.textContent = "Добавлено";
  } catch (err) {
    status.textContent = err.message;
  } finally {
    await refresh();
  }
};

document.querySelector("#filter").oninput = debounce(refresh, 200);

function debounce(fn, ms) { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); }; }

refresh();
