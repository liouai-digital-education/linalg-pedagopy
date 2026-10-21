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
        const originalText = btn.textContent;
        btn.textContent = "✓ Copié";
        setTimeout(() => {
          btn.textContent = originalText;
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

  // Les résultats sont construits avec textContent : ni la saisie ni le texte indexé ne sont
  // interprétés comme du HTML (un extrait « a < b » ou une saisie « <img onerror=…> » restent du texte).
  function message(texte) {
    const p = document.createElement("p");
    p.style.color = "var(--text-muted)";
    p.style.fontSize = "0.875rem";
    p.textContent = texte;
    modalResults.replaceChildren(p);
  }

  // Comparaison sans casse ni accents (« determinant » trouve « déterminant ») ; la longueur du texte
  // est conservée pour un texte en NFC, si bien que les positions trouvées valent dans l'original.
  function sansAccents(texte) {
    return texte.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function extraitAutour(res, q) {
    const i = sansAccents(res.content).indexOf(q);
    if (i < 0) return res.snippet;
    const debut = Math.max(0, i - 60);
    const fin = Math.min(res.content.length, i + q.length + 100);
    return (debut > 0 ? "…" : "") + res.content.slice(debut, fin) + (fin < res.content.length ? "…" : "");
  }

  function resultat(res, q) {
    const lien = document.createElement("a");
    lien.href = res.url;
    lien.className = "search-result-item";
    lien.addEventListener("click", closeSearch);
    const titre = document.createElement("div");
    titre.className = "search-result-title";
    titre.textContent = res.pageTitle + " → " + res.title;
    const extrait = document.createElement("div");
    extrait.className = "search-result-snippet";
    extrait.textContent = extraitAutour(res, q);
    lien.append(titre, extrait);
    return lien;
  }

  if (modalInput) {
    modalInput.addEventListener("input", (e) => {
      const q = sansAccents(e.target.value.trim());
      if (!q || !searchData.length) {
        message("Saisissez un terme à rechercher...");
        return;
      }

      const dansTitre = searchData.filter((item) => sansAccents(item.title).includes(q));
      const dansTexte = searchData.filter(
        (item) => !sansAccents(item.title).includes(q) && sansAccents(item.content).includes(q)
      );
      const results = dansTitre.concat(dansTexte).slice(0, 10);

      if (!results.length) {
        message("Aucun résultat trouvé pour « " + e.target.value.trim() + " ».");
        return;
      }

      modalResults.replaceChildren(...results.map((res) => resultat(res, q)));
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
