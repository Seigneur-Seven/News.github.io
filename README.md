# Seven News

Le quotidien de Simon, façon presse française des années 50 : culture générale, offres de stage, mots du jour, tech, dépôts GitHub, cinq sujets d'actualité vérifiés (faits, avis de gauche et de droite, sources), votes du Sénat et sorties à Cergy.

- **Site** : `index.html` (dernière édition), `archives.html` (historique et suivi de lecture), `api.html` (documentation de l'API).
- **API** : `api/latest.json`, `api/editions.json`, `api/editions/AAAA-MM-JJ.json`, `pdf/Seven-News-AAAA-MM-JJ.pdf`.
- **Outils** (`outils/`) :
  - `PROMPT.md` : le prompt complet qui rédige chaque édition ;
  - `offres_du_jour.py` : sélection des 50 stages les mieux payés, sans doublon ;
  - `seven_news.py` : mise en page du PDF ;
  - `publier_site.py` : ajoute une édition au site et à l'API.

## Publier une édition

```bash
pip install reportlab
python3 outils/offres_du_jour.py deja_vus.json offres.json
python3 outils/seven_news.py contenu.json offres.json Seven-News-AAAA-MM-JJ.pdf
python3 outils/publier_site.py contenu.json offres.json Seven-News-AAAA-MM-JJ.pdf .
git add -A && git commit -m "Édition du AAAA-MM-JJ" && git push
```

## Mise en ligne (GitHub Pages)

Settings > Pages > Source : « Deploy from a branch », branche `main`, dossier `/ (root)`.
Le site est alors servi sur `https://seigneur-seven.github.io/News.github.io/`.
Pour l'avoir à la racine `https://seigneur-seven.github.io/`, renommer le dépôt en `Seigneur-Seven.github.io`.

Le suivi de lecture est stocké dans le navigateur (localStorage) ; la page Archives permet de le copier vers un autre appareil.
