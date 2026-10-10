"""Outils partagés par les scripts de collecte.

Chaque script de collecte :
  1. télécharge une source publique gratuite ;
  2. écrit un CSV propre dans data/clean/ (une ligne par pays, codes ISO3) ;
  3. note le résultat (succès ou échec) dans data/status.json.

En cas d'échec, l'ancien CSV est conservé et l'échec est enregistré :
la carte l'affichera au lieu de présenter des données périmées comme fraîches.
"""

import csv
import json
import os
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_CLEAN = os.path.join(RACINE, "data", "clean")
FICHIER_STATUT = os.path.join(RACINE, "data", "status.json")
FICHIER_PAYS = os.path.join(RACINE, "site", "pays.geojson")

# Certaines API refusent les appels sans User-Agent (obligatoire pour la DG Trésor).
USER_AGENT = "mapproject/1.0 (carte publique non commerciale; https://github.com/arnchpt/mapproject)"


def maintenant():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def telecharger(url, essais=3, delai=10, timeout=120):
    """Télécharge une URL et renvoie les octets. Réessaie en cas d'erreur réseau."""
    derniere_erreur = None
    for i in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            derniere_erreur = e
            print(f"  essai {i + 1}/{essais} échoué pour {url} : {e}")
            time.sleep(delai)
    raise RuntimeError(f"Téléchargement impossible : {url} ({derniere_erreur})")


def telecharger_json(url, **kw):
    return json.loads(telecharger(url, **kw).decode("utf-8"))


def pays_reference():
    """Liste des pays du fond de carte : {iso3: {"iso2":..., "nom":..., "nom_en":...}}."""
    with open(FICHIER_PAYS, encoding="utf-8") as f:
        geo = json.load(f)
    pays = {}
    for feat in geo["features"]:
        p = feat["properties"]
        pays.setdefault(p["iso3"], {"iso2": p["iso2"], "nom": p["nom"], "nom_en": p["nom_en"]})
    return pays


def normaliser(texte):
    """Minuscules, sans accents ni ponctuation : sert à rapprocher des noms de pays."""
    t = unicodedata.normalize("NFKD", texte or "").encode("ascii", "ignore").decode()
    t = t.lower().replace("'", " ").replace("’", " ").replace("-", " ")
    garde = "".join(c if c.isalnum() or c == " " else " " for c in t)
    return " ".join(garde.split())


def ecrire_csv(nom_fichier, colonnes, lignes):
    os.makedirs(DOSSIER_CLEAN, exist_ok=True)
    chemin = os.path.join(DOSSIER_CLEAN, nom_fichier)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colonnes)
        w.writeheader()
        for ligne in sorted(lignes, key=lambda l: l["iso3"]):
            w.writerow(ligne)
    print(f"  {len(lignes)} lignes écrites dans data/clean/{nom_fichier}")


def lire_statut():
    if os.path.exists(FICHIER_STATUT):
        with open(FICHIER_STATUT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def noter_statut(couche, ok, **infos):
    """Enregistre le résultat d'une collecte dans data/status.json."""
    statut = lire_statut()
    entree = statut.get(couche, {})
    entree["derniere_tentative"] = maintenant()
    entree["ok"] = ok
    if ok:
        entree["derniere_reussite"] = entree["derniere_tentative"]
        entree.pop("erreur", None)
    entree.update(infos)
    statut[couche] = entree
    os.makedirs(os.path.dirname(FICHIER_STATUT), exist_ok=True)
    with open(FICHIER_STATUT, "w", encoding="utf-8") as f:
        json.dump(statut, f, ensure_ascii=False, indent=2, sort_keys=True)


def executer(couche, fonction):
    """Lance une collecte ; un échec est enregistré mais n'arrête pas les autres collectes."""
    print(f"== Collecte : {couche}")
    try:
        infos = fonction() or {}
        noter_statut(couche, True, **infos)
        print("  OK")
    except Exception as e:  # noqa: BLE001
        noter_statut(couche, False, erreur=str(e)[:500])
        print(f"  ÉCHEC : {e}")
