"""Compte rendu de l'évolution et de l'actualisation de la carte sur une période.

Lit l'historique Git du dépôt (les collectes nocturnes y sont enregistrées) et produit
un fichier Markdown dans docs/comptes-rendus/ :
  - fiabilité de la collecte : nuits collectées, échecs par source ;
  - fraîcheur : édition et date des données de chaque source ;
  - évolution : pays ajoutés ou retirés, valeurs qui ont changé.

Usage : python scripts/compte_rendu.py [--depuis AAAA-MM-JJ] [--jusqu-au AAAA-MM-JJ]
Nécessite l'historique Git complet (git fetch --unshallow si le dépôt a été cloné en --depth 1).
"""

import argparse
import csv
import io
import json
import os
import subprocess
from datetime import date, datetime, timedelta

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUCHES = {
    "imf": ("imf.csv", ["croissance_pib", "dette_publique"], "macro-économie (IMF)"),
    "commerce": ("commerce.csv", ["exportations_fr", "importations_fr"], "commerce (Eurostat Comext)"),
    "gels": ("gels.csv", ["entrees_gel"], "gels d'avoirs (DG Trésor)"),
}
LIBELLES = {
    "croissance_pib": "croissance du PIB (%)", "dette_publique": "dette publique (% du PIB)",
    "exportations_fr": "exportations françaises (M€)", "importations_fr": "importations françaises (M€)",
    "entrees_gel": "entrées au registre des gels",
}


def git(*args):
    return subprocess.run(["git", *args], cwd=RACINE, capture_output=True, text=True, check=False).stdout


def fichier_au_commit(commit, chemin):
    if not commit:
        return None
    sortie = subprocess.run(["git", "show", f"{commit}:{chemin}"], cwd=RACINE, capture_output=True, text=True)
    return sortie.stdout if sortie.returncode == 0 else None


def lire_csv(texte):
    if not texte:
        return {}
    return {l["iso3"]: l for l in csv.DictReader(io.StringIO(texte))}


def maj(t):
    return t[:1].upper() + t[1:]


