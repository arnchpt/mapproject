# Journal de la preuve de concept (30 jours)

Objectif : vérifier que la carte se met à jour seule pendant 30 jours, sans intervention.

## Critères de décision (à évaluer au bout de 30 jours)

| Critère | Go | No-go |
|---|---|---|
| Collectes réussies | ≥ 90 % des nuits, sans intervention | Pannes répétées |
| Temps passé par le porteur | < 1 h sur le mois | Plus de 1 h par semaine |
| Fraîcheur visible | Dates justes sur la carte | Données périmées affichées sans alerte |
| Test non-initié (1 personne) | Comprend un pays en < 30 s | Ne comprend pas ce qu'il voit |

## Relevé hebdomadaire

Une ligne par semaine : un coup d'œil à la carte et à l'onglet Actions suffit.

| Semaine du | Nuits en échec (sur 7) | Bandeau visible ? | Temps passé | Remarques |
|---|---|---|---|---|
| 05/10/2026 (PoC depuis le 10/10) | 0 / 2 nuits écoulées (collecte du 12/10 pas encore passée à 9 h) | non (attendu, aucune source en défaut) | à compléter par Arnaud | 18/18 collectes OK ; collecte planifiée du 11/10 retardée à 12 h (Paris) ; carte en ligne non vérifiée (accès web refusé) |
| 12/10/2026 | 1 / 7 (échec partiel : gels seuls, le 16/10, rétabli seul) | oui le 16/10 (attendu, non vérifié visuellement) ; non le 19/10 | à compléter par Arnaud | 20/21 collectes OK (95 %) ; édition IMF d'octobre 2026 intégrée le 13/10 ; gels +13 % (Russie) ; carte en ligne à jour |
| 19/10/2026 | 0 / 7 | non (attendu, aucune source en défaut) | à compléter par Arnaud | 21/21 collectes OK (100 %) ; gels +7 % (Russie +318) ; IMF et commerce inchangés ; carte en ligne à jour (25/10) |
| | | | | |

## Incidents

| Date | Ce qui s'est passé | Ce qui a été fait | Temps passé |
|---|---|---|---|
| | | | |

## Test non-initié

Date, profil du testeur, temps pour comprendre un pays, ce qu'il n'a pas compris :

## Comptes rendus automatiques

Chaque lundi, une tâche planifiée produit un compte rendu dans `docs/comptes-rendus/` (fiabilité de la collecte, fraîcheur des données, évolution des valeurs) à partir de `scripts/compte_rendu.py`. Le compte rendu du 10/10/2026 sert d'état de départ.
