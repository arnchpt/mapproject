"""Collecte du registre national des gels d'avoirs (DG Trésor, API publique).

Pour chaque pays : nombre d'entrées du registre (personnes, entités, navires) rattachées
au pays par la NATIONALITÉ (personnes) ou l'ADRESSE (personnes et entités).
Seuls des comptages agrégés sont publiés : aucun nom ni donnée personnelle n'est conservé.
Licence : Licence Ouverte 2.0 déclarée sur data.gouv.fr (par un producteur tiers, à confirmer).
"""

from collections import defaultdict

from common import executer, ecrire_csv, normaliser, pays_reference, telecharger_json

URL = "https://gels-avoirs.dgtresor.gouv.fr/ApiPublic/api/v1/publication/derniere-publication-fichier-json"

# Variantes de noms de pays rencontrées dans les registres officiels français.
ALIAS = {
    "russie": "RUS", "federation de russie": "RUS", "russie federation de": "RUS",
    "bielorussie": "BLR", "belarus": "BLR", "republique du belarus": "BLR",
    "iran": "IRN", "republique islamique d iran": "IRN", "iran republique islamique d": "IRN",
    "coree du nord": "PRK", "republique populaire democratique de coree": "PRK", "rpdc": "PRK",
    "coree du sud": "KOR", "republique de coree": "KOR",
    "syrie": "SYR", "republique arabe syrienne": "SYR",
    "birmanie": "MMR", "myanmar": "MMR", "birmanie myanmar": "MMR", "myanmar birmanie": "MMR",
    "republique democratique du congo": "COD", "rdc": "COD", "congo kinshasa": "COD",
    "congo": "COG", "republique du congo": "COG", "congo brazzaville": "COG",
    "etats unis": "USA", "etats unis d amerique": "USA",
    "royaume uni": "GBR", "emirats arabes unis": "ARE", "eau": "ARE",
    "libye": "LBY", "irak": "IRQ", "iraq": "IRQ", "yemen": "YEM", "liban": "LBN",
    "soudan du sud": "SSD", "soudan": "SDN", "somalie": "SOM", "afghanistan": "AFG",
    "venezuela": "VEN", "nicaragua": "NIC", "moldavie": "MDA", "republique de moldavie": "MDA",
    "guinee": "GIN", "guinee bissau": "GNB", "mali": "MLI", "haiti": "HTI", "tunisie": "TUN",
    "egypte": "EGY", "chine": "CHN", "republique populaire de chine": "CHN", "hong kong": "HKG",
    "kirghizistan": "KGZ", "kazakhstan": "KAZ", "georgie": "GEO", "armenie": "ARM",
    "azerbaidjan": "AZE", "ouzbekistan": "UZB", "tadjikistan": "TJK", "turkmenistan": "TKM",
    "serbie": "SRB", "bosnie herzegovine": "BIH", "montenegro": "MNE", "kosovo": "KOS",
    "macedoine du nord": "MKD", "turquie": "TUR", "ukraine": "UKR", "crimee": "UKR",
    "palestine": "PSE", "territoires palestiniens": "PSE", "cisjordanie": "PSE", "gaza": "PSE",
    "republique centrafricaine": "CAF", "centrafrique": "CAF", "cote d ivoire": "CIV",
    "pakistan": "PAK", "inde": "IND", "arabie saoudite": "SAU", "qatar": "QAT", "koweit": "KWT",
    "jordanie": "JOR", "algerie": "DZA", "maroc": "MAR", "nigeria": "NGA", "niger": "NER",
    "burkina faso": "BFA", "tchad": "TCD", "erythree": "ERI", "ethiopie": "ETH", "zimbabwe": "ZWE",
    "cuba": "CUB", "bresil": "BRA", "allemagne": "DEU", "italie": "ITA", "espagne": "ESP",
    "belgique": "BEL", "pays bas": "NLD", "suisse": "CHE", "chypre": "CYP", "grece": "GRC",
    "lettonie": "LVA", "lituanie": "LTU", "estonie": "EST", "finlande": "FIN", "pologne": "POL",
    "malaisie": "MYS", "singapour": "SGP", "indonesie": "IDN", "philippines": "PHL",
    "thailande": "THA", "vietnam": "VNM", "viet nam": "VNM", "japon": "JPN", "mongolie": "MNG",
    "israel": "ISR", "oman": "OMN", "bahrein": "BHR", "sri lanka": "LKA", "bangladesh": "BGD",
    "seychelles": "SYC", "iles vierges britanniques": "VGB", "panama": "PAN", "belize": "BLZ",
    "marshall": "MHL", "iles marshall": "MHL", "liberia": "LBR", "comores": "COM",
    "trinidad et tobago": "TTO", "republique tcheque": "CZE", "iles caimanes": "CYM",
    "saint kitts et nevis": "KNA", "saint christophe et nieves": "KNA",
    "france": "FRA",
}