def nombre(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def noms_pays():
    with open(os.path.join(RACINE, "site", "pays.geojson"), encoding="utf-8") as f:
        geo = json.load(f)
    noms = {}
    for feat in geo["features"]:
        noms.setdefault(feat["properties"]["iso3"], feat["properties"]["nom"])
    return noms


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--depuis", default=(date.today() - timedelta(days=7)).isoformat())
    p.add_argument("--jusqu-au", dest="jusqu_au", default=date.today().isoformat())
    a = p.parse_args()
    debut, fin = date.fromisoformat(a.depuis), date.fromisoformat(a.jusqu_au)
    noms = noms_pays()

    # 1. Toutes les versions de status.json dans la période : une version = une collecte.
    lignes = git("log", "--reverse", f"--since={debut.isoformat()}T00:00:00Z",
                 f"--until={fin.isoformat()}T23:59:59Z", "--format=%H", "--", "data/status.json").split()
    tentatives = {c: {} for c in COUCHES}
    for commit in lignes:
        statut = json.loads(fichier_au_commit(commit, "data/status.json") or "{}")
        for couche in COUCHES:
            s = statut.get(couche)
            if s and s.get("derniere_tentative"):
                tentatives[couche][s["derniere_tentative"]] = bool(s.get("ok"))
    jours_collectes = {t[:10] for c in tentatives.values() for t in c}
    jours_periode = [(debut + timedelta(days=i)).isoformat() for i in range((fin - debut).days + 1)]
    jours_sans = [j for j in jours_periode if j not in jours_collectes]

    # 2. État de référence (avant la période) et état final.
    ref = git("log", "-1", f"--before={debut.isoformat()}T00:00:00Z", "--format=%H", "--", "data/clean").strip()
    if not ref:
        ref = git("log", "--reverse", "--format=%H", "--", "data/clean").split()[0]
    fin_commit = git("log", "-1", f"--before={fin.isoformat()}T23:59:59Z", "--format=%H", "--", "data/clean").strip() or "HEAD"
    statut_ref = json.loads(fichier_au_commit(ref, "data/status.json") or "{}")
    fin_statut = git("log", "-1", f"--before={fin.isoformat()}T23:59:59Z", "--format=%H", "--", "data/status.json").strip() or "HEAD"
    statut_fin = json.loads(fichier_au_commit(fin_statut, "data/status.json") or "{}")

    out = [f"# Compte rendu de la carte, du {debut:%d/%m/%Y} au {fin:%d/%m/%Y}", "",
           f"Généré le {datetime.now():%d/%m/%Y à %H:%M} à partir de l'historique du dépôt.", ""]

    # Fiabilité
    out += ["## Fiabilité de la collecte", "",
            f"- Jours de la période : {len(jours_periode)} ; jours avec au moins une collecte : {len(jours_periode) - len(jours_sans)}.",
            f"- Jours sans collecte : {', '.join(jours_sans) if jours_sans else 'aucun'}.", "",
            "| Source | Collectes | Réussies | Échouées | Dernière réussite | Dernière erreur |",
            "|---|---|---|---|---|---|"]
    for couche, (_, _, libelle) in COUCHES.items():
        t = tentatives[couche]
        ok = sum(t.values())
        sf = statut_fin.get(couche, {})
        out.append(f"| {libelle} | {len(t)} | {ok} | {len(t) - ok} | {sf.get('derniere_reussite', '—')} | "
                   f"{(sf.get('erreur') or '—')[:120]} |")
    total = sum(len(t) for t in tentatives.values())
    reussies = sum(sum(t.values()) for t in tentatives.values())
    taux = f"{100 * reussies / total:.0f} %" if total else "n/a"
    out += ["", f"Taux de réussite global : **{taux}** ({reussies}/{total} collectes).", ""]

    # Fraîcheur
    def edition(s):
        return (s.get("imf", {}).get("croissance_pib") or {}).get("edition", "—")
    out += ["## Fraîcheur des données", "",
            "| Source | Début de période | Fin de période |", "|---|---|---|",
            f"| IMF : édition | {edition(statut_ref)} | {edition(statut_fin)} |",
            f"| IMF : année affichée | {(statut_ref.get('imf', {}).get('croissance_pib') or {}).get('annee', '—')} | "
            f"{(statut_fin.get('imf', {}).get('croissance_pib') or {}).get('annee', '—')} |",
            f"| Commerce : année affichée | {statut_ref.get('commerce', {}).get('annee', '—')} | {statut_fin.get('commerce', {}).get('annee', '—')} |",
            f"| Gels : date du registre | {statut_ref.get('gels', {}).get('date_publication_registre', '—')[:10]} | "
            f"{statut_fin.get('gels', {}).get('date_publication_registre', '—')[:10]} |",
            f"| Gels : entrées au registre | {statut_ref.get('gels', {}).get('nb_entrees_registre', '—')} | "
            f"{statut_fin.get('gels', {}).get('nb_entrees_registre', '—')} |", ""]

    # Évolution
    out += ["## Évolution des données", ""]
    for couche, (fichier, colonnes, libelle) in COUCHES.items():
        avant = lire_csv(fichier_au_commit(ref, f"data/clean/{fichier}"))
        apres = lire_csv(fichier_au_commit(fin_commit, f"data/clean/{fichier}"))
        ajoutes = sorted(set(apres) - set(avant))
        retires = sorted(set(avant) - set(apres))
        out.append(f"### {maj(libelle)}")
        out.append("")
        out.append(f"- Pays couverts : {len(avant)} → {len(apres)}."
                   + (f" Ajoutés : {', '.join(noms.get(i, i) for i in ajoutes)}." if ajoutes else "")
                   + (f" Retirés : {', '.join(noms.get(i, i) for i in retires)}." if retires else ""))
        for col in colonnes:
            ecarts = []
            for iso3 in set(avant) & set(apres):
                x, y = nombre(avant[iso3].get(col)), nombre(apres[iso3].get(col))
                if x is not None and y is not None and abs(y - x) > 1e-9:
                    ecarts.append((abs(y - x), iso3, x, y))
            ecarts.sort(reverse=True)
            if not ecarts:
                out.append(f"- {maj(LIBELLES[col])} : aucune valeur modifiée.")
                continue
            detail = "; ".join(f"{noms.get(i, i)} {x:g} → {y:g}" for _, i, x, y in ecarts[:8])
            out.append(f"- {maj(LIBELLES[col])} : {len(ecarts)} pays modifiés. Plus fortes variations : {detail}.")
        out.append("")

    os.makedirs(os.path.join(RACINE, "docs", "comptes-rendus"), exist_ok=True)
    chemin = os.path.join(RACINE, "docs", "comptes-rendus", f"{fin.isoformat()}.md")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(chemin)


if __name__ == "__main__":
    main()
