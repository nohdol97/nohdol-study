(() => {
  "use strict";
  const grid = document.getElementById("sites");
  const query = document.getElementById("query");
  const category = document.getElementById("category");
  const empty = document.getElementById("empty");
  const count = document.getElementById("site-count");
  let sites = [];
  const normalize = (value) => String(value ?? "").normalize("NFKC").toLowerCase();

  function card(site, index) {
    const link = document.createElement("a");
    link.className = "site-card";
    link.href = site.href;
    const top = document.createElement("div");
    top.className = "site-top";
    const number = document.createElement("span");
    number.className = "site-index";
    number.textContent = String(index + 1).padStart(2, "0");
    const status = document.createElement("span");
    status.className = "status";
    status.textContent = site.status;
    top.append(number, status);
    const title = document.createElement("h2");
    title.textContent = site.title;
    const description = document.createElement("p");
    description.textContent = site.description;
    const tags = document.createElement("div");
    tags.className = "tags";
    [site.category, ...site.tags].forEach((value) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = value;
      tags.append(tag);
    });
    const open = document.createElement("span");
    open.className = "open";
    open.textContent = "사이트 열기 →";
    link.append(top, title, description, tags, open);
    return link;
  }

  function render() {
    const needle = normalize(query.value).trim();
    const selected = category.value;
    const filtered = sites.filter((site) => (!selected || site.category === selected) && (!needle || normalize(`${site.title} ${site.description} ${site.category} ${site.tags.join(" ")}`).includes(needle)));
    grid.replaceChildren(...filtered.map(card));
    empty.hidden = filtered.length > 0;
    count.textContent = `${filtered.length} / ${sites.length} sites`;
  }

  fetch("sites.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((manifest) => {
      sites = manifest.sites.filter((site) => site.status !== "archived");
      [...new Set(sites.map((site) => site.category))].sort((a, b) => a.localeCompare(b, "ko")).forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        category.append(option);
      });
      render();
    })
    .catch((error) => {
      count.textContent = "manifest error";
      const message = document.createElement("p");
      message.className = "error";
      message.textContent = `사이트 목록을 읽지 못했습니다: ${error.message}. _workspace 루트에서 HTTP 서버를 실행했는지 확인하세요.`;
      grid.replaceChildren(message);
    });
  query.addEventListener("input", render);
  category.addEventListener("change", render);
})();
