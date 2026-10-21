"""Vérificateurs du tuteur : un module par type de vérification.

Chaque module contient la fonction de vérification, son contrôle croisé (validation des fiches)
et l'enregistrement du type dans le registre (``tutor/registry.py``), forme attendue comprise.
L'import de ce paquet enregistre tous les types.
"""

from __future__ import annotations

from linalg_pedagopy.tutor.verifiers.commun import (
    VerificationResult,
    _eval_data_expr,
    _format_linear_comb,
    _parse_indexed_expr,
    raison_illisible,
)
from linalg_pedagopy.tutor.verifiers.contre_exemple import verify_counterexample
from linalg_pedagopy.tutor.verifiers.dimensions import verify_dimensions
from linalg_pedagopy.tutor.verifiers.egalites import verify_equalities
from linalg_pedagopy.tutor.verifiers.ensemble_valeurs import racines_reelles, verify_value_set
from linalg_pedagopy.tutor.verifiers.formule import verify_formula
from linalg_pedagopy.tutor.verifiers.labo import _verify_lab
from linalg_pedagopy.tutor.verifiers.matrice import verify_matrix
from linalg_pedagopy.tutor.verifiers.produit_scalaire import verify_inner_product
from linalg_pedagopy.tutor.verifiers.propriete import verify_property
from linalg_pedagopy.tutor.verifiers.valeur import verify_value

# French backward-compatible aliases
verifier_produit_scalaire = verify_inner_product
verifier_matrice = verify_matrix
verifier_formule = verify_formula
verifier_valeur = verify_value
verifier_ensemble_valeurs = verify_value_set
verifier_propriete = verify_property
verifier_contre_exemple = verify_counterexample
verifier_egalites = verify_equalities
verifier_dimensions = verify_dimensions

__all__ = [
    "VerificationResult",
    "_eval_data_expr",
    "_format_linear_comb",
    "_parse_indexed_expr",
    "_verify_lab",
    "racines_reelles",
    "raison_illisible",
    "verifier_contre_exemple",
    "verifier_dimensions",
    "verifier_egalites",
    "verifier_ensemble_valeurs",
    "verifier_formule",
    "verifier_matrice",
    "verifier_produit_scalaire",
    "verifier_propriete",
    "verifier_valeur",
    "verify_counterexample",
    "verify_dimensions",
    "verify_equalities",
    "verify_formula",
    "verify_inner_product",
    "verify_matrix",
    "verify_property",
    "verify_value",
    "verify_value_set",
]
