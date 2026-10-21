"""Évaluation sûre des expressions des fiches et des réponses saisies (interpréteur fondé sur ``ast``).

``eval(texte, {"__builtins__": {}}, noms)`` ne protège pas : un attribut comme ``__globals__``
rend les fonctions intégrées, donc tout Python. ``sympify`` d'une chaîne, ni ``Vector`` ou
``Matrix`` construits avec des chaînes (qui passent par ``sympify``), ne protègent pas davantage.

L'interpréteur parcourt l'arbre syntaxique et n'accepte qu'une liste blanche de constructions :
nombres, chaînes, listes, n-uplets, dictionnaires, ensembles, opérations arithmétiques,
comparaisons, opérateurs logiques, expression conditionnelle, indexation, accès à un attribut
et appel. Il refuse :

- les noms et les attributs qui commencent par « _ », les attributs qui donnent accès aux
  cadres d'exécution (``f_globals``…) et ``format`` (qui lit des attributs) ;
- les modules, comme valeur d'un nom ou d'un attribut ;
- les fonctions anonymes, les compréhensions, l'affectation ``:=``, les f-chaînes, le
  dépaquetage ``*`` et ``**`` ;
- toute chaîne contenant « ( » ou « __ » passée à un appel ou à une opération : ``sympify``
  l'exécuterait (sans parenthèse, une chaîne ne peut appeler aucune fonction ; le texte libre
  d'un générateur, ``'R^2, coefficients dans {0, 1}'``, reste admis) ;
- les puissances entières et les répétitions de listes démesurées.

Deux modes :

- :func:`evaluer` : sémantique de Python (``1/3`` vaut 0.333…), noms inconnus refusés
  (``NameError``). Remplace ``eval`` ;
- :func:`expression` : sémantique de ``sympify`` (entiers exacts, ``^`` lu comme puissance,
  nom inconnu lu comme symbole, fonctions usuelles de SymPy). Remplace ``sympify`` d'une chaîne.
"""

from __future__ import annotations

import ast
import operator
import re
import types
from typing import Any, Callable, Mapping

import sympy as sp

from linalg_pedagopy.core.field import symbols


class EvaluationRefusee(ValueError):
    """Construction refusée par l'interpréteur sûr."""


# Attributs sans « _ » qui donnent accès aux cadres d'exécution ou lisent des attributs
_ATTRIBUTS_INTERDITS = frozenset(
    {
        "format",
        "format_map",
        "mro",
        "f_globals",
        "f_locals",
        "f_builtins",
        "f_back",
        "f_code",
        "gi_frame",
        "gi_code",
        "cr_frame",
        "cr_code",
        "ag_frame",
        "ag_code",
        "tb_frame",
        "tb_next",
    }
)

# Une chaîne passée à un appel ou à une opération ne doit pouvoir appeler aucune fonction
_CHAINE_DE_CODE = re.compile(r"\(|__")

# Exposant entier maximal d'une puissance (au-delà, le calcul exact peut bloquer la séance)
_EXPOSANT_MAX = 10_000

_BINAIRES: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.MatMult: operator.matmul,
    ast.BitXor: operator.xor,
}

_UNAIRES: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}

_COMPARAISONS: dict[type[ast.cmpop], Callable[[Any, Any], Any]] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

# Fonctions et constantes de SymPy disponibles en mode « expression »
_SYMPY: dict[str, Any] = {
    "sqrt": sp.sqrt,
    "cbrt": sp.cbrt,
    "root": sp.root,
    "Rational": sp.Rational,
    "Integer": sp.Integer,
    "pi": sp.pi,
    "E": sp.E,
    "I": sp.I,
    "oo": sp.oo,
    "Abs": sp.Abs,
    "sign": sp.sign,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "factorial": sp.factorial,
    "binomial": sp.binomial,
    "floor": sp.floor,
    "ceiling": sp.ceiling,
    "Min": sp.Min,
    "Max": sp.Max,
    "re": sp.re,
    "im": sp.im,
    "conjugate": sp.conjugate,
    "gcd": sp.gcd,
    "lcm": sp.lcm,
}


def _refuser(message: str) -> EvaluationRefusee:
    return EvaluationRefusee(f"Expression refusée : {message}.")


