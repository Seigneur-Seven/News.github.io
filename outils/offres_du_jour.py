#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEVEN NEWS — sélection des offres de stage du jour (sans doublon)

Usage : python offres_du_jour.py deja_vus.json offres.json
  deja_vus.json : liste JSON des identifiants, clés et liens déjà publiés (peut être [] ou absent)
  offres.json   : sortie, les 50 offres retenues (format attendu par seven_news.py)
"""
import datetime
import json
import os
import re
import sys
import unicodedata
import urllib.request

URL_OFFRES = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
SAISON = "Summer 2027"
NB_OFFRES = 50


def slug(texte):
    t = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode().lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", t)).strip("-")[:120]


# Salaires de stage relevés sur levels.fyi (USD bruts / mois, temps plein).
# Format : (motif entreprise, motif dans l'intitulé, lieux concernés ou None, valeur)
# valeur = (usd_par_mois, texte d'origine, durée en semaines, source) ou None pour écarter.
# L'ordre compte : la première règle qui correspond gagne. Mets cette table à jour de temps en temps.
SALAIRES = [
    ("optiver", "fpga", None, (34600, "80 000 $ pour l'été (base + prime)", 10, "Optiver")),
    ("optiver", "", ("London",), (17700, "≈ 102 $/h (donnée Londres)", 10, "levels.fyi")),
    ("optiver", "", None, (26000, "150 $/h", 10, "levels.fyi")),
    ("jane street", "", ("London",), (17682, "102 $/h", 10, "levels.fyi")),
    ("jane street", "", None, (25000, "144 $/h", 10, "levels.fyi")),
    ("susquehanna", "", ("London", "Dublin"), (9800, "≈ 56 $/h (donnée Dublin)", 10, "levels.fyi")),
    ("susquehanna", "", None, (26000, "150 $/h", 10, "levels.fyi")),
    ("imc", "", None, (25000, "≈ 5 800 $/semaine", 10, "Young and Calculated")),
    ("five rings", "", None, (24917, "143,75 $/h", 10, "levels.fyi")),
    ("citadel", "", None, (20800, "≈ 120 $/h", 10, "levels.fyi")),
    ("virtu", "", None, (21667, "125 $/h", 10, "levels.fyi")),
    ("tower research", "", ("Montreal", "London"), None),
    ("tower research", "", None, (19500, "112,50 $/h", 10, "levels.fyi")),
    ("two sigma", "", None, (18200, "105 $/h", 12, "levels.fyi")),
    ("hudson river", "", None, (17753, "≈ 102 $/h", 10, "Career Principles")),
    ("chicago trading", "", ("London",), None),
    ("chicago trading", "", None, (15600, "90 $/h", 10, "levels.fyi")),
    ("akuna", "", None, (12567, "72,50 $/h", 10, "levels.fyi")),
    ("waymo", "", None, (12133, "70 $/h", 12, "levels.fyi")),
    ("google", "", ("Canada", "London", "India"), None),
    ("google", "", None, (11750, "67,79 $/h", 12, "levels.fyi")),
    ("nvidia", "hardware", None, (11613, "67 $/h (master) + logement", 12, "levels.fyi")),
    ("nvidia", "", None, (12307, "71 $/h", 12, "levels.fyi")),
    ("apple", "hardware", None, (9880, "57 $/h (master)", 12, "levels.fyi")),
    ("apple", "", None, (8493, "49 $/h", 12, "levels.fyi")),
    ("verkada", "", None, (11267, "65 $/h", 12, "levels.fyi")),
    ("marvell", "", ("Canada",), None),
    ("marvell", "", ("Santa Clara",), (10920, "63 $/h", 12, "levels.fyi")),
    ("marvell", "", None, (6219, "35,88 $/h", 12, "levels.fyi")),
    ("tesla", "", None, (10208, "58,89 $/h", 12, "levels.fyi")),
    ("amazon", "", ("Canada",), (8401, "48,47 $/h", 12, "levels.fyi")),
    ("amazon", "", None, (10513, "60,65 $/h", 12, "levels.fyi")),
    ("qualcomm", "", ("Canada",), None),
    ("qualcomm", "", None, (9360, "54 $/h", 12, "levels.fyi")),
    ("intel", "", None, (7700, "44,42 $/h", 12, "levels.fyi")),
    ("amd", "", ("Canada",), (4323, "24,94 $/h", 12, "levels.fyi")),
    ("amd", "", None, (7280, "42 $/h", 12, "levels.fyi")),
]

# Employeurs qui exigent quasi systématiquement la nationalité américaine ou une habilitation défense.
EMPLOYEURS_EXCLUS = re.compile(
    r"\b(rtx|raytheon|lockheed|northrop|general dynamics|booz allen|caci|leidos|peraton|l3harris|bae systems|"
    r"johns hopkins applied physics|sierra nevada|textron|spacex|anduril|saab|innovative defense|"
    r"collins aerospace|huntington ingalls|mitre|sandia|lawrence livermore|los alamos)\b", re.I)
SPONSOR_EXCLUS = {"U.S. Citizenship is Required", "Does Not Offer Sponsorship"}

# Intitulés hors de tes domaines (trading pur, recherche quant, doctorat, MBA, etc.)
INTITULES_EXCLUS = re.compile(
    r"phd|mba|quantitative research|quant research|researcher|trader|trading intern|quant trading|"
    r"quantitative intern|risk|operations|analyst|portfolio|people products|labeling|commercialization|"
    r"sales|marketing|product manag|designer|recruit|finance intern|accounting|legal|business", re.I)
INTITULES_OK = re.compile(
    r"fpga|asic|hardware|embedded|firmware|robot|electrical|silicon|rtl|verification|chip|autonom|"
    r"controls|mechatronic|network|low.?latency|c\+\+|software|swe|developer|engineer|systems|vlsi|"
    r"analog|validation|perception|motion|kernel|compiler|infrastructure", re.I)
RE_HW = re.compile(r"fpga|asic|hardware|silicon|vlsi|verification|dft|analog|electrical|serdes|validation|"
                   r"package|physical design|rtl|chip", re.I)
RE_EMB = re.compile(r"embedded|firmware|robot|optimus|autonom|vehicle|systems engineer|controls|"
                    r"mechatronic|perception|motion|drone|avionic", re.I)


# ======================================================================
# 1-4. COLLECTE, FILTRAGE, CLASSEMENT
# ======================================================================
def salaire_pour(entreprise, intitule, lieux):
    for motif_co, motif_titre, lieux_regle, valeur in SALAIRES:
        if motif_co in entreprise.lower() and motif_titre in intitule.lower():
            if lieux_regle and not any(l in lieux for l in lieux_regle):
                continue
            return valeur if valeur else "exclu"
    return None


def pays_de(ville):
    if "UK" in ville or "London" in ville:
        return "Royaume-Uni"
    if "Dublin" in ville or "Ireland" in ville:
        return "Irlande"
    if "Canada" in ville:
        return "Canada"
    if "Remote" in ville:
        return "À distance"
    return "États-Unis"


def selectionner(brutes, deja_vus, date_iso, nb=NB_OFFRES):
    vus = set(deja_vus)
    retenues, cles = {}, set()
    for x in brutes:
        if not (x.get("active") and x.get("is_visible", True)):
            continue
        if SAISON not in (x.get("terms") or []):
            continue
        if x.get("sponsorship") in SPONSOR_EXCLUS:
            continue
        co, titre = x.get("company_name", ""), x.get("title", "")
        if EMPLOYEURS_EXCLUS.search(co) or INTITULES_EXCLUS.search(titre) or not INTITULES_OK.search(titre):
            continue
        lieux = ";".join(x.get("locations") or [])
        sal = salaire_pour(co, titre, lieux)
        if sal == "exclu":
            continue
        co_propre = re.sub(r"\s*\(.*?\)|\s+University$", "", co).strip()
        ville = (x.get("locations") or ["?"])[0]
        id_doc = slug(f"{co_propre}-{titre}-{ville}")
        url = x.get("url", "")
        if id_doc in vus or url in vus:
            continue
        cle = co_propre.lower() + "|" + re.sub(r"\s*-?\s*summer 2027", "", titre.lower()).strip()
        if cle in cles or cle in vus:
            continue
        cles.add(cle)
        domaine = ("FPGA / hardware" if RE_HW.search(titre)
                   else "Robotique / embarqué" if RE_EMB.search(titre) else "Logiciel")
        if sal:
            usd, txt, duree, source = sal
        else:
            usd, txt, duree, source = None, "Salaire non publié", 12, "SimplifyJobs"
        nb_autres = len(x.get("locations") or []) - 1
        retenues[id_doc] = {
            "id": id_doc, "cle": cle, "entreprise": co_propre, "poste": titre, "pays": pays_de(ville),
            "ville": ville + (f" (+{nb_autres})" if nb_autres > 0 else ""), "domaine": domaine,
            "duree_semaines": duree, "duree_a_verifier": True, "salaire_mensuel_usd": usd,
            "salaire_texte": txt, "lien": url, "source": source, "date_ajout": date_iso,
            "publie_le": x.get("date_posted", 0),
        }
    # salaires connus d'abord (du plus haut au plus bas), puis les plus récentes sans salaire publié
    liste = sorted(retenues.values(),
                   key=lambda o: (o["salaire_mensuel_usd"] is None, -(o["salaire_mensuel_usd"] or 0),
                                  -o["publie_le"]))
    return liste[:nb]




if __name__ == "__main__":
    vus = []
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        vus = json.load(open(sys.argv[1], encoding="utf-8"))
    with urllib.request.urlopen(URL_OFFRES, timeout=120) as r:
        brutes = json.load(r)
    date_iso = datetime.date.today().isoformat()
    offres = selectionner(brutes, vus, date_iso)
    sortie = sys.argv[2] if len(sys.argv) > 2 else "offres.json"
    json.dump(offres, open(sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(offres)} offres écrites dans {sortie}")
