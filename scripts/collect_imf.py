"""Collecte IMF (World Economic Outlook, via l'API DataMapper).

Indicateurs : croissance du PIB réel (NGDP_RPCH) et dette publique brute en % du PIB (GGXWDG_NGDP).
On retient la dernière année AVANT les projections de l'IMF (elle peut être une estimation).
Conditions IMF : réutilisation permise avec mention de la source ; usage commercial soumis à permission.
"""

from common import executer, ecrire_csv, pays_reference, telecharger_json

API = "https://www.imf.org/external/datamapper/api/v2/"
INDICATEURS = {"NGDP_RPCH": "croissance_pib", "GGXWDG_NGDP": "dette_publique"}

# Codes IMF qui diffèrent du fond de carte Natural Earth.
CORRESPONDANCES = {"UVK": "KOS", "WBG": "PSE"}


def collecter():
    pays = pays_reference()
    lignes = {}
    infos = {}
    for code, colonne in INDICATEURS.items():
        donnees = telecharger_json(API + code)
        meta = donnees["indicators"][code]
        annee_proj = int(meta.get("projection-year") or 0)
        annee = annee_proj - 1
        infos[colonne] = {
            "annee": annee,
            "edition": meta.get("source", ""),
            "mise_a_jour_source": meta.get("last-modified", ""),
        }
        for code_pays, serie in donnees["values"][code].items():
            iso3 = CORRESPONDANCES.get(code_pays, code_pays)
            if iso3 not in pays:
                continue  # agrégats régionaux (ex. « Zone euro ») ou territoires absents de la carte
            valeur = serie.get(str(annee))
            if valeur is None:
                continue
            ligne = lignes.setdefault(iso3, {"iso3": iso3})
            ligne[colonne] = round(float(valeur), 1)
            ligne[colonne + "_annee"] = annee
    if len(lignes) < 100:
        raise RuntimeError(f"Trop peu de pays reçus ({len(lignes)}) : réponse IMF suspecte")
    colonnes = ["iso3"]
    for c in INDICATEURS.values():
        colonnes += [c, c + "_annee"]
    ecrire_csv("imf.csv", colonnes, list(lignes.values()))
    infos["nb_pays"] = len(lignes)
    return infos


if __name__ == "__main__":
    executer("imf", collecter)
