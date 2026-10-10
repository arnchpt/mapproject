# Que faire quand quelque chose ne marche pas

Cette page s'adresse au porteur du projet. Elle ne suppose aucune connaissance en code.

## Comment savoir si tout va bien

1. **Sur la carte** : un bandeau rouge ou orange apparaît sous le titre dès qu'une collecte a échoué ou date de plus de 3 jours. Pas de bandeau = tout va bien.
2. **Sur GitHub** : onglet **Actions** du dépôt. Chaque nuit, une ligne « Collecte et publication » apparaît. Une coche verte signifie que tout a marché, une croix rouge qu'une étape a échoué.
3. **Le détail** est dans le fichier `data/status.json` : pour chaque source, la date de la dernière réussite et, en cas d'échec, le message d'erreur.

## Les pannes probables et quoi faire

| Ce que vous voyez | Cause probable | Que faire |
|---|---|---|
| Bandeau « la collecte X a échoué » pendant 1 ou 2 jours | Le site de la source était indisponible | Rien. La collecte réessaie chaque nuit. |
| Le même bandeau pendant plus de 5 jours | La source a changé son adresse ou son format | Ouvrir une session Claude sur ce dépôt et coller le message d'erreur de `data/status.json`, en demandant de réparer le script de cette source. |
| Plus aucune ligne dans l'onglet Actions depuis des semaines | GitHub a désactivé la tâche planifiée (dépôt sans activité pendant 60 jours) | Onglet **Actions** > « Collecte et publication » > bouton **Enable workflow**. |
| La carte ne s'affiche plus du tout | La publication GitHub Pages a échoué | Onglet **Actions**, relancer la dernière exécution (**Re-run all jobs**). Si l'échec persiste, vérifier **Settings > Pages** : la source doit être « GitHub Actions ». |
| Un pays affiche un chiffre étrange | Changement chez la source, ou rattachement de pays erroné | Vérifier le chiffre sur le site de la source (lien dans la fiche pays). Signaler l'écart dans `docs/journal-poc.md`. |

## Relancer une collecte à la main

Onglet **Actions** > « Collecte et publication » (colonne de gauche) > bouton **Run workflow** > **Run workflow**. Le résultat arrive en 2 à 5 minutes.

## Ce qui n'est jamais automatique

Rien n'est inventé : si une source ne répond pas, la carte garde les dernières données réussies et l'affiche clairement. Aucune donnée n'est saisie à la main dans cette preuve de concept.
