// Gestion du thème sombre / clair, recherche instantanée et interactivité
(function () {
  // 1. Thème
  const themeBtn = document.getElementById("themeToggle");
  const currentTheme = localStorage.getItem("academic-theme") || "light";
  document.documentElement.setAttribute("data-theme", currentTheme);

  if (themeBtn) {
    themeBtn.addEventListener("click", () => {
      const activeTheme = document.documentElement.getAttribute("data-theme");
      const nextTheme = activeTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      localStorage.setItem("academic-theme", nextTheme);
    });
  }

  // 2. Copie du code
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.closest(".code-container").querySelector("pre code").innerText;
      navigator.clipboard.writeText(code).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = "<span>✓ Copié</span>";
        setTimeout(() => {
          btn.innerHTML = originalText;
        }, 2000);
      });
    });
  });

  // 3. Recherche instantanée
  const searchInput = document.getElementById("searchInput");
  const modal = document.getElementById("searchModal");
  const modalInput = document.getElementById("modalSearchInput");
  const modalResults = document.getElementById("modalSearchResults");
  let searchData = [];

  fetch("assets/js/search_index.json")
    .then((r) => r.json())
    .then((data) => {
      searchData = data;
    })
    .catch((err) => console.error("Index non chargé :", err));

  function openSearch() {
    if (modal) {
      modal.style.display = "flex";
      modalInput.focus();
    }
  }

  function closeSearch() {
    if (modal) {
      modal.style.display = "none";
    }
  }

  if (searchInput) {
    searchInput.addEventListener("focus", openSearch);
  }

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeSearch();
    });
    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeSearch();
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        openSearch();
      }
    });
  }

  if (modalInput) {
    modalInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q || !searchData.length) {
        modalResults.innerHTML = "<p style='color:var(--text-muted);font-size:0.875rem;'>Saisissez un terme à rechercher...</p>";
        return;
      }

      const results = searchData
        .filter((item) => item.title.toLowerCase().includes(q) || item.content.toLowerCase().includes(q))
        .slice(0, 10);

      if (!results.length) {
        modalResults.innerHTML = "<p style='color:var(--text-muted);font-size:0.875rem;'>Aucun résultat trouvé pour « " + q + " ».</p>";
        return;
      }

      modalResults.innerHTML = results
        .map((res) => {
          return `
            <a href="${res.url}" class="search-result-item" onclick="document.getElementById('searchModal').style.display='none'">
              <div class="search-result-title">${res.pageTitle} &rarr; ${res.title}</div>
              <div class="search-result-snippet">${res.snippet}</div>
            </a>
          `;
        })
        .join("");
    });
  }

  // 4. Surbrillance dynamique de la TOC lors du scroll
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          document.querySelectorAll(".toc-list a").forEach((a) => {
            if (a.getAttribute("href") === "#" + id) {
              a.style.color = "var(--accent-primary)";
              a.style.fontWeight = "600";
            } else {
              a.style.color = "";
              a.style.fontWeight = "";
            }
          });
        }
      });
    },
    { rootMargin: "0px 0px -70% 0px" }
  );

  document.querySelectorAll(".markdown-body h2, .markdown-body h3").forEach((h) => {
    observer.observe(h);
  });
})();
