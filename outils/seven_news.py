#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEVEN NEWS — mise en page du journal en PDF (style presse années 50, petits blocs)

  p.1    Culture générale (sous le grand titre)
  p.2    Offres de stage
  p.3    Les mots du jour (soutenu / argot)
  p.4    Actualité tech
  p.5+   Information : un sujet par page (contexte, faits sourcés, chiffres, chronologie,
         arguments de gauche et de droite, zoom, incertitudes, vérification, sources numérotées)

Usage : python seven_news.py contenu.json offres.json sortie.pdf [dossier_polices]
Dépendances : pip install reportlab   (les polices sont téléchargées automatiquement si absentes)
"""
import datetime
import json
import os
import random
import sys
import urllib.request
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

NOM_JOURNAL = "Seven News"
DEVISE = ["« Les faits d'abord,", "l'opinion ensuite. »"]
DEDICACE = ["Tirage spécial", "pour M. Simon"]

# ---------------------------------------------------------------- polices
URL_POLICES = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
POLICES = {
    "Gothique": "unifrakturmaguntia/UnifrakturMaguntia-Book.ttf",
    "Titre": "bebasneue/BebasNeue-Regular.ttf",
    "Texte": "ptserif/PT_Serif-Web-Regular.ttf",
    "Texte-Gras": "ptserif/PT_Serif-Web-Bold.ttf",
    "Texte-Italique": "ptserif/PT_Serif-Web-Italic.ttf",
    "Etiquette": "ptsansnarrow/PT_Sans-Narrow-Web-Bold.ttf",
    "Etroit": "ptsansnarrow/PT_Sans-Narrow-Web-Regular.ttf",
}


def charger_polices(dossier):
    os.makedirs(dossier, exist_ok=True)
    for nom, chemin in POLICES.items():
        dest = os.path.join(dossier, os.path.basename(chemin))
        if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
            urllib.request.urlretrieve(URL_POLICES + chemin, dest)
        pdfmetrics.registerFont(TTFont(nom, dest))
    pdfmetrics.registerFontFamily("Texte", normal="Texte", bold="Texte-Gras", italic="Texte-Italique",
                                  boldItalic="Texte-Gras")


# ---------------------------------------------------------------- couleurs & mesures
PAPIER = colors.HexColor("#F3EBD8")
ENCRE = colors.HexColor("#1C1A16")
GRIS = colors.HexColor("#5C564B")
TRAME = colors.HexColor("#E6DBC0")
ROUGE = colors.HexColor("#9B2C20")      # gauche / accents
BLEU = colors.HexColor("#1F3E66")       # droite
VERT = colors.HexColor("#2F5D3A")       # vérification
ORANGE = colors.HexColor("#8A5A12")     # incertitudes
W, H = A4
M = 13 * mm
LARG = W - 2 * M
GAP = 4 * mm
DEMI = (LARG - GAP) / 2

JOURS = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"]
MOIS = ["JANVIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN", "JUILLET", "AOÛT", "SEPTEMBRE",
        "OCTOBRE", "NOVEMBRE", "DÉCEMBRE"]


def date_longue(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"


def dollars(n):
    return f"{int(round(n)):,}".replace(",", " ") + " $"


# ---------------------------------------------------------------- styles
S = {}


def st(nom, **kw):
    base = dict(fontName="Texte", fontSize=9.5, leading=12.5, textColor=ENCRE)
    base.update(kw)
    return ParagraphStyle(nom, **base)


def init_styles():
    S.update({
        "bande": st("bande", fontName="Titre", fontSize=19, leading=21, textColor=PAPIER),
        "bande_d": st("bande_d", fontName="Etiquette", fontSize=9, leading=21, textColor=PAPIER, alignment=TA_RIGHT),
        "etiq": st("etiq", fontName="Etiquette", fontSize=8, leading=10, textColor=ROUGE),
        "btitre": st("btitre", fontName="Texte-Gras", fontSize=11.5, leading=14),
        "puce": st("puce", fontSize=9.6, leading=12.6, leftIndent=9, bulletIndent=0, spaceAfter=2),
        "puce_l": st("puce_l", fontSize=10.4, leading=13.8, leftIndent=10, bulletIndent=0, spaceAfter=3),
        "petit": st("petit", fontSize=8.6, leading=11, textColor=GRIS),
        "lien": st("lien", fontName="Etroit", fontSize=9, leading=11.5, textColor=ROUGE),
        "grand_titre": st("grand_titre", fontName="Titre", fontSize=36, leading=36),
        "chapeau": st("chapeau", fontName="Texte-Italique", fontSize=12, leading=15.5, textColor=GRIS),
        "chiffre": st("chiffre", fontName="Titre", fontSize=30, leading=30, alignment=TA_CENTER),
        "chiffre_l": st("chiffre_l", fontName="Etroit", fontSize=8.6, leading=10.5, alignment=TA_CENTER,
                        textColor=GRIS),
        "chrono_d": st("chrono_d", fontName="Etiquette", fontSize=8.6, leading=11, textColor=ROUGE),
        "chrono_t": st("chrono_t", fontSize=8.8, leading=11.2),
        "citation": st("citation", fontName="Texte-Italique", fontSize=12.5, leading=16, alignment=TA_CENTER),
        "citation_a": st("citation_a", fontName="Etiquette", fontSize=8.5, leading=11, alignment=TA_CENTER,
                         textColor=GRIS),
        "cit_avis": st("cit_avis", fontName="Texte-Italique", fontSize=11, leading=14.5),
        "cit_auteur": st("cit_auteur", fontName="Etiquette", fontSize=8, leading=10, textColor=GRIS),
        "mot": st("mot", fontName="Texte-Gras", fontSize=11.5, leading=13),
        "def": st("def", fontSize=9.2, leading=11.6),
        "ex": st("ex", fontName="Texte-Italique", fontSize=8.8, leading=11, textColor=GRIS),
        "th": st("th", fontName="Etiquette", fontSize=7.8, leading=9.5, textColor=PAPIER),
        "td": st("td", fontName="Etroit", fontSize=7.9, leading=9.2),
        "td_b": st("td_b", fontName="Etiquette", fontSize=7.9, leading=9.2),
        "td_r": st("td_r", fontName="Etiquette", fontSize=7.9, leading=9.2, alignment=TA_RIGHT),
        "td_l": st("td_l", fontName="Etiquette", fontSize=7.9, leading=9.2, textColor=ROUGE),
        "source_n": st("source_n", fontName="Etroit", fontSize=9.6, leading=12, textColor=ENCRE),
    })


def P(txt, style, **kw):
    return Paragraph(txt, S[style], **kw)


def T(txt):
    return escape(str(txt))


def refs(liste):
    """[1, 3] -> exposant « [1][3] » en rouge."""
    if not liste:
        return ""
    return " <font name='Etiquette' size='7.5' color='#9B2C20'>" + "".join(f"[{n}]" for n in liste) + "</font>"


# ---------------------------------------------------------------- fond de page
def fond(c):
    c.setFillColor(PAPIER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    if not getattr(c, "_grain", False):
        c.beginForm("grain")
        rnd = random.Random(7)
        c.setFillColor(TRAME)
        for _ in range(1100):
            c.circle(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.15, 0.5), stroke=0, fill=1)
        c.endForm()
        c._grain = True
    c.doForm("grain")
    c.setStrokeColor(colors.HexColor("#DACBA6"))
    c.setLineWidth(6)
    c.rect(3, 3, W - 6, H - 6, stroke=1, fill=0)


def filet_double(c, y):
    c.setStrokeColor(ENCRE)
    c.setLineWidth(1.6)
    c.line(M, y, W - M, y)
    c.setLineWidth(0.5)
    c.line(M, y - 2.6, W - M, y - 2.6)


def pied(c, doc):
    c.setStrokeColor(ENCRE)
    c.setLineWidth(0.5)
    c.line(M, M + 9, W - M, M + 9)
    c.setFont("Etroit", 7.5)
    c.setFillColor(GRIS)
    c.drawString(M, M + 1, f"{NOM_JOURNAL} · Faits recoupés, sources numérotées en bas de page · "
                           "Imprimé par Claude pour M. Simon")
    c.drawRightString(W - M, M + 1, f"Page {doc.page}")


def page_une(c, doc):
    ed = doc.ed
    c.saveState()
    fond(c)
    top = H - M
    c.setFillColor(ENCRE)
    c.setFont("Etiquette", 8)
    c.drawString(M, top - 6, f"N° {ed['numero']}  ·  ÉDITION DU SOIR")
    c.drawCentredString(W / 2, top - 6, "PARIS, " + date_longue(ed["date"]))
    c.drawRightString(W - M, top - 6, "PRIX : 0 FRANC")
    filet_double(c, top - 10)
    c.setFont("Gothique", 50)
    c.drawCentredString(W / 2, top - 52, NOM_JOURNAL)
    c.setFont("Texte-Italique", 7.6)
    for i, l in enumerate(DEVISE):
        c.drawString(M, top - 32 - i * 9, l)
    for i, l in enumerate(DEDICACE):
        c.drawRightString(W - M, top - 32 - i * 9, l)
    filet_double(c, top - 62)
    c.setFont("Etiquette", 8)
    themes = "  ·  ".join(["CULTURE", "STAGES", "MOTS", "TECH", "GITHUB"] + [i["theme"].upper() for i in ed["infos"]]
                          + ["SÉNAT", ed.get("ville", {}).get("nom", "VILLE").upper()])
    c.drawCentredString(W / 2, top - 72, themes)
    c.setLineWidth(0.5)
    c.line(M, top - 76, W - M, top - 76)
    pied(c, doc)
    c.restoreState()


def page_interieure(c, doc):
    ed = doc.ed
    c.saveState()
    fond(c)
    top = H - M
    c.setFillColor(ENCRE)
    c.setFont("Gothique", 22)
    c.drawString(M, top - 17, NOM_JOURNAL)
    c.setFont("Etiquette", 8)
    c.drawRightString(W - M, top - 8, date_longue(ed["date"]))
    c.drawRightString(W - M, top - 18, f"N° {ed['numero']}")
    filet_double(c, top - 23)
    pied(c, doc)
    c.restoreState()


# ---------------------------------------------------------------- briques
def bande(gauche, droite=""):
    t = Table([[P(T(gauche), "bande"), P(T(droite), "bande_d")]], colWidths=[LARG * 0.62, LARG * 0.38])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ENCRE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def bloc(contenu, largeur, accent=ENCRE, fond_bloc=None, epais=0.8, haut_accent=False):
    t = Table([[contenu]], colWidths=[largeur])
    style = [("BOX", (0, 0), (-1, -1), epais, ENCRE),
             ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
             ("VALIGN", (0, 0), (-1, -1), "TOP")]
    if fond_bloc:
        style.append(("BACKGROUND", (0, 0), (-1, -1), fond_bloc))
    if haut_accent:
        style.append(("LINEABOVE", (0, 0), (-1, 0), 3, accent))
    t.setStyle(TableStyle(style))
    return t


def puces(points, style="puce"):
    return [P(T(p), style, bulletText="•") for p in points]


def etiquette(txt, couleur=ROUGE):
    return Paragraph(T(txt.upper()), ParagraphStyle("e", parent=S["etiq"], textColor=couleur))


def nu(t):
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def deux_colonnes(gauche, droite, lg=DEMI, ld=DEMI):
    return nu(Table([[gauche, "", droite]], colWidths=[lg, GAP, ld]))


def grille(cellules, cols=2, largeur_col=DEMI, bas=GAP):
    lignes = [cellules[i:i + cols] for i in range(0, len(cellules), cols)]
    data = []
    for l in lignes:
        l = l + [""] * (cols - len(l))
        r = []
        for i, cel in enumerate(l):
            r.append(cel)
            if i < cols - 1:
                r.append("")
        data.append(r)
    widths = []
    for i in range(cols):
        widths.append(largeur_col)
        if i < cols - 1:
            widths.append(GAP)
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), bas),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def lien(txt, url, style="lien"):
    return P(f"<a href=\"{T(url)}\" color=\"#9B2C20\"><u>{T(txt)}</u></a>", style)


# ---------------------------------------------------------------- pages
def page_culture(ed):
    cu = ed["culture"]
    fl = [bande("Culture générale", f"{len(cu['blocs'])} choses à savoir"), Spacer(1, 6)]
    cit = cu["citation"]
    fl.append(bloc([P("« " + T(cit["texte"]) + " »", "citation"), Spacer(1, 2), P(T(cit["auteur"]), "citation_a")],
                   LARG, fond_bloc=TRAME, epais=1.2))
    fl.append(Spacer(1, GAP))
    cel = [bloc([etiquette(b["rubrique"]), P(T(b["titre"]), "btitre"), Spacer(1, 3)] + puces(b["points"], "puce_l"),
                DEMI) for b in cu["blocs"]]
    fl.append(grille(cel))
    return fl


def page_offres(offres):
    fl = [bande("Les offres de stage", f"{len(offres)} offres · triées par salaire"), Spacer(1, 5)]
    data = [[P(x, "th") for x in ["N°", "ENTREPRISE", "POSTE", "LIEU", "$ / MOIS", "DURÉE", "LIEN"]]]
    for i, o in enumerate(offres, 1):
        poste = o["poste"].replace(" - Summer 2027", "")
        poste = poste if len(poste) <= 52 else poste[:50] + "…"
        lieu = o.get("ville", "").split(" (")[0]
        lieu = lieu if len(lieu) <= 22 else lieu[:21] + "…"
        sal = dollars(o["salaire_mensuel_usd"]) if o.get("salaire_mensuel_usd") else "n. c."
        data.append([P(str(i), "td_b"), P(T(o["entreprise"][:24]), "td_b"), P(T(poste), "td"), P(T(lieu), "td"),
                     P(T(sal), "td_r"), P(T(f"{o.get('duree_semaines', '?')} sem."), "td"),
                     P(f"<a href=\"{T(o.get('lien', ''))}\" color=\"#9B2C20\"><u>Postuler</u></a>", "td_l")])
    larg = [16, 96, 170, 92, 54, 40, 0]
    larg[-1] = LARG - sum(larg)
    t = Table(data, colWidths=larg, repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), ENCRE), ("LINEBELOW", (0, 1), (-1, -1), 0.25, GRIS),
             ("BOX", (0, 0), (-1, -1), 0.8, ENCRE),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
             ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    style += [("BACKGROUND", (0, r), (-1, r), TRAME) for r in range(2, len(data), 2)]
    t.setStyle(TableStyle(style))
    fl += [t, Spacer(1, 4),
           P("Montants bruts en dollars US (levels.fyi et offres publiées). Stages d'été américains : 10 à 12 "
             "semaines, durée et visa J-1 à vérifier sur l'offre.", "petit")]
    return fl


def page_mots(ed):
    mots = ed["mots"]
    nb_s = sum(1 for m in mots if m["registre"] == "soutenu")
    fl = [bande("Les mots du jour", f"{nb_s} soutenus · {len(mots) - nb_s} d'argot"), Spacer(1, 6)]
    cel = []
    for m in mots:
        couleur = BLEU if m["registre"] == "soutenu" else ROUGE
        tete = (f"{T(m['mot'])}  <font name='Etiquette' size='7.5' color='{couleur.hexval()}'>"
                f"{T(m['registre'].upper())}</font>  <font name='Texte-Italique' size='8' color='#5C564B'>"
                f"{T(m['nature'])}</font>")
        cel.append(bloc([P(tete, "mot"), P(T(m["definition"]), "def"), P("« " + T(m["exemple"]) + " »", "ex")],
                        DEMI, accent=couleur, haut_accent=True, epais=0.5))
    fl.append(grille(cel, bas=3))
    return fl


def page_tech(ed):
    fl = [bande("Actualité tech", "l'essentiel, sources à l'appui"), Spacer(1, 6)]
    cel = []
    for n in ed["tech"]:
        contenu = [P(T(n["titre"]), "btitre"), Spacer(1, 4)] + puces(n["points"], "puce_l") + [Spacer(1, 4)]
        contenu += [lien("Source : " + s[0], s[1]) for s in n["sources"]]
        cel.append(bloc(contenu, DEMI, accent=ROUGE, haut_accent=True))
    fl.append(grille(cel))
    return fl


def bloc_avis(a, titre, couleur, largeur):
    contenu = [etiquette(titre, couleur), P(T(a["qui"]), "btitre"), Spacer(1, 4)]
    contenu += [P(T(x), "puce_l", bulletText="•") for x in a.get("arguments", [])]
    cit = a.get("citation")
    if cit:
        contenu += [Spacer(1, 6), P("« " + T(cit[0]) + " »" + refs(cit[2] if len(cit) > 2 else []), "cit_avis"),
                    Spacer(1, 1), P("— " + T(cit[1]), "cit_auteur")]
    return bloc(contenu, largeur, accent=couleur, haut_accent=True)


def page_info(info, i, total):
    """Deux pages par sujet : A = les faits ; B = le débat et la vérification."""
    # ---------- page A : les faits
    fl = [bande(f"Information  ·  {info['theme']}", f"{i}/{total}  ·  les faits"),
          Spacer(1, 8), P(T(info["titre"]), "grand_titre"), Spacer(1, 4), P(T(info["chapeau"]), "chapeau"),
          Spacer(1, 8)]
    lg = LARG * 0.64
    ld = LARG - lg - GAP
    g = [etiquette("Le contexte", GRIS)] + puces(info.get("contexte", []), "puce_l")
    g += [Spacer(1, 6), etiquette("Les faits", ENCRE), Spacer(1, 2)]
    g += [P(T(f[0]) + refs(f[1]), "puce_l", bulletText="•") for f in info["faits"]]
    col_g = bloc(g, lg, epais=1.1)
    d = []
    for ch in info.get("chiffres", []):
        d.append(bloc([P(T(ch[0]), "chiffre"), Spacer(1, 2), P(T(ch[1]) + refs(ch[2]), "chiffre_l")], ld,
                      fond_bloc=TRAME, epais=0.6))
        d.append(Spacer(1, 3))
    if info.get("chronologie"):
        lignes = [[P(T(a), "chrono_d"), P(T(b), "chrono_t")] for a, b in info["chronologie"]]
        tc = Table(lignes, colWidths=[ld * 0.30 - 7, ld * 0.70 - 7])
        tc.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                                ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                                ("LINEBELOW", (0, 0), (-1, -2), 0.25, GRIS), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        d.append(bloc([etiquette("Chronologie", ROUGE), Spacer(1, 2), tc], ld))
    col_d = nu(Table([[x] for x in d], colWidths=[ld]))
    fl += [deux_colonnes(col_g, col_d, lg, ld), Spacer(1, GAP)]
    z = info.get("zoom")
    if z:
        fl.append(bloc([etiquette("Zoom", ROUGE), P(T(z["titre"]) + refs(z.get("refs")), "btitre"), Spacer(1, 3)]
                       + puces(z["points"], "puce_l"), LARG, fond_bloc=TRAME))
    # ---------- page B : le débat, la vérification, les sources
    fl += [PageBreak(), bande(f"Information  ·  {info['theme']}", f"{i}/{total}  ·  le débat et les sources"),
           Spacer(1, 8), P("Le débat : " + T(info["titre"]), "btitre"), Spacer(1, 6)]
    fl.append(deux_colonnes(bloc_avis(info["gauche"], info.get("gauche_titre", "Avis de gauche"), ROUGE, DEMI),
                            bloc_avis(info["droite"], info.get("droite_titre", "Avis de droite"), BLEU, DEMI)))
    fl.append(Spacer(1, GAP))
    cel = []
    if info.get("incertain"):
        cel.append(bloc([etiquette("Ce qui reste incertain", ORANGE), Spacer(1, 2)] + puces(info["incertain"], "puce_l"),
                        DEMI, accent=ORANGE, haut_accent=True))
    v = [etiquette("Vérification", VERT), Spacer(1, 2)]
    for quoi, comment, rr in info["verification"]:
        v.append(P(f"<font name='ZapfDingbats' color='#2F5D3A'>4</font> <b>{T(quoi)}</b> : {T(comment)}{refs(rr)}",
                   "puce"))
        v.append(Spacer(1, 3))
    cel.append(bloc(v, DEMI, accent=VERT, haut_accent=True))
    fl.append(grille(cel))
    src = [etiquette("Sources", ENCRE), Spacer(1, 2)]
    for n, (titre, url) in enumerate(info["sources"], 1):
        src.append(P(f"<font name='Etiquette' color='#9B2C20'>[{n}]</font> "
                     f"<a href=\"{T(url)}\" color=\"#1C1A16\"><u>{T(titre)}</u></a>", "source_n"))
        src.append(P(T(url), "petit"))
    fl.append(KeepTogether(bloc(src, LARG, epais=0.5)))
    return fl


def page_github(ed):
    g = ed["github"]
    fl = [bande("Dépôts GitHub à suivre", f"actifs depuis un mois · relevé du {g['date_releve']}"), Spacer(1, 6)]
    cel = []
    for r in g["rubriques"]:
        lignes = []
        for nom, etoiles, langage, maj, desc in r["depots"]:
            lignes.append(P(f"<a href=\"https://github.com/{T(nom)}\" color=\"#1C1A16\"><b>{T(nom)}</b></a>"
                            f"  <font name='ZapfDingbats' color='#9B2C20'>H</font><font name='Etiquette' color='#9B2C20'> {etoiles:,}</font>".replace(",", "\u202f")
                            + f"  <font name='Etroit' color='#5C564B'>{T(langage)} · màj {T(maj)}</font>", "puce"))
            lignes.append(P(T(desc), "petit"))
            lignes.append(Spacer(1, 4))
        cel.append(bloc([etiquette(r["titre"], ROUGE), Spacer(1, 3)] + lignes, DEMI, accent=ROUGE, haut_accent=True))
    fl.append(grille(cel))
    fl.append(lien("Source : " + g["source"][0], g["source"][1]))
    return fl


def page_senat(ed):
    s = ed["senat"]
    fl = [bande("Au Sénat", "les votes de la semaine"), Spacer(1, 8), P(T(s["titre"]), "grand_titre"), Spacer(1, 4),
          P(T(s["chapeau"]), "chapeau"), Spacer(1, 8)]
    lg = LARG * 0.66
    ld = LARG - lg - GAP
    votes = []
    for v in s["votes"]:
        c = [P(f"<font name='Etiquette' color='#9B2C20'>{T(v['date'].upper())}</font>  <b>{T(v['objet'])}</b>"
               + refs(v.get("refs")), "puce"),
             P("<b>Résultat :</b> " + T(v["resultat"]), "puce"),
             P("<b>Pourquoi c'est important :</b> " + T(v["importance"]), "puce")]
        c += [P(T(x), "petit", bulletText="•") for x in v.get("debat", [])]
        votes.append(bloc(c, lg, epais=0.6))
        votes.append(Spacer(1, 3))
    col_g = nu(Table([[x] for x in votes], colWidths=[lg]))
    total = sum(n for _, n in s["composition"])
    lignes = [[P(T(g), "chrono_t"), P(str(n), "td_r")] for g, n in s["composition"]]
    lignes.append([P("<b>Total</b>", "chrono_t"), P(f"<b>{total}</b>", "td_r")])
    tc = Table(lignes, colWidths=[ld * 0.72 - 7, ld * 0.28 - 7])
    tc.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                            ("LINEBELOW", (0, 0), (-1, -2), 0.25, GRIS)]))
    droite = [bloc([etiquette("Composition du Sénat", ENCRE), Spacer(1, 2), tc], ld, fond_bloc=TRAME), Spacer(1, 4)]
    for a in s.get("a_venir", []):
        c = [etiquette("À venir", ORANGE),
             P(f"<font name='Etiquette' color='#9B2C20'>{T(a['date'].upper())}</font>  <b>{T(a['objet'])}</b>"
               + refs(a.get("refs")), "puce"), P(T(a["contenu"]), "petit")]
        if a.get("pour"):
            c.append(P("<font color='#1F3E66'><b>Pour :</b></font> " + T(a["pour"]), "petit"))
        if a.get("contre"):
            c.append(P("<font color='#9B2C20'><b>Contre :</b></font> " + T(a["contre"]), "petit"))
        droite += [bloc(c, ld, accent=ORANGE, haut_accent=True), Spacer(1, 4)]
    col_d = nu(Table([[x] for x in droite], colWidths=[ld]))
    fl += [deux_colonnes(col_g, col_d, lg, ld), Spacer(1, GAP)]
    src = [etiquette("Sources", ENCRE), Spacer(1, 2)]
    for n, (titre, url) in enumerate(s["sources"], 1):
        src.append(P(f"<font name='Etiquette' color='#9B2C20'>[{n}]</font> "
                     f"<a href=\"{T(url)}\" color=\"#1C1A16\"><u>{T(titre)}</u></a>", "source_n"))
    fl.append(KeepTogether(bloc(src, LARG, epais=0.5)))
    return fl


def page_ville(ed):
    v = ed["ville"]
    fl = [bande(f"À {v['nom']} et alentour", "l'actu de la ville · quoi faire"), Spacer(1, 6)]
    cel = [bloc([etiquette("Actualité", ROUGE), P(T(a["titre"]), "btitre"), Spacer(1, 2), P(T(a["texte"]), "puce"),
                 Spacer(1, 2), lien("Source : " + a["source"][0], a["source"][1])], DEMI) for a in v["actus"]]
    fl.append(grille(cel))
    lignes = [[P(T(q), "chrono_d"), P(f"<b>{T(t)}</b> — {T(d)}", "chrono_t")] for q, t, d in v["activites"]]
    ta = Table(lignes, colWidths=[LARG * 0.24 - 7, LARG * 0.76 - 7])
    ta.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                            ("LINEBELOW", (0, 0), (-1, -2), 0.25, GRIS), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    fl.append(bloc([etiquette("Que faire cette semaine ?", ENCRE), Spacer(1, 3), ta], LARG, epais=1.1))
    fl.append(Spacer(1, GAP))
    al = [P(f"<b>{T(n)}</b> — {T(d)}", "puce", bulletText="•") for n, d in v["alentours"]]
    fl.append(bloc([etiquette("Aux alentours", VERT), Spacer(1, 2)] + al, LARG, fond_bloc=TRAME))
    fl.append(Spacer(1, GAP))
    src = [etiquette("Sources", ENCRE)] + [lien(t, u) for t, u in v["sources"]]
    fl.append(bloc(src, LARG, epais=0.5))
    return fl


# ---------------------------------------------------------------- assemblage
def construire(ed, offres, sortie):
    init_styles()
    doc = BaseDocTemplate(sortie, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=M,
                          title=f"{NOM_JOURNAL}, n° {ed['numero']}", author="Claude pour Simon")
    doc.ed = ed
    bas = M + 14
    f_une = Frame(M, bas, LARG, H - M - 82 - bas, id="une", leftPadding=0, rightPadding=0, topPadding=0,
                  bottomPadding=0)
    f_int = Frame(M, bas, LARG, H - M - 30 - bas, id="int", leftPadding=0, rightPadding=0, topPadding=0,
                  bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="une", frames=[f_une], onPage=page_une),
                          PageTemplate(id="int", frames=[f_int], onPage=page_interieure)])
    fl = page_culture(ed) + [NextPageTemplate("int"), PageBreak()]
    if offres:
        fl += page_offres(offres) + [PageBreak()]
    fl += page_mots(ed) + [PageBreak()] + page_tech(ed)
    if ed.get("github"):
        fl += [PageBreak()] + page_github(ed)
    for i, info in enumerate(ed["infos"], 1):
        fl += [PageBreak()] + page_info(info, i, len(ed["infos"]))
    if ed.get("senat"):
        fl += [PageBreak()] + page_senat(ed)
    if ed.get("ville"):
        fl += [PageBreak()] + page_ville(ed)
    doc.build(fl)


if __name__ == "__main__":
    contenu = json.load(open(sys.argv[1], encoding="utf-8"))
    offres = json.load(open(sys.argv[2], encoding="utf-8")) if sys.argv[2] != "-" else []
    if isinstance(offres, dict):
        offres = offres.get("offres", [])
    charger_polices(sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                        "polices"))
    construire(contenu, offres, sys.argv[3])
    print("PDF écrit :", sys.argv[3])