def construire_index(pays):
    index = {normaliser(v["nom"]): iso3 for iso3, v in pays.items()}
    index.update({normaliser(v["nom_en"]): iso3 for iso3, v in pays.items()})
    index.update(ALIAS)
    return index


def rattacher(texte, index):
    """Renvoie le code ISO3 correspondant à un nom de pays libre, ou None."""
    n = normaliser(texte)
    if not n:
        return None
    if n in index:
        return index[n]
    # Repli : le nom de pays le plus long contenu dans le texte (ex. « Moscou, Russie »).
    candidats = [k for k in index if len(k) >= 4 and f" {k} " in f" {n} "]
    if candidats:
        return index[max(candidats, key=len)]
    return None


def pays_de_l_entree(entree):
    """Noms de pays associés à une entrée : nationalité et adresses."""
    noms = []
    for champ in entree.get("RegistreDetail", []):
        type_champ = champ.get("TypeChamp")
        if type_champ not in ("NATIONALITE", "ADRESSE_PP", "ADRESSE_PM"):
            continue
        valeurs = champ.get("Valeur") or []
        if isinstance(valeurs, dict):
            valeurs = [valeurs]
        for v in valeurs:
            if isinstance(v, dict) and v.get("Pays"):
                noms.append(v["Pays"])
    return noms


def collecter():
    pays = pays_reference()
    index = construire_index(pays)
    donnees = telecharger_json(URL)
    publication = donnees["Publications"]
    entrees = publication["PublicationDetail"]
    if len(entrees) < 100:
        raise RuntimeError(f"Registre anormalement court ({len(entrees)} entrées)")

    par_pays = defaultdict(lambda: {"Personne physique": set(), "Personne morale": set(), "Navire": set()})
    non_rattaches = defaultdict(int)
    sans_pays = 0
    for e in entrees:
        noms = pays_de_l_entree(e)
        if not noms:
            sans_pays += 1
            continue
        for nom in noms:
            iso3 = rattacher(nom, index)
            if iso3 and iso3 in pays:
                par_pays[iso3].setdefault(e.get("Nature"), set()).add(e["IdRegistre"])
            else:
                non_rattaches[nom] += 1

    lignes = []
    for iso3, groupes in par_pays.items():
        tous = set().union(*groupes.values())
        lignes.append({
            "iso3": iso3,
            "entrees_gel": len(tous),
            "personnes": len(groupes.get("Personne physique", ())),
            "entites": len(groupes.get("Personne morale", ())),
            "navires": len(groupes.get("Navire", ())),
        })
    ecrire_csv("gels.csv", ["iso3", "entrees_gel", "personnes", "entites", "navires"], lignes)
    top_non_rattaches = sorted(non_rattaches.items(), key=lambda x: -x[1])[:25]
    return {
        "date_publication_registre": publication.get("DatePublication", ""),
        "nb_entrees_registre": len(entrees),
        "nb_entrees_sans_pays": sans_pays,
        "nb_pays": len(lignes),
        "noms_pays_non_rattaches": [f"{n} ({c})" for n, c in top_non_rattaches],
    }


if __name__ == "__main__":
    executer("gels", collecter)
