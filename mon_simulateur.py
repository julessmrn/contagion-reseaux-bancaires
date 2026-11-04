"""Votre simulateur de cascade : c'est le fichier que votre équipe complète.

Écrivez les deux fonctions ci-dessous, puis vérifiez-les depuis le dossier du dépôt :

    python aides/verifier_simulateur.py mon_simulateur.py

Le vérificateur lance les 9 tests du sujet et explique chaque échec.
Ne changez pas le nom des fonctions ni leurs arguments : les aides les appellent ainsi.
"""

import os
import sys

import networkx as nx

# Rend le dossier aides/ importable, que ce fichier soit lancé ou importé depuis un notebook.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "aides"))
from aides_contagion import depasse_capital  # noqa: E402


def construire_graphe(banques_r, expositions_r):
    """Construit le graphe orienté pondéré d'UN réseau.

    banques_r : lignes de banques.csv pour ce réseau (colonnes banque_id, capital).
    expositions_r : lignes de expositions.csv pour ce réseau (colonnes debiteur_id, creancier_id, montant).

    Renvoie un nx.DiGraph avec :
      * un sommet par banque, avec l'attribut "capital", y compris les banques isolées ;
      * une arête debiteur -> creancier par dette, avec l'attribut "montant"
        (la banque i doit le montant à la banque j : si i fait défaut, j perd).
    """
    # Accepte un DataFrame pandas ou une liste de dictionnaires (csv.DictReader)
    if hasattr(banques_r, "to_dict"):
        banques_r = banques_r.to_dict("records")
    if hasattr(expositions_r, "to_dict"):
        expositions_r = expositions_r.to_dict("records")

    G = nx.DiGraph()

    # 1. D'abord toutes les banques, pour garder les banques isolées
    for ligne in banques_r:
        G.add_node(str(ligne["banque_id"]), capital=float(ligne["capital"]))

    # 2. Puis les dettes : débiteur -> créancier
    for ligne in expositions_r:
        G.add_edge(str(ligne["debiteur_id"]), str(ligne["creancier_id"]),
                   montant=float(ligne["montant"]))

    return G


def simuler(G, origine, lam):
    """Simule la cascade à seuil du sujet (section 3) à partir de la banque d'origine.

    G : graphe renvoyé par construire_graphe (ne le modifiez pas).
    origine : identifiant de la banque en défaut au départ (son défaut est imposé).
    lam : fraction de perte, entre 0 et 1.

    Renvoie le couple (defauts, nouveaux_par_etape) :
      * defauts : ensemble (set) des banques en défaut à la fin, origine comprise ;
      * nouveaux_par_etape : liste du nombre de nouveaux défauts aux étapes 1, 2, 3...,
        sans l'origine et sans zéro final ([] si rien ne se propage).

    Pour comparer une perte au capital, utilisez depasse_capital(perte, capital) :
    une perte exactement égale au capital ne provoque pas de défaut.
    """
    defauts = {origine}      # l'origine est en défaut d'office
    pertes = {}              # perte cumulée de chaque banque encore solvable
    vague = [origine]        # banques qui propagent leur défaut à l'étape suivante
    nouveaux_par_etape = []

    while vague:
        # 1. Les banques de la vague précédente transmettent leurs pertes
        touchees = set()
        for debiteur in vague:
            for creancier in G.successors(debiteur):      # arête debiteur -> creancier
                if creancier in defauts:
                    continue
                perte = lam * G[debiteur][creancier]["montant"]   # <- formule de perte (voir plus bas)
                pertes[creancier] = pertes.get(creancier, 0.0) + perte
                touchees.add(creancier)

        # 2. Nouveaux défauts de l'étape, décidés uniquement avec depasse_capital
        vague = [b for b in touchees
                 if depasse_capital(pertes[b], G.nodes[b]["capital"])]

        # 3. Enregistrement (pas de zéro final : on n'ajoute que si la vague n'est pas vide)
        if vague:
            defauts.update(vague)
            nouveaux_par_etape.append(len(vague))

    return defauts, nouveaux_par_etape