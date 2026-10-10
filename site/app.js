/* Carte « La France dans le monde » : lecture de data/donnees.json et affichage. */
(function () {
  "use strict";

  const SANS_DONNEE = "#d6d8d3";
  const NOMS_COUCHES = { imf: "macro-économie (IMF)", commerce: "commerce (Eurostat)", gels: "gels d'avoirs (DG Trésor)" };

  // Classes fixes, expliquées dans la légende (plus lisibles que des quantiles).
  const COUCHES = [
    {
      id: "croissance", libelle: "Croissance", source: "imf", champ: "croissance_pib",
      titre: v => `Croissance du PIB réel, ${v.annee} (%)`,
      classes: [
        { max: -2, couleur: "#b8302f", texte: "Moins de −2 %" },
        { max: -0.5, couleur: "#ee8f8e", texte: "−2 à −0,5 %" },
        { max: 0.5, couleur: "#f0efec", texte: "Stable (−0,5 à 0,5 %)" },
        { max: 3, couleur: "#86b6ef", texte: "0,5 à 3 %" },
        { max: Infinity, couleur: "#1c5cab", texte: "Plus de 3 %" },
      ],
      format: v => fmtNb(v, 1) + " %",
    },
    {
      id: "dette", libelle: "Dette publique", source: "imf", champ: "dette_publique",
      titre: v => `Dette publique brute, ${v.annee} (% du PIB)`,
      classes: [
        { max: 30, couleur: "#cde2fb", texte: "Moins de 30 %" },
        { max: 60, couleur: "#86b6ef", texte: "30 à 60 %" },
        { max: 90, couleur: "#3987e5", texte: "60 à 90 %" },
        { max: 120, couleur: "#1c5cab", texte: "90 à 120 %" },
        { max: Infinity, couleur: "#0d366b", texte: "Plus de 120 %" },
      ],
      format: v => fmtNb(v, 0) + " % du PIB",
    },
    {
      id: "exportations", libelle: "Exportations françaises", source: "commerce", champ: "exportations_fr",
      titre: v => `Exportations de biens de la France vers le pays, ${v.annee}`,
      classes: [
        { max: 100, couleur: "#cde2fb", texte: "Moins de 100 M€" },
        { max: 1000, couleur: "#86b6ef", texte: "100 M€ à 1 Md€" },
        { max: 5000, couleur: "#3987e5", texte: "1 à 5 Md€" },
        { max: 20000, couleur: "#1c5cab", texte: "5 à 20 Md€" },
        { max: Infinity, couleur: "#0d366b", texte: "Plus de 20 Md€" },
      ],
      format: v => fmtEuros(v),
    },
    {
      id: "gels", libelle: "Gels d'avoirs", source: "gels", champ: "entrees_gel", zeroSiAbsent: true,
      titre: () => "Entrées au registre français des gels d'avoirs",
      classes: [
        { max: 0, couleur: "#eef0f3", texte: "Aucune" },
        { max: 5, couleur: "#cde2fb", texte: "1 à 5" },
        { max: 20, couleur: "#86b6ef", texte: "6 à 20" },
        { max: 100, couleur: "#3987e5", texte: "21 à 100" },
        { max: Infinity, couleur: "#0d366b", texte: "Plus de 100" },
      ],
      format: v => fmtNb(v, 0) + (v > 1 ? " entrées" : " entrée"),
    },
  ];

  let donnees = null, geo = null, carte = null, coucheActive = COUCHES[0];

  /* ---------- formats ---------- */
  function fmtNb(v, dec) {
    return Number(v).toLocaleString("fr-FR", { minimumFractionDigits: dec, maximumFractionDigits: dec });
  }
  function fmtEuros(mEur) {
    const a = Math.abs(mEur);
    if (a >= 1000) return fmtNb(mEur / 1000, 1) + " Md€";
    return fmtNb(mEur, a < 10 ? 1 : 0) + " M€";
  }
  function fmtDate(iso) {
    if (!iso) return "date inconnue";
    const d = new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
    if (isNaN(d)) return iso;
    return d.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
  }
  function echapper(t) {
    return String(t).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  /* ---------- données ---------- */
  function valeur(iso3, couche) {
    const bloc = donnees && donnees.pays[iso3] && donnees.pays[iso3][couche.source];
    if (bloc && bloc[couche.champ] !== undefined) return bloc[couche.champ];
    const st = donnees && donnees.statut[couche.source];
    if (couche.zeroSiAbsent && st && st.derniere_reussite && iso3 !== "FRA") return 0;
    return null;
  }
  function couleur(v, couche) {
    if (v === null || v === undefined) return SANS_DONNEE;
    for (const c of couche.classes) if (v <= c.max) return c.couleur;
    return SANS_DONNEE;
  }
  function infosAnnee(couche) {
    const st = (donnees && donnees.statut[couche.source]) || {};
    if (couche.source === "imf") return { annee: (st[couche.champ] || {}).annee || "?" };
    return { annee: st.annee || "?" };
  }

  /* ---------- alertes de fraîcheur ---------- */
  function afficherAlertes() {
    const zone = document.getElementById("alertes");
    zone.innerHTML = "";
    if (!donnees) {
      zone.innerHTML = '<p class="erreur">Les données ne sont pas encore disponibles : la première collecte n\'a pas eu lieu ou a échoué.</p>';
      return;
    }
    const maintenant = Date.now();
    for (const [cle, nom] of Object.entries(NOMS_COUCHES)) {
      const st = donnees.statut[cle];
      let msg = null, classe = "avert";
      if (!st) { msg = `La couche ${nom} n'a jamais été collectée.`; classe = "erreur"; }
      else if (!st.ok) {
        classe = "erreur";
        msg = `La collecte ${nom} a échoué le ${fmtDate(st.derniere_tentative)}. ` +
          (st.derniere_reussite ? `Les données affichées sont celles collectées le ${fmtDate(st.derniere_reussite)}.` : "Aucune donnée n'est disponible.");
      } else if (maintenant - new Date(st.derniere_reussite).getTime() > 3 * 86400000) {
        msg = `La couche ${nom} n'a pas été mise à jour depuis le ${fmtDate(st.derniere_reussite)}.`;
      }
      if (msg) {
        const p = document.createElement("p");
        p.className = classe;
        p.textContent = msg;
        zone.appendChild(p);
      }
    }
  }

  /* ---------- légende et boutons ---------- */
  function construireBoutons() {
    const nav = document.getElementById("couches");
    COUCHES.forEach(c => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = c.libelle;
      b.setAttribute("aria-pressed", c === coucheActive ? "true" : "false");
      b.addEventListener("click", () => {
        coucheActive = c;
        nav.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
        colorier();
      });
      nav.appendChild(b);
    });
  }
  function afficherLegende() {
    const c = coucheActive;
    document.getElementById("legende-titre").textContent = c.titre(infosAnnee(c));
    const ol = document.getElementById("legende-classes");
    ol.innerHTML = "";
    [...c.classes, { couleur: SANS_DONNEE, texte: "Données indisponibles" }].forEach(k => {
      const li = document.createElement("li");
      li.innerHTML = `<i style="background:${k.couleur}"></i>${echapper(k.texte)}`;
      ol.appendChild(li);
    });
    const src = donnees ? donnees.sources[c.source] : null;
    const st = donnees ? donnees.statut[c.source] || {} : {};
    document.getElementById("legende-source").innerHTML = src
      ? `Source : <a href="${src.lien}" target="_blank" rel="noopener">${echapper(src.nom)}</a>. Collecté le ${fmtDate(st.derniere_reussite)}.`
      : "";
  }

  /* ---------- carte ---------- */
  function colorier() {
    if (!geo || !carte) return;
    geo.features.forEach(f => {
      const v = valeur(f.properties.iso3, coucheActive);
      f.properties.couleur = couleur(v, coucheActive);
      f.properties.v = v;
    });
    carte.getSource("pays").setData(geo);
    afficherLegende();
  }

  function initCarte() {
    carte = new maplibregl.Map({
      container: "carte",
      style: {
        version: 8,
        sources: {},
        layers: [{ id: "fond", type: "background", paint: { "background-color": getComputedStyle(document.documentElement).getPropertyValue("--mer").trim() || "#e6ecf2" } }],
      },
      center: [10, 25], zoom: 1.3, minZoom: 0.8, maxZoom: 6,
      renderWorldCopies: false, attributionControl: false,
    });
    carte.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
    carte.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: "Frontières : Natural Earth (vue France)" }));

    carte.on("load", () => {
      carte.addSource("pays", { type: "geojson", data: geo });
      carte.addLayer({ id: "pays-fond", type: "fill", source: "pays", paint: { "fill-color": ["get", "couleur"] } });
      carte.addLayer({
        id: "pays-trait", type: "line", source: "pays",
        paint: { "line-color": getComputedStyle(document.documentElement).getPropertyValue("--frontiere").trim() || "#fff", "line-width": 0.6 },
      });
      carte.addLayer({
        id: "pays-choisi", type: "line", source: "pays", filter: ["==", ["get", "iso3"], ""],
        paint: { "line-color": "#17212e", "line-width": 2 },
      });
      colorier();

      const bulle = document.getElementById("infobulle");
      carte.on("mousemove", "pays-fond", e => {
        const p = e.features[0].properties;
        carte.getCanvas().style.cursor = "pointer";
        const v = p.v === "null" || p.v === undefined || p.v === null ? null : Number(p.v);
        bulle.innerHTML = `<strong>${echapper(p.nom)}</strong>${v === null ? "Données indisponibles" : echapper(coucheActive.format(v))}`;
        bulle.hidden = false;
        const x = Math.min(e.point.x + 14, carte.getCanvas().clientWidth - 200);
        bulle.style.left = x + "px";
        bulle.style.top = (e.point.y + 14) + "px";
      });
      carte.on("mouseleave", "pays-fond", () => { carte.getCanvas().style.cursor = ""; bulle.hidden = true; });
      carte.on("click", "pays-fond", e => ouvrirFiche(e.features[0].properties.iso3));
    });
  }

  /* ---------- fiche pays ---------- */
  function ligneSource(cle) {
    const src = donnees.sources[cle], st = donnees.statut[cle] || {};
    return `<p class="source">Source : <a href="${src.lien}" target="_blank" rel="noopener">${echapper(src.nom)}</a>. Collecté le ${fmtDate(st.derniere_reussite)}.</p>`;
  }
  function bloc(titre, valeurHtml, detail, cle, lecture) {
    return `<section class="fait"><h3>${titre}</h3>${valeurHtml}${detail ? `<p class="detail">${detail}</p>` : ""}${lecture ? `<p class="lecture">${lecture}</p>` : ""}${ligneSource(cle)}</section>`;
  }
  const vide = t => `<p class="valeur vide">${t}</p>`;

  function ouvrirFiche(iso3) {
    const f = geo.features.find(x => x.properties.iso3 === iso3);
    if (!f || !donnees) return;
    const d = donnees.pays[iso3] || {};
    const imf = d.imf || {}, com = d.commerce || {}, gel = d.gels || {};
    const stImf = donnees.statut.imf || {};
    let html = "";

    html += bloc(`Croissance du PIB réel${imf.croissance_pib_annee ? ", " + imf.croissance_pib_annee : ""}`,
      imf.croissance_pib !== undefined ? `<p class="valeur">${fmtNb(imf.croissance_pib, 1)} %</p>` : vide("Donnée non publiée par l'IMF."),
      null, "imf", `${(stImf.croissance_pib || {}).edition || "World Economic Outlook"}. La valeur peut être une estimation ; les années suivantes sont des projections.`);

    html += bloc(`Dette publique brute${imf.dette_publique_annee ? ", " + imf.dette_publique_annee : ""}`,
      imf.dette_publique !== undefined ? `<p class="valeur">${fmtNb(imf.dette_publique, 0)} % du PIB</p>` : vide("Donnée non publiée par l'IMF."),
      null, "imf", null);

    if (iso3 === "FRA") {
      html += bloc("Commerce avec la France", vide("Sans objet."), null, "commerce", null);
    } else {
      html += bloc(`Commerce de biens avec la France${com.annee ? ", " + com.annee : ""}`,
        com.exportations_fr !== undefined ? `<p class="valeur">${fmtEuros(com.exportations_fr)} exportés par la France</p>` : vide("Aucun échange déclaré."),
        com.importations_fr !== undefined ? `${fmtEuros(com.importations_fr)} importés par la France. Solde pour la France : ${com.solde_fr >= 0 ? "+" : ""}${fmtEuros(com.solde_fr)}.` : null,
        "commerce", "Mesure l'intensité des échanges, pas la qualité de la relation.");
    }

    const nbGel = valeur(iso3, COUCHES[3]);
    html += bloc("Gels d'avoirs en France",
      nbGel === null ? vide("Donnée indisponible.") : `<p class="valeur">${fmtNb(nbGel, 0)} ${nbGel > 1 ? "entrées" : "entrée"}</p>`,
      nbGel ? `${gel.personnes || 0} personnes, ${gel.entites || 0} entités, ${gel.navires || 0} navires.` : null,
      "gels", "Personnes, entités ou navires visés par un gel d'avoirs en France, rattachés au pays par leur nationalité ou leur adresse. Ce n'est pas une mesure de la relation diplomatique.");

    document.getElementById("fiche-nom").textContent = f.properties.nom;
    document.getElementById("fiche-contenu").innerHTML = html;
    const fiche = document.getElementById("fiche");
    fiche.hidden = false;
    document.getElementById("fermer").focus();
    carte.setFilter("pays-choisi", ["==", ["get", "iso3"], iso3]);
  }

  function fermerFiche() {
    document.getElementById("fiche").hidden = true;
    if (carte) carte.setFilter("pays-choisi", ["==", ["get", "iso3"], ""]);
  }

  /* ---------- recherche ---------- */
  function initRecherche() {
    const liste = document.getElementById("liste-pays");
    const noms = {};
    geo.features.forEach(f => { if (!noms[f.properties.nom] && /^[A-Z]{3}$/.test(f.properties.iso3)) noms[f.properties.nom] = f.properties.iso3; });
    Object.keys(noms).sort((a, b) => a.localeCompare(b, "fr")).forEach(n => {
      const o = document.createElement("option");
      o.value = n;
      liste.appendChild(o);
    });
    document.getElementById("recherche").addEventListener("change", e => {
      const iso3 = noms[e.target.value];
      if (!iso3) return;
      const f = geo.features.find(x => x.properties.iso3 === iso3);
      const b = new maplibregl.LngLatBounds();
      const ajouter = c => (typeof c[0] === "number" ? b.extend(c) : c.forEach(ajouter));
      // On cadre sur le plus grand territoire du pays (évite de dézoomer sur tout le globe
      // pour un pays à îles lointaines ou à cheval sur l'antiméridien, comme la Russie).
      const polygones = f.geometry.type === "MultiPolygon" ? f.geometry.coordinates : [f.geometry.coordinates];
      const principal = polygones.reduce((a, p) => (p[0].length > a[0].length ? p : a));
      ajouter(principal);
      carte.fitBounds(b, { padding: 60, maxZoom: 5 });
      ouvrirFiche(iso3);
    });
  }

  /* ---------- démarrage ---------- */
  document.getElementById("fermer").addEventListener("click", fermerFiche);
  document.addEventListener("keydown", e => { if (e.key === "Escape") fermerFiche(); });
  construireBoutons();

  Promise.all([
    fetch("pays.geojson").then(r => r.json()),
    fetch("data/donnees.json", { cache: "no-store" }).then(r => (r.ok ? r.json() : null)).catch(() => null),
  ]).then(([g, d]) => {
    geo = g;
    donnees = d;
    if (d) document.getElementById("genere").textContent = `Dernière mise à jour du site : ${fmtDate(d.genere_le)}.`;
    afficherAlertes();
    initCarte();
    initRecherche();
  });
})();
