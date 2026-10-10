# La France dans le monde — preuve de concept

Carte publique et gratuite qui montre, pays par pays, des **faits datés et sourcés** : santé économique et relations avec la France. Aucune note, aucun jugement.

Cette version est une **preuve de concept** : elle teste si la carte peut se mettre à jour seule pendant 30 jours, sans intervention.

## Ce que montre la carte

| Couche | Source | Mise à jour |
|---|---|---|
| Croissance du PIB, dette publique | IMF, World Economic Outlook (API DataMapper) | Chaque nuit (les données changent 2 fois par an) |
| Commerce de biens France–pays | Eurostat, Comext (CC BY 4.0) | Chaque nuit (données annuelles) |
| Gels d'avoirs en France | DG Trésor, registre national des gels | Chaque nuit |

Fond de carte : Natural Earth, vue France (domaine public). Bibliothèque cartographique : MapLibre GL JS (licence BSD, copie dans `site/vendor/`).

## Comment ça marche

1. Chaque nuit, GitHub Actions lance les scripts de `scripts/`, qui téléchargent les sources et écrivent des CSV dans `data/clean/`.
2. `data/status.json` garde la date de la dernière réussite de chaque source, et l'erreur en cas d'échec.
3. La carte (`site/`) est publiée sur GitHub Pages. Elle affiche un bandeau quand une source a échoué ou n'est plus à jour.

Coût : zéro (dépôt public, GitHub Actions et GitHub Pages gratuits pour les dépôts publics).

## En cas de problème

Voir [`docs/relance.md`](docs/relance.md). Le suivi des 30 jours se fait dans [`docs/journal-poc.md`](docs/journal-poc.md).

## Avertissement

Projet indépendant, non affilié au ministère de l'Europe et des Affaires étrangères ni à aucune administration. Les données appartiennent à leurs éditeurs et sont réutilisées selon leurs conditions (voir `sources/registre-sources.csv`). Usage non commercial.
