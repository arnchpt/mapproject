"""Collecte Eurostat Comext : commerce de biens de la France par pays partenaire.

Jeu DS-059341 (« International trade of EU and non-EU countries since 2002 by HS2-4-6 »),
déclarant = France, produit = total, valeur en euros, données annuelles.
Licence Eurostat : CC BY 4.0 (réutilisation libre avec mention de la source).
"""

from datetime import date

from common import executer, ecrire_csv, pays_reference, telecharger_json

API = ("https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-059341"
       "?format=JSON&lang=en&freq=A&reporter=FR&product=TOTAL&indicators=VALUE_EUR&flow={flux}&time={annee}")

# Codes partenaires Comext qui diffèrent de l'ISO2 du fond de carte.
# Depuis 2021, le Royaume-Uni est déclaré en XU (hors Irlande du Nord) et XI (Irlande du Nord).
CORRESPONDANCES_ISO2 = {"XU": "GB", "XI": "GB", "EL": "GR", "XK": "XK", "XS": "RS"}


def decoder_jsonstat(donnees):
    """Transforme la réponse JSON-stat en {code_partenaire: valeur}."""
    ids = donnees["id"]
    tailles = donnees["size"]
    dims = donnees["dimension"]
    # position de chaque catégorie, dimension par dimension
    positions = []
    for d in ids:
        index = dims[d]["category"]["index"]
        inverse = {v: k for k, v in index.items()} if isinstance(index, dict) else dict(enumerate(index))
        positions.append(inverse)
    resultats = {}
    for cle, valeur in donnees.get("value", {}).items():
        n = int(cle)
        coords = []
        for taille in reversed(tailles):
            coords.append(n % taille)
            n //= taille
        coords.reverse()
        categories = {ids[i]: positions[i][coords[i]] for i in range(len(ids))}
        if categories.get("indicators", "VALUE_EUR") != "VALUE_EUR":
            continue
        resultats[categories["partner"]] = resultats.get(categories["partner"], 0) + float(valeur)
    return resultats


def collecter():
    pays = pays_reference()
    iso2_vers_iso3 = {v["iso2"]: k for k, v in pays.items() if v["iso2"]}
    # On cherche l'année complète la plus récente disponible (année passée, sinon celle d'avant).
    for annee in (date.today().year - 1, date.today().year - 2):
        exports = decoder_jsonstat(telecharger_json(API.format(flux=2, annee=annee)))
        imports = decoder_jsonstat(telecharger_json(API.format(flux=1, annee=annee)))
        if len(exports) > 100:
            break
    else:
        raise RuntimeError("Aucune année récente disponible dans Comext")

    lignes = {}
    non_rattaches = set()
    for colonne, valeurs in (("exportations_fr", exports), ("importations_fr", imports)):
        for code, v in valeurs.items():
            iso3 = iso2_vers_iso3.get(CORRESPONDANCES_ISO2.get(code, code))
            if not iso3 or iso3 == "FRA":
                non_rattaches.add(code)  # agrégats (ex. EU27_2020_EXTRA) ou codes sans pays
                continue
            ligne = lignes.setdefault(iso3, {"iso3": iso3, "annee": annee})
            ligne[colonne] = round(ligne.get(colonne, 0) + v / 1e6, 1)  # en millions d'euros
    for ligne in lignes.values():
        ligne["solde_fr"] = round(ligne.get("exportations_fr", 0) - ligne.get("importations_fr", 0), 1)
    if len(lignes) < 100:
        raise RuntimeError(f"Trop peu de partenaires ({len(lignes)}) : réponse Comext suspecte")
    ecrire_csv("commerce.csv", ["iso3", "annee", "exportations_fr", "importations_fr", "solde_fr"],
               list(lignes.values()))
    return {"annee": annee, "nb_pays": len(lignes), "codes_non_rattaches": sorted(non_rattaches)[:40]}


if __name__ == "__main__":
    executer("commerce", collecter)