def _controler_chaines(valeur: Any) -> None:
    """Refuse une chaîne de code transmise à un appel ou à une opération (y compris dans un conteneur)."""
    if isinstance(valeur, str):
        if _CHAINE_DE_CODE.search(valeur):
            raise _refuser(f"chaîne {valeur!r} transmise à un calcul (ni « ( » ni « __ » n'y sont admis)")
    elif isinstance(valeur, (list, tuple, set, frozenset)):
        for v in valeur:
            _controler_chaines(v)
    elif isinstance(valeur, dict):
        for k, v in valeur.items():
            _controler_chaines(k)
            _controler_chaines(v)


def _controler_valeur(valeur: Any, nom: str) -> Any:
    if isinstance(valeur, types.ModuleType):
        raise _refuser(f"« {nom} » est un module")
    return valeur


class _Interprete:
    def __init__(self, noms: Mapping[str, Any], *, sympy: bool) -> None:
        self.noms = noms
        self.sympy = sympy

    def visiter(self, noeud: ast.AST) -> Any:
        methode = getattr(self, f"_{type(noeud).__name__}", None)
        if methode is None:
            raise _refuser(f"construction {type(noeud).__name__} interdite")
        return methode(noeud)

    # Feuilles

    def _Expression(self, n: ast.Expression) -> Any:
        return self.visiter(n.body)

    def _Constant(self, n: ast.Constant) -> Any:
        v = n.value
        if isinstance(v, bool) or v is None:
            return v
        if isinstance(v, int):
            return sp.Integer(v) if self.sympy else v
        if isinstance(v, float):
            return sp.Float(repr(v)) if self.sympy else v
        if isinstance(v, complex) and not self.sympy:
            return v
        if isinstance(v, str):
            if self.sympy:
                raise _refuser("chaîne dans une expression")
            return v
        raise _refuser(f"constante {v!r}")

    def _Name(self, n: ast.Name) -> Any:
        if n.id.startswith("_"):
            raise _refuser(f"nom « {n.id} »")
        if n.id in self.noms:
            return _controler_valeur(self.noms[n.id], n.id)
        if self.sympy:
            if n.id in _SYMPY:
                return _SYMPY[n.id]
            return sp.Symbol(n.id)
        raise NameError(f"name '{n.id}' is not defined")

    # Conteneurs

    def _List(self, n: ast.List) -> Any:
        return [self.visiter(e) for e in n.elts]

    def _Tuple(self, n: ast.Tuple) -> Any:
        return tuple(self.visiter(e) for e in n.elts)

    def _Set(self, n: ast.Set) -> Any:
        return {self.visiter(e) for e in n.elts}

    def _Dict(self, n: ast.Dict) -> Any:
        if any(k is None for k in n.keys):
            raise _refuser("dépaquetage **")
        return {self.visiter(k): self.visiter(v) for k, v in zip(n.keys, n.values)}  # type: ignore[arg-type]

    # Opérations

    def _BinOp(self, n: ast.BinOp) -> Any:
        op = type(n.op)
        if op not in _BINAIRES:
            raise _refuser(f"opérateur {op.__name__}")
        gauche, droite = self.visiter(n.left), self.visiter(n.right)
        _controler_chaines(gauche)
        _controler_chaines(droite)
        if op is ast.Pow and _exposant_demesure(droite):
            raise _refuser("exposant trop grand")
        if op is ast.Mult and _repetition_demesuree(gauche, droite):
            raise _refuser("répétition trop grande")
        return _BINAIRES[op](gauche, droite)

    def _UnaryOp(self, n: ast.UnaryOp) -> Any:
        op = type(n.op)
        if op not in _UNAIRES:
            raise _refuser(f"opérateur {op.__name__}")
        valeur = self.visiter(n.operand)
        _controler_chaines(valeur)
        return _UNAIRES[op](valeur)

    def _BoolOp(self, n: ast.BoolOp) -> Any:
        resultat: Any = None
        for e in n.values:
            resultat = self.visiter(e)
            if isinstance(n.op, ast.And) and not resultat:
                return resultat
            if isinstance(n.op, ast.Or) and resultat:
                return resultat
        return resultat

    def _Compare(self, n: ast.Compare) -> Any:
        gauche = self.visiter(n.left)
        for op, terme in zip(n.ops, n.comparators):
            if type(op) not in _COMPARAISONS:
                raise _refuser(f"comparaison {type(op).__name__}")
            droite = self.visiter(terme)
            _controler_chaines(gauche)
            _controler_chaines(droite)
            if not _COMPARAISONS[type(op)](gauche, droite):
                return False
            gauche = droite
        return True

    def _IfExp(self, n: ast.IfExp) -> Any:
        return self.visiter(n.body) if self.visiter(n.test) else self.visiter(n.orelse)

    def _Subscript(self, n: ast.Subscript) -> Any:
        valeur = self.visiter(n.value)
        cle = self.visiter(n.slice)
        _controler_chaines(cle)
        return valeur[cle]

    def _Slice(self, n: ast.Slice) -> Any:
        return slice(
            *(None if e is None else self.visiter(e) for e in (n.lower, n.upper, n.step))
        )

    def _Attribute(self, n: ast.Attribute) -> Any:
        if n.attr.startswith("_") or n.attr in _ATTRIBUTS_INTERDITS:
            raise _refuser(f"attribut « {n.attr} »")
        return _controler_valeur(getattr(self.visiter(n.value), n.attr), n.attr)

    def _Call(self, n: ast.Call) -> Any:
        fonction = self.visiter(n.func)
        if not callable(fonction):
            raise _refuser("appel d'un objet qui n'est pas une fonction")
        args = []
        for a in n.args:
            if isinstance(a, ast.Starred):
                raise _refuser("dépaquetage *")
            args.append(self.visiter(a))
        kwargs = {}
        for k in n.keywords:
            if k.arg is None:
                raise _refuser("dépaquetage **")
            kwargs[k.arg] = self.visiter(k.value)
        _controler_chaines(args)
        _controler_chaines(kwargs)
        return fonction(*args, **kwargs)


