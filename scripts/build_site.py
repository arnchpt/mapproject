"""Assemble les CSV de data/clean/ en un seul fichier lu par la carte (site/data/donnees.json).

Copie aussi les CSV dans site/data/ pour qu'ils soient téléchargeables depuis la carte.
"""

import csv
import json
import os
import shutil

from common import DOSSIER_CLEAN, RACINE, lire_statut, maintenant

SORTIE = os.path.join(RACINE, "site", "data")

SOURCES = {
    "imf": {
        "nom": "IMF – World Economic Outlook (API DataMapper)",
        "lien": "https://www.imf.org/external/datamapper/",
        "licence": "Réutilisation permise avec mention de la source (conditions IMF)",
        "licence_lien": "https://www.imf.org/en/About/copyright-and-terms",
        "fichier": "imf.csv",
    },
    "commerce": {
        "nom": "Eurostat – Comext (DS-059341)",
        "lien": "https://ec.europa.eu/eurostat/comext/newxtweb/",
        "licence": "CC BY 4.0",
        "licence_lien": "https://ec.europa.eu/eurostat/web/main/help/copyright-notice",
        "fichier": "commerce.csv",
    },
    "gels": {
        "nom": "DG Trésor – Registre national des gels",
        "lien": "https://gels-avoirs.dgtresor.gouv.fr/",
        "licence": "Licence Ouverte 2.0 (déclarée sur data.gouv.fr)",
        "licence_lien": "https://www.data.gouv.fr/dataservices/api-gels-des-avoirs/",
        "fichier": "gels.csv",
    },
}


def nombre(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return v


def main():
    os.makedirs(SORTIE, exist_ok=True)
    pays = {}
    for couche, meta in SOURCES.items():
        chemin = os.path.join(DOSSIER_CLEAN, meta["fichier"])
        if not os.path.exists(chemin):
            continue
        shutil.copy(chemin, os.path.join(SORTIE, meta["fichier"]))
        with open(chemin, encoding="utf-8") as f:
            for ligne in csv.DictReader(f):
                iso3 = ligne.pop("iso3")
                pays.setdefault(iso3, {})[couche] = {k: nombre(v) for k, v in ligne.items() if v != ""}
    sortie = {
        "genere_le": maintenant(),
        "statut": lire_statut(),
        "sources": SOURCES,
        "pays": pays,
    }
    with open(os.path.join(SORTIE, "donnees.json"), "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, separators=(",", ":"))
    print(f"site/data/donnees.json : {len(pays)} pays")


if __name__ == "__main__":
    main()
