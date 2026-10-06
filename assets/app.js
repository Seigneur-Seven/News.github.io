/* Seven News — affichage d'une édition (index.html?date=AAAA-MM-JJ, sinon la dernière). */
(function () {
  "use strict";

  const $ = (sel, el = document) => el.querySelector(sel);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const JOURS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
  const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
  const dateLongue = (iso) => { const [a, m, j] = iso.split("-").map(Number); const d = new Date(a, m - 1, j); return `${JOURS[d.getDay()]} ${j} ${MOIS[m - 1]} ${a}`; };
  const dollars = (n) => (n == null ? "n. c." : Math.round(n).toLocaleString("fr-FR") + " $");
  const slugMot = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  let ED = null;          // édition affichée
  let ARTICLES = [];      // identifiants des rubriques comptées dans le suivi de lecture

  async function charger() {
    const params = new URLSearchParams(location.search);
    let date = params.get("date");
    try {
      if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
        const r = await fetch("api/latest.json", { cache: "no-cache" });
        if (!r.ok) throw new Error("latest.json introuvable (" + r.status + ")");
        date = (await r.json()).date;
      }
      const r2 = await fetch(`api/editions/${date}.json`, { cache: "no-cache" });
      if (!r2.ok) throw new Error(`Aucune édition pour le ${date}`);
      ED = await r2.json();
      rendre();
    } catch (e) {
      $("#contenu").innerHTML = `<div class="erreur"><b>Impossible de charger l'édition.</b> ${esc(e.message)}. ` +
        `Vérifiez que le dossier <code>api/</code> est bien publié, ou ouvrez les <a href="archives.html">archives</a>.</div>`;
    }
  }

  /* ---------- briques ---------- */
  const refs = (liste, prefixe) => (liste || []).map((n) => `<sup class="ref"><a href="#src-${prefixe}-${n}">[${n}]</a></sup>`).join("");
  const puces = (items) => `<ul class="puces">${items.map((t) => `<li>${t}</li>`).join("")}</ul>`;
  const bande = (titre, droite) => `<div class="bande"><h2>${esc(titre)}</h2><small>${esc(droite || "")}</small></div>`;
  const boutonLu = (id) => `<div class="lu-zone"><button class="btn petit" data-lu="${id}" aria-pressed="false">Marquer comme lu</button></div>`;
  const sources = (liste, prefixe) => `<ol class="sources-liste">${liste.map(([t, u], i) =>
    `<li id="src-${prefixe}-${i + 1}"><a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a></li>`).join("")}</ol>`;

  /* ---------- manchette ---------- */
  function manchette() {
    $("#bandeau-numero").textContent = `N° ${ED.numero} · Édition du soir`;
    $("#bandeau-date").textContent = "Paris, " + dateLongue(ED.date);
    const pdf = ED.pdf ? `<a href="${esc(ED.pdf)}" style="color:inherit">Télécharger le PDF</a>` : "Prix : 0 franc";
    $("#bandeau-pdf").innerHTML = pdf;
    document.title = `Seven News, n° ${ED.numero} du ${dateLongue(ED.date)}`;
    const themes = ["Culture", "Stages", "Mots", "Tech", "GitHub"].concat(ED.infos.map((i) => i.theme)).concat(["Sénat", ED.ville ? ED.ville.nom : ""]);
    $("#sommaire").textContent = themes.filter(Boolean).join(" · ");
    const liens = [["#une", "À la une"], ["#culture", "Culture"], ["#stages", "Stages"], ["#mots", "Mots"], ["#tech", "Tech"]];
    if (ED.github) liens.push(["#github", "GitHub"]);
    ED.infos.forEach((info, i) => liens.push([`#info-${i + 1}`, info.theme]));
    if (ED.senat) liens.push(["#senat", "Sénat"]);
    if (ED.ville) liens.push(["#ville", ED.ville.nom]);
    liens.push(["archives.html", "Archives"], ["api.html", "API"]);
    $("#nav").innerHTML = liens.map(([h, t]) => `<a href="${h}">${esc(t)}</a>`).join("");
  }

  /* ---------- rubriques ---------- */
  function une() {
    const tete = ED.infos[0];
    const autres = ED.infos.slice(1);
    return `<section class="rubrique" id="une">
      <div class="une">
        <div>
          <p class="etiq">${esc(tete.theme)}</p>
          <h3 class="gros"><a href="#info-1" style="color:inherit;text-decoration:none">${esc(tete.titre)}</a></h3>
          <p class="chapeau">${esc(tete.chapeau)}</p>
          <p class="texte-labeur lettrine">${esc(tete.contexte.join(" "))}</p>
          ${puces(tete.faits.slice(0, 4).map((f) => esc(f[0])))}
          <p><a href="#info-1">Lire la suite, le débat et les sources →</a></p>
        </div>
        <div class="une-liste">
          <p class="etiq encre">Aussi dans ce numéro</p>
          ${autres.map((a, i) => `<article><p class="etiq">${esc(a.theme)}</p><h4><a href="#info-${i + 2}">${esc(a.titre)}</a></h4><p style="margin:0;font-size:.92rem">${esc(a.chapeau)}</p></article>`).join("")}
          ${ED.senat ? `<article><p class="etiq">Sénat</p><h4><a href="#senat">${esc(ED.senat.titre)}</a></h4></article>` : ""}
          ${ED.ville ? `<article><p class="etiq">${esc(ED.ville.nom)}</p><h4><a href="#ville">${esc(ED.ville.actus[0].titre)}</a></h4></article>` : ""}
        </div>
      </div>
    </section>`;
  }

  function culture() {
    const c = ED.culture;
    return `<section class="rubrique" id="culture">${bande("Culture générale", c.blocs.length + " choses à savoir")}
      <blockquote class="citation">« ${esc(c.citation.texte)} »<cite>${esc(c.citation.auteur)}</cite></blockquote>
      <div class="colonnes c2">${c.blocs.map((b) => `<div><p class="etiq">${esc(b.rubrique)}</p><h4>${esc(b.titre)}</h4>${puces(b.points.map(esc))}</div>`).join("")}</div>
      ${boutonLu("culture")}</section>`;
  }

  function stages() {
    const o = ED.offres || [];
    const doms = [...new Set(o.map((x) => x.domaine))];
    return `<section class="rubrique" id="stages">${bande("Les offres de stage", o.length + " offres · triées par salaire")}
      <div class="filtres">
        <input id="filtre-texte" type="search" placeholder="Entreprise, poste, ville…" aria-label="Filtrer les offres">
        <select id="filtre-domaine" aria-label="Domaine"><option value="">Tous les domaines</option>${doms.map((d) => `<option>${esc(d)}</option>`).join("")}</select>
      </div>
      <div class="tableau-defile"><table class="stages"><thead><tr><th>N°</th><th>Entreprise</th><th>Poste</th><th>Lieu</th><th>$ / mois</th><th>Durée</th><th></th></tr></thead>
      <tbody id="stages-corps">${o.map((x, i) => `<tr data-dom="${esc(x.domaine)}" data-txt="${esc((x.entreprise + " " + x.poste + " " + x.ville).toLowerCase())}">
        <td>${i + 1}</td><td><b>${esc(x.entreprise)}</b></td><td>${esc(x.poste)}</td><td>${esc((x.ville || "").split(" (")[0])}</td>
        <td class="num">${dollars(x.salaire_mensuel_usd)}</td><td>${esc(x.duree_semaines)} sem.</td>
        <td><a href="${esc(x.lien)}" target="_blank" rel="noopener">Postuler</a></td></tr>`).join("")}</tbody></table></div>
      <p style="font-size:.85rem;color:var(--gris)">Montants bruts en dollars US (levels.fyi et offres publiées). Durée et visa J-1 à vérifier sur chaque offre.</p>
      ${boutonLu("stages")}</section>`;
  }

  function mots() {
    const m = ED.mots;
    const nbS = m.filter((x) => x.registre === "soutenu").length;
    return `<section class="rubrique" id="mots">${bande("Les mots du jour", `${nbS} soutenus · ${m.length - nbS} d'argot`)}
      <div class="colonnes c3">${m.map((x) => {
        const id = slugMot(x.mot);
        return `<div class="mot"><b>${esc(x.mot)}</b><span class="registre ${esc(x.registre)}">${esc(x.registre)}</span> <i>${esc(x.nature)}</i>
          <p style="margin:4px 0 0">${esc(x.definition)}</p><p class="ex">« ${esc(x.exemple)} »</p>
          <button class="btn petit" data-mot="${id}" aria-pressed="false" style="margin-top:6px">Je le connais</button></div>`;
      }).join("")}</div>${boutonLu("mots")}</section>`;
  }

  function tech() {
    return `<section class="rubrique" id="tech">${bande("Actualité tech", "l'essentiel, sources à l'appui")}
      <div class="colonnes c2">${ED.tech.map((t) => `<div><h4>${esc(t.titre)}</h4>${puces(t.points.map(esc))}
        <p style="margin:6px 0 0;font-family:var(--f-etiq);font-size:.9rem">${t.sources.map(([n, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(n)}</a>`).join(" · ")}</p></div>`).join("")}</div>
      ${boutonLu("tech")}</section>`;
  }

  function carteDepot([nom, etoiles, langage, maj, desc]) {
    return `<li><a href="https://github.com/${esc(nom)}" target="_blank" rel="noopener"><b>${esc(nom)}</b></a>
      <span style="font-family:var(--f-etiq);color:var(--rouge);font-weight:700"> ★ ${Number(etoiles).toLocaleString("fr-FR")}</span>
      <span style="font-family:var(--f-etiq);color:var(--gris)"> · ${esc(langage || "—")} · mis à jour le ${esc(maj)}</span><br>
      <span style="font-size:.92rem">${esc(desc || "")}</span></li>`;
  }

  function github() {
    const g = ED.github;
    return `<section class="rubrique" id="github">${bande("Dépôts GitHub à suivre", "actifs depuis un mois · relevé du " + g.date_releve)}
      <div class="colonnes c2" id="github-grille">${g.rubriques.map((r) => `<div><p class="etiq">${esc(r.titre)}</p><ul class="puces">${r.depots.map(carteDepot).join("")}</ul></div>`).join("")}</div>
      <p style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px">
        <button class="btn" id="github-direct">Actualiser en direct</button>
        <span id="github-etat" style="font-family:var(--f-etiq);font-size:.9rem;color:var(--gris)">Source : <a href="${esc(g.source[1])}" target="_blank" rel="noopener">${esc(g.source[0])}</a></span>
      </p>${boutonLu("github")}</section>`;
  }

  async function githubDirect() {
    const etat = $("#github-etat");
    etat.textContent = "Interrogation de l'API GitHub…";
    const depuis = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);
    const requetes = [["FPGA et matériel", `topic:fpga pushed:>${depuis}`], ["Robotique", `topic:robotics pushed:>${depuis}`],
      ["Embarqué", `topic:embedded pushed:>${depuis}`], ["Nouveaux du mois", `created:>${depuis}`]];
    try {
      const blocs = [];
      for (const [titre, q] of requetes) {
        const r = await fetch(`https://api.github.com/search/repositories?q=${encodeURIComponent(q)}&sort=stars&order=desc&per_page=5`);
        if (!r.ok) throw new Error(r.status === 403 ? "limite de requêtes GitHub atteinte, réessayez dans une minute" : "erreur " + r.status);
        const d = await r.json();
        blocs.push(`<div><p class="etiq">${esc(titre)}</p><ul class="puces">${d.items.map((x) => carteDepot([x.full_name, x.stargazers_count, x.language, (x.pushed_at || "").slice(0, 10), x.description])).join("")}</ul></div>`);
      }
      $("#github-grille").innerHTML = blocs.join("");
      etat.textContent = "Données en direct de l'API GitHub, " + new Date().toLocaleString("fr-FR") + ".";
    } catch (e) {
      etat.textContent = "Actualisation impossible : " + e.message + ". Le relevé du jour reste affiché.";
    }
  }

  function info(x, i) {
    const p = `info-${i}`;
    const avis = (a, titre, classe, etiq) => `<div class="boite ${classe}"><p class="etiq ${etiq}">${esc(titre)}</p><h4>${esc(a.qui)}</h4>
      ${puces((a.arguments || []).map(esc))}
      ${a.citation ? `<blockquote class="citation-avis">« ${esc(a.citation[0])} »${refs(a.citation[2], p)}<footer>— ${esc(a.citation[1])}</footer></blockquote>` : ""}</div>`;
    return `<section class="rubrique" id="${p}">${bande("Information · " + x.theme, `${i}/${ED.infos.length} · des faits, rien que des faits`)}
      <h3 class="gros">${esc(x.titre)}</h3><p class="chapeau">${esc(x.chapeau)}</p>
      <div class="une">
        <div>
          <p class="etiq gris">Le contexte</p>${puces(x.contexte.map(esc))}
          <p class="etiq encre" style="margin-top:12px">Les faits</p>${puces(x.faits.map((f) => esc(f[0]) + refs(f[1], p)))}
          ${x.zoom ? `<div class="boite trame" style="margin-top:12px"><p class="etiq">Zoom</p><h4>${esc(x.zoom.titre)}${refs(x.zoom.refs, p)}</h4>${puces(x.zoom.points.map(esc))}</div>` : ""}
        </div>
        <div class="pile">
          <div class="chiffres">${x.chiffres.map((c) => `<div class="chiffre"><b>${esc(c[0])}</b><span>${esc(c[1])}${refs(c[2], p)}</span></div>`).join("")}</div>
          <div><p class="etiq">Chronologie</p><table class="chrono">${x.chronologie.map(([d, t]) => `<tr><td>${esc(d)}</td><td>${esc(t)}</td></tr>`).join("")}</table></div>
        </div>
      </div>
      <h4 style="margin-top:18px;font-family:var(--f-titre);font-weight:400;font-size:1.6rem">Le débat</h4>
      <div class="colonnes c2" style="border-top:0">
        ${avis(x.gauche, x.gauche_titre || "Avis de gauche", "gauche", "")}
        ${avis(x.droite, x.droite_titre || "Avis de droite", "droite", "bleu")}
      </div>
      <div class="colonnes c2" style="border-top:0;margin-top:12px">
        <div class="boite incertain"><p class="etiq ocre">Ce qui reste incertain</p>${puces((x.incertain || []).map(esc))}</div>
        <div class="boite verif"><p class="etiq vert">Vérification</p>${puces(x.verification.map(([q, c, r]) => `<b>${esc(q)}</b> : ${esc(c)}${refs(r, p)}`))}</div>
      </div>
      <div style="margin-top:12px"><p class="etiq encre">Sources</p>${sources(x.sources, p)}</div>
      ${boutonLu(p)}</section>`;
  }

  function senat() {
    const s = ED.senat;
    const total = s.composition.reduce((n, g) => n + g[1], 0);
    return `<section class="rubrique" id="senat">${bande("Au Sénat", "les votes de la semaine")}
      <h3 class="gros">${esc(s.titre)}</h3><p class="chapeau">${esc(s.chapeau)}</p>
      <div class="une">
        <div class="pile">${s.votes.map((v) => `<div class="boite"><p class="etiq">${esc(v.date)}</p><h4>${esc(v.objet)}${refs(v.refs, "senat")}</h4>
          <p style="margin:0 0 4px"><b>Résultat :</b> ${esc(v.resultat)}</p><p style="margin:0 0 4px"><b>Pourquoi c'est important :</b> ${esc(v.importance)}</p>
          ${v.debat && v.debat.length ? puces(v.debat.map(esc)) : ""}</div>`).join("")}</div>
        <div class="pile">
          <div class="boite trame"><p class="etiq encre">Composition du Sénat</p><table class="chrono">${s.composition.map(([g, n]) => `<tr><td style="color:var(--encre);font-weight:400">${esc(g)}</td><td style="text-align:right">${n}</td></tr>`).join("")}
            <tr><td style="color:var(--encre)"><b>Total</b></td><td style="text-align:right"><b>${total}</b></td></tr></table></div>
          ${(s.a_venir || []).map((a) => `<div class="boite incertain"><p class="etiq ocre">À venir · ${esc(a.date)}</p><h4>${esc(a.objet)}${refs(a.refs, "senat")}</h4>
            <p style="margin:0 0 4px">${esc(a.contenu)}</p>${a.pour ? `<p style="margin:0 0 4px"><b style="color:var(--bleu)">Pour :</b> ${esc(a.pour)}</p>` : ""}
            ${a.contre ? `<p style="margin:0"><b style="color:var(--rouge)">Contre :</b> ${esc(a.contre)}</p>` : ""}</div>`).join("")}
        </div>
      </div>
      <div style="margin-top:12px"><p class="etiq encre">Sources</p>${sources(s.sources, "senat")}</div>
      ${boutonLu("senat")}</section>`;
  }

  function ville() {
    const v = ED.ville;
    return `<section class="rubrique" id="ville">${bande("À " + v.nom + " et alentour", "l'actu de la ville · quoi faire")}
      <div class="colonnes c2">${v.actus.map((a) => `<div><p class="etiq">Actualité</p><h4>${esc(a.titre)}</h4><p style="margin:0">${esc(a.texte)}</p>
        <p style="margin:6px 0 0;font-family:var(--f-etiq);font-size:.9rem"><a href="${esc(a.source[1])}" target="_blank" rel="noopener">${esc(a.source[0])}</a></p></div>`).join("")}</div>
      <div class="boite" style="margin-top:12px"><p class="etiq encre">Que faire cette semaine ?</p>
        <table class="chrono">${v.activites.map(([q, t, d]) => `<tr><td>${esc(q)}</td><td><b>${esc(t)}</b> — ${esc(d)}</td></tr>`).join("")}</table></div>
      <div class="boite trame" style="margin-top:12px"><p class="etiq vert">Aux alentours</p>${puces(v.alentours.map(([n, d]) => `<b>${esc(n)}</b> — ${esc(d)}`))}</div>
      <p style="font-family:var(--f-etiq);font-size:.9rem">Sources : ${v.sources.map(([t, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>`).join(" · ")}</p>
      ${boutonLu("ville")}</section>`;
  }

  /* ---------- assemblage et interactions ---------- */
  function rendre() {
    manchette();
    ARTICLES = ["culture", "stages", "mots", "tech"];
    if (ED.github) ARTICLES.push("github");
    ED.infos.forEach((_, i) => ARTICLES.push(`info-${i + 1}`));
    if (ED.senat) ARTICLES.push("senat");
    if (ED.ville) ARTICLES.push("ville");
    let h = une() + culture() + stages() + mots() + tech();
    if (ED.github) h += github();
    ED.infos.forEach((x, i) => { h += info(x, i + 1); });
    if (ED.senat) h += senat();
    if (ED.ville) h += ville();
    $("#contenu").innerHTML = h;
    Lecture.ouvrir(ED.date, ARTICLES.length);
    document.querySelectorAll("[data-lu]").forEach((b) => majBouton(b, Lecture.estLu(ED.date, b.dataset.lu)));
    document.querySelectorAll("[data-mot]").forEach((b) => majMot(b, Lecture.motConnu(b.dataset.mot)));
    majProgression();
    const filtre = () => {
      const t = $("#filtre-texte").value.trim().toLowerCase();
      const d = $("#filtre-domaine").value;
      document.querySelectorAll("#stages-corps tr").forEach((tr) => {
        tr.hidden = !((!t || tr.dataset.txt.includes(t)) && (!d || tr.dataset.dom === d));
      });
    };
    $("#filtre-texte").addEventListener("input", filtre);
    $("#filtre-domaine").addEventListener("change", filtre);
    const bg = $("#github-direct");
    if (bg) bg.addEventListener("click", githubDirect);
    if (location.hash) { const cible = document.getElementById(location.hash.slice(1)); if (cible) cible.scrollIntoView(); }
  }

  function majBouton(b, lu) { b.setAttribute("aria-pressed", lu ? "true" : "false"); b.textContent = lu ? "✓ Lu" : "Marquer comme lu"; }
  function majMot(b, connu) { b.setAttribute("aria-pressed", connu ? "true" : "false"); b.textContent = connu ? "✓ Je le connais" : "Je le connais"; }
  function majProgression() {
    const p = Lecture.progression(ED.date);
    $("#progression span").style.width = p.pct + "%";
    $("#progression-texte").textContent = `Lecture : ${p.lus} / ${p.total} rubriques (${p.pct} %)`;
  }

  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-lu]");
    if (b && ED) { majBouton(b, Lecture.basculer(ED.date, b.dataset.lu)); majProgression(); return; }
    const m = e.target.closest("[data-mot]");
    if (m) majMot(m, Lecture.basculerMot(m.dataset.mot));
  });

  charger();
})();