def _exposant_demesure(exposant: Any) -> bool:
    try:
        return abs(int(exposant)) > _EXPOSANT_MAX and exposant == int(exposant)
    except (TypeError, ValueError, OverflowError):
        return False


def _repetition_demesuree(gauche: Any, droite: Any) -> bool:
    """``[0] * 10**9`` épuiserait la mémoire."""
    for seq, n in ((gauche, droite), (droite, gauche)):
        if isinstance(seq, (list, tuple, str)) and isinstance(n, (int, sp.Integer)):
            if int(n) * max(len(seq), 1) > _EXPOSANT_MAX:
                return True
    return False


def _analyser(texte: str) -> ast.Expression:
    return ast.parse(str(texte).strip(), mode="eval")


def evaluer(texte: str, noms: Mapping[str, Any]) -> Any:
    """Évalue une expression avec la sémantique de Python ; seuls ``noms`` sont connus."""
    return _Interprete(noms, sympy=False).visiter(_analyser(texte))


def expression(texte: str, noms: Mapping[str, Any] | None = None) -> Any:
    """Lit une expression comme ``sympify`` : entiers exacts, ``^`` pour la puissance, nom inconnu = symbole."""
    # Comme sympify (convert_xor), « ^ » est remplacé avant l'analyse : il garde la priorité de « ** »
    texte = str(texte).replace("^", "**")
    return sp.sympify(_Interprete(noms or {}, sympy=True).visiter(_analyser(texte)))


def en_expression(valeur: Any, noms: Mapping[str, Any] | None = None) -> Any:
    """``sympify`` sans exécution de code : les chaînes, même dans un conteneur, passent par :func:`expression`."""
    return sp.sympify(_sans_chaines(valeur, noms))


def _sans_chaines(valeur: Any, noms: Mapping[str, Any] | None) -> Any:
    if isinstance(valeur, str):
        return expression(valeur, noms)
    if isinstance(valeur, (list, tuple)):
        return type(valeur)(_sans_chaines(v, noms) for v in valeur)
    return valeur


def lire_donnee(valeur: Any) -> Any:
    """Donnée d'une fiche : les chaînes d'une liste (``[1, a]``) deviennent des expressions à symboles réels."""
    if isinstance(valeur, str):
        expr = expression(valeur)
        return expr.xreplace({s: symbols(s.name)[0] for s in expr.free_symbols if isinstance(s, sp.Symbol)})
    if isinstance(valeur, list):
        return [lire_donnee(v) for v in valeur]
    return valeur
