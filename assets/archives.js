/* Seven News — archives : historique des éditions et suivi de lecture. */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const JOURS = ["dim.", "lun.", "mar.", "mer.", "jeu.", "ven.", "sam."];
  const MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  const court = (iso) => { const [a, m, j] = iso.split("-").map(Number); const d = new Date(a, m - 1, j); return `${JOURS[d.getDay()]} ${j} ${MOIS[m - 1]} ${a}`; };
  let EDITIONS = [];

  function stats() {
    const s = Lecture.stats();
    $("#stat-editions").textContent = s.editionsLues;
    $("#stat-articles").textContent = s.articlesLus;
    $("#stat-serie").textContent = s.serie;
    $("#stat-mots").textContent = s.motsConnus;
  }

  function liste() {
    const f = $("#filtre-statut").value;
    const t = $("#filtre-texte").value.trim().toLowerCase();
    const lignes = EDITIONS.filter((e) => {
      const st = Lecture.statut(e.date);
      const okStatut = !f || (f === "nonlu" ? (st === "nonlu" || st === "ouverte") : st === f);
      const okTexte = !t || (e.titres || []).join(" ").toLowerCase().includes(t) || e.date.includes(t);
      return okStatut && okTexte;
    });
    $("#liste").innerHTML = lignes.length ? lignes.map((e) => {
      const st = Lecture.statut(e.date);
      const p = Lecture.progression(e.date);
      const lib = st === "lu" ? "Lu" : st === "encours" ? `En cours · ${p.pct} %` : st === "ouverte" ? "Ouvert" : "Non lu";
      const cls = st === "lu" ? "lu" : st === "encours" || st === "ouverte" ? "encours" : "nonlu";
      return `<li><span class="date">N° ${esc(e.numero)}<br><small style="font-family:var(--f-etiq);font-size:.85rem">${court(e.date)}</small></span>
        <span><a href="./?date=${esc(e.date)}"><b>${esc((e.titres || [])[0] || "Édition du " + e.date)}</b></a><br>
        <span class="titres">${esc((e.titres || []).slice(1).join(" · "))}</span><br>
        <span style="font-family:var(--f-etiq);font-size:.85rem">${e.pdf ? `<a href="${esc(e.pdf)}">PDF</a> · ` : ""}<a href="${esc(e.json)}">JSON</a></span></span>
        <span class="statut ${cls}">${lib}</span></li>`;
    }).join("") : `<li><span></span><span>Aucune édition ne correspond à ce filtre.</span><span></span></li>`;
  }

  async function charger() {
    try {
      const r = await fetch("api/editions.json", { cache: "no-cache" });
      if (!r.ok) throw new Error("api/editions.json introuvable (" + r.status + ")");
      EDITIONS = (await r.json()).editions || [];
      EDITIONS.sort((a, b) => b.date.localeCompare(a.date));
      liste();
    } catch (e) {
      $("#liste").innerHTML = `<li><span></span><span class="erreur">Impossible de charger l'historique : ${esc(e.message)}</span><span></span></li>`;
    }
    stats();
  }

  $("#filtre-statut").addEventListener("change", liste);
  $("#filtre-texte").addEventListener("input", liste);
  $("#sauvegarder").addEventListener("click", async () => {
    const txt = Lecture.exporter();
    $("#zone-sauvegarde").value = txt;
    $("#zone-sauvegarde").hidden = false;
    try { await navigator.clipboard.writeText(txt); $("#msg-sauvegarde").textContent = "Sauvegarde copiée : colle-la sur ton autre appareil, puis « Restaurer »."; }
    catch (e) { $("#zone-sauvegarde").select(); $("#msg-sauvegarde").textContent = "Copie automatique refusée : le texte est sélectionné ci-dessous, copie-le à la main."; }
  });
  $("#restaurer").addEventListener("click", () => {
    const z = $("#zone-sauvegarde");
    if (z.hidden || !z.value.trim()) { z.hidden = false; z.value = ""; z.focus(); $("#msg-sauvegarde").textContent = "Colle ta sauvegarde dans le cadre, puis clique à nouveau sur « Restaurer »."; return; }
    try { Lecture.importer(z.value); $("#msg-sauvegarde").textContent = "Suivi de lecture restauré."; liste(); stats(); }
    catch (e) { $("#msg-sauvegarde").textContent = "Restauration impossible : " + e.message + "."; }
  });
  charger();
})();
