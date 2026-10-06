#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEVEN NEWS — publie une édition dans le site (et donc dans l'API).

Usage : python outils/publier_site.py contenu.json offres.json Seven-News-AAAA-MM-JJ.pdf [dossier_du_site]

Écrit :
  api/editions/AAAA-MM-JJ.json  (contenu + offres + liens)
  pdf/Seven-News-AAAA-MM-JJ.pdf
  api/editions.json             (index, du plus récent au plus ancien)
  api/latest.json               (dernière édition)
"""
import datetime
import json
import os
import shutil
import sys

try:
    from zoneinfo import ZoneInfo
    PARIS = ZoneInfo("Europe/Paris")
except Exception:  # Python < 3.9
    PARIS = None


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    contenu = json.load(open(sys.argv[1], encoding="utf-8"))
    offres = json.load(open(sys.argv[2], encoding="utf-8")) if sys.argv[2] != "-" else []
    if isinstance(offres, dict):
        offres = offres.get("offres", [])
    pdf_source = sys.argv[3]
    site = sys.argv[4] if len(sys.argv) > 4 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    date = contenu["date"]
    os.makedirs(os.path.join(site, "api", "editions"), exist_ok=True)
    os.makedirs(os.path.join(site, "pdf"), exist_ok=True)

    nom_pdf = f"Seven-News-{date}.pdf"
    shutil.copyfile(pdf_source, os.path.join(site, "pdf", nom_pdf))

    edition = dict(contenu)
    edition["offres"] = offres
    edition["pdf"] = f"pdf/{nom_pdf}"
    edition["json"] = f"api/editions/{date}.json"
    chemin_ed = os.path.join(site, "api", "editions", f"{date}.json")
    with open(chemin_ed, "w", encoding="utf-8") as f:
        json.dump(edition, f, ensure_ascii=False, indent=1)

    maintenant = datetime.datetime.now(PARIS) if PARIS else datetime.datetime.now()
    chemin_index = os.path.join(site, "api", "editions.json")
    index = {"editions": []}
    if os.path.exists(chemin_index):
        index = json.load(open(chemin_index, encoding="utf-8"))
    index["editions"] = [e for e in index.get("editions", []) if e.get("date") != date]
    index["editions"].append({
        "date": date,
        "numero": contenu.get("numero"),
        "titres": [i["titre"] for i in contenu.get("infos", [])],
        "themes": [i["theme"] for i in contenu.get("infos", [])],
        "nb_offres": len(offres),
        "json": f"api/editions/{date}.json",
        "pdf": f"pdf/{nom_pdf}",
    })
    index["editions"].sort(key=lambda e: e["date"], reverse=True)
    index["mise_a_jour"] = maintenant.isoformat(timespec="seconds")
    with open(chemin_index, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)

    derniere = index["editions"][0]
    with open(os.path.join(site, "api", "latest.json"), "w", encoding="utf-8") as f:
        json.dump({"date": derniere["date"], "numero": derniere["numero"], "json": derniere["json"],
                   "pdf": derniere["pdf"], "mise_a_jour": index["mise_a_jour"]}, f, ensure_ascii=False, indent=1)
    print(f"Édition du {date} publiée dans {site} ({len(index['editions'])} édition(s) au total).")


if __name__ == "__main__":
    main()
