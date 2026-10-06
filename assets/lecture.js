/* Seven News — suivi de lecture (stocké dans le navigateur du lecteur, localStorage).
   Structure : { editions: { "AAAA-MM-JJ": { total, articles: { id: horodatage }, ouverte } },
                 jours: { "AAAA-MM-JJ": true }, mots: { id: "connu" } } */
const Lecture = (() => {
  const CLE = "sevennews:lecture:v1";
  const vide = () => ({ editions: {}, jours: {}, mots: {} });

  function charger() {
    try {
      const d = JSON.parse(localStorage.getItem(CLE));
      if (d && typeof d === "object") return Object.assign(vide(), d);
    } catch (e) { /* stockage indisponible : on repart de zéro */ }
    return vide();
  }
  let etat = charger();

  function sauver() {
    try { localStorage.setItem(CLE, JSON.stringify(etat)); } catch (e) { /* navigation privée : ignoré */ }
  }

  function aujourdHui() {
    const d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  function edition(date) {
    if (!etat.editions[date]) etat.editions[date] = { total: 0, articles: {}, ouverte: null };
    return etat.editions[date];
  }

  return {
    ouvrir(date, total) {
      const e = edition(date);
      e.total = total;
      if (!e.ouverte) e.ouverte = new Date().toISOString();
      sauver();
    },
    estLu(date, id) {
      return !!(etat.editions[date] && etat.editions[date].articles[id]);
    },
    basculer(date, id) {
      const e = edition(date);
      if (e.articles[id]) delete e.articles[id];
      else { e.articles[id] = new Date().toISOString(); etat.jours[aujourdHui()] = true; }
      sauver();
      return !!e.articles[id];
    },
    progression(date) {
      const e = etat.editions[date];
      if (!e || !e.total) return { lus: 0, total: e ? e.total : 0, pct: 0 };
      const lus = Object.keys(e.articles).length;
      return { lus, total: e.total, pct: Math.min(100, Math.round((lus / e.total) * 100)) };
    },
    statut(date) {
      const p = this.progression(date);
      if (!p.total || p.lus === 0) return etat.editions[date] && etat.editions[date].ouverte ? "ouverte" : "nonlu";
      return p.lus >= p.total ? "lu" : "encours";
    },
    motConnu(id) { return etat.mots[id] === "connu"; },
    basculerMot(id) {
      if (etat.mots[id]) delete etat.mots[id]; else etat.mots[id] = "connu";
      sauver();
      return !!etat.mots[id];
    },
    stats() {
      const eds = Object.keys(etat.editions);
      const editionsLues = eds.filter((d) => this.statut(d) === "lu").length;
      const articlesLus = eds.reduce((n, d) => n + Object.keys(etat.editions[d].articles).length, 0);
      // série : jours consécutifs avec au moins un article lu, en partant d'aujourd'hui (ou d'hier)
      let serie = 0;
      const jour = new Date();
      const cle = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
      if (!etat.jours[cle(jour)]) jour.setDate(jour.getDate() - 1);
      while (etat.jours[cle(jour)]) { serie++; jour.setDate(jour.getDate() - 1); }
      return { editionsLues, articlesLus, serie, motsConnus: Object.keys(etat.mots).length };
    },
    exporter() { return JSON.stringify(etat, null, 1); },
    importer(texte) {
      const d = JSON.parse(texte);
      if (!d || typeof d !== "object" || !d.editions) throw new Error("Fichier de lecture invalide");
      etat = Object.assign(vide(), d);
      sauver();
    },
  };
})();
