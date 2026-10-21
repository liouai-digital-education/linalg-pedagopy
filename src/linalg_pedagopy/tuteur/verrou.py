"""Proxys verrouillés protégeant les données des exercices du tuteur."""

from __future__ import annotations

from typing import Any, Callable, Iterator, Mapping
from weakref import WeakKeyDictionary

from linalg_pedagopy.core.exceptions import LockedExerciseDataError
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.tuteur.evaluation_sure import lire_donnee

_LOCKED_MSG = (
    "Les données de cet exercice sont verrouillées tant que vous n'avez pas proposé et validé "
    "votre propre réponse avec ex.verifier(...). Effectuez le calcul par vous-même "
    "(ou demandez un indice avec ex.indice()) avant d'utiliser les méthodes automatiques !"
)

# Private vault keyed by object identity via weak references so no underlying Vector/Matrix
# or unlock callback is ever stored on instance __dict__ or inspectable via vars()/getattr().
_LOCK_VAULT: WeakKeyDictionary[Any, dict[str, Any]] = WeakKeyDictionary()


def _unwrap_locked_arg(obj: Any) -> Any:
    if isinstance(obj, LockedVector):
        return obj._require_unlocked("argument")
    if isinstance(obj, LockedMatrix):
        return obj._require_unlocked("argument")
    return obj


class LockedVector:
    """Vecteur d'exercice verrouillé, protégé contre la modification."""

    __slots__ = ("__weakref__",)
    _is_locked_tutor_proxy = True

    def __init__(self, vec: Vector, is_unlocked: Callable[[], bool], name: str = "x") -> None:
        _LOCK_VAULT[self] = {
            "vec": vec,
            "is_unlocked": is_unlocked,
            "name": name,
        }

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("LockedVector est immuable et protégé par le tuteur.")

    def _state(self) -> dict[str, Any]:
        return _LOCK_VAULT[self]

    def _require_unlocked(self, method_name: str) -> Vector:
        st = self._state()
        if not st["is_unlocked"]():
            raise LockedExerciseDataError(
                f"Calcul direct '{st['name']}.{method_name}' refusé : {_LOCKED_MSG}"
            )
        return st["vec"]  # type: ignore[no-any-return]

    def _unwrap_for_constructor(self, caller: str) -> Vector:
        return self._require_unlocked(caller)

    @property
    def entries(self) -> tuple[Any, ...]:
        """Coefficients du vecteur ; refusé tant que l'exercice est verrouillé."""
        return self._require_unlocked("entries").entries

    @property
    def size(self) -> int:
        """Taille du vecteur, accessible même verrouillé."""
        return self._state()["vec"].size  # type: ignore[no-any-return]

    @property
    def shape(self) -> tuple[int, int]:
        """Forme ``(n, 1)`` du vecteur, accessible même verrouillé."""
        return self._state()["vec"].shape  # type: ignore[no-any-return]

    def __len__(self) -> int:
        return len(self._state()["vec"])

    def __getitem__(self, index: int) -> Any:
        return self._require_unlocked("__getitem__")[index]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._require_unlocked("__iter__"))

    def rms(self) -> Any:
        """Moyenne quadratique (``Vector.rms``) ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("rms()").rms()

    def norm(self) -> Any:
        """Norme euclidienne (``Vector.norm``) ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("norm()").norm()

    def norm_sq(self) -> Any:
        """Carré de la norme (``Vector.norm_sq``) ; refusé tant que l'exercice est verrouillé."""
        return self._require_unlocked("norm_sq()").norm_sq()

    def avg(self) -> Any:
        """Moyenne des coefficients (``Vector.avg``) ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("avg()").avg()

    def std(self) -> Any:
        """Écart type (``Vector.std``) ; refusé tant que l'exercice est verrouillé."""
        return self._require_unlocked("std()").std()

    def demean(self) -> Vector:
        """Vecteur centré (``Vector.demean``) ; refusé tant que l'exercice est verrouillé."""
        return self._require_unlocked("demean()").demean()

    def dot(self, other: Any) -> Any:
        """Produit scalaire avec ``other`` (``Vector.dot``) ; refusé tant que l'exercice est verrouillé."""
        u = self._require_unlocked("dot()")
        v = _unwrap_locked_arg(other)
        return u.dot(v)

    def distance(self, other: Any) -> Any:
        """Distance à ``other`` (``Vector.distance``) ; refusée tant que l'exercice est verrouillé."""
        u = self._require_unlocked("distance()")
        v = _unwrap_locked_arg(other)
        return u.distance(v)

    def angle(self, other: Any) -> Any:
        """Angle avec ``other`` (``Vector.angle``) ; refusé tant que l'exercice est verrouillé."""
        u = self._require_unlocked("angle()")
        v = _unwrap_locked_arg(other)
        return u.angle(v)

    def correlation(self, other: Any) -> Any:
        """Coefficient de corrélation avec ``other`` (``Vector.correlation``) ; refusé tant que l'exercice est verrouillé."""
        u = self._require_unlocked("correlation()")
        v = _unwrap_locked_arg(other)
        return u.correlation(v)

    def __add__(self, other: Any) -> Vector:
        u = self._require_unlocked("+")
        v = _unwrap_locked_arg(other)
        return u + v

    def __sub__(self, other: Any) -> Vector:
        u = self._require_unlocked("-")
        v = _unwrap_locked_arg(other)
        return u - v

    def __mul__(self, scalar: Any) -> Vector:
        return self._require_unlocked("*") * scalar

    def __rmul__(self, scalar: Any) -> Vector:
        return scalar * self._require_unlocked("*")

    def __repr__(self) -> str:
        st = self._state()
        status = "déverrouillé" if st["is_unlocked"]() else "verrouillé"
        return f"LockedVector(size={st['vec'].size}, {status})"

    def __str__(self) -> str:
        return str(self._state()["vec"])


class LockedMatrix:
    """Matrice d'exercice verrouillée, protégée contre la modification."""

    __slots__ = ("__weakref__",)
    _is_locked_tutor_proxy = True

    def __init__(self, mat: Matrix, is_unlocked: Callable[[], bool], name: str = "A") -> None:
        _LOCK_VAULT[self] = {
            "mat": mat,
            "is_unlocked": is_unlocked,
            "name": name,
        }

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("LockedMatrix est immuable et protégée par le tuteur.")

    def _state(self) -> dict[str, Any]:
        return _LOCK_VAULT[self]

    def _require_unlocked(self, method_name: str) -> Matrix:
        st = self._state()
        if not st["is_unlocked"]():
            raise LockedExerciseDataError(
                f"Calcul direct '{st['name']}.{method_name}' refusé : {_LOCKED_MSG}"
            )
        return st["mat"]  # type: ignore[no-any-return]

    def _unwrap_for_constructor(self, caller: str) -> Matrix:
        return self._require_unlocked(caller)

    @property
    def rows(self) -> int:
        """Nombre de lignes, accessible même verrouillé."""
        return self._state()["mat"].rows  # type: ignore[no-any-return]

    @property
    def cols(self) -> int:
        """Nombre de colonnes, accessible même verrouillé."""
        return self._state()["mat"].cols  # type: ignore[no-any-return]

    @property
    def shape(self) -> tuple[int, int]:
        """Forme ``(lignes, colonnes)``, accessible même verrouillée."""
        return self._state()["mat"].shape  # type: ignore[no-any-return]

    def __getitem__(self, key: Any) -> Any:
        return self._require_unlocked("__getitem__")[key]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._require_unlocked("__iter__"))

    @property
    def T(self) -> Matrix:
        """Transposée ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("T").T

    def gram(self) -> Matrix:
        """Matrice de Gram ``AᵀA`` (``Matrix.gram``) ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("gram()").gram()

    def rref(self, *, assumptions: Any = None) -> Any:
        """Forme échelonnée réduite (``Matrix.rref``) ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("rref()").rref(assumptions=assumptions)

    def rank(self, *, assumptions: Any = None) -> Any:
        """Rang (``Matrix.rank``) ; refusé tant que l'exercice est verrouillé."""
        return self._require_unlocked("rank()").rank(assumptions=assumptions)

    def nullspace(self, *, assumptions: Any = None) -> Any:
        """Base du noyau (``Matrix.nullspace``) ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("nullspace()").nullspace(assumptions=assumptions)

    def inv(self, *, assumptions: Any = None, strict: bool = True) -> Any:
        """Inverse (``Matrix.inv``) ; refusée tant que l'exercice est verrouillé."""
        return self._require_unlocked("inv()").inv(assumptions=assumptions, strict=strict)

    def solve(self, b: Any, *, assumptions: Any = None, strict: bool = False) -> Any:
        """Ensemble des solutions de ``A x = b`` (``Matrix.solve``) ; refusé tant que l'exercice est verrouillé."""
        m = self._require_unlocked("solve()")
        rhs = _unwrap_locked_arg(b)
        return m.solve(rhs, assumptions=assumptions, strict=strict)

    def __matmul__(self, other: Any) -> Any:
        m = self._require_unlocked("@")
        rhs = _unwrap_locked_arg(other)
        return m @ rhs

    def __repr__(self) -> str:
        st = self._state()
        status = "déverrouillé" if st["is_unlocked"]() else "verrouillé"
        return f"LockedMatrix(shape={st['mat'].shape}, {status})"

    def __str__(self) -> str:
        return str(self._state()["mat"])


class LockedNamespace:
    """Espace de noms des données verrouillées d'un exercice (``ex.donnees``)."""

    __slots__ = ("__weakref__",)

    def __init__(self, raw_data: Mapping[str, Any], is_unlocked: Callable[[], bool]) -> None:
        raw: dict[str, Any] = {}
        wrapped: dict[str, Any] = {}

        for key, val in raw_data.items():
            if isinstance(val, Vector):
                raw[key] = val
                wrapped[key] = LockedVector(val, is_unlocked, name=key)
            elif isinstance(val, Matrix):
                raw[key] = val
                wrapped[key] = LockedMatrix(val, is_unlocked, name=key)
            elif isinstance(val, list) and val and isinstance(val[0], list):
                m = Matrix(lire_donnee(val))
                raw[key] = m
                wrapped[key] = LockedMatrix(m, is_unlocked, name=key)
            elif isinstance(val, list):
                v = Vector(lire_donnee(val))
                raw[key] = v
                wrapped[key] = LockedVector(v, is_unlocked, name=key)
            else:
                raw[key] = val
                wrapped[key] = val

        _LOCK_VAULT[self] = {
            "raw": raw,
            "wrapped": wrapped,
            "is_unlocked": is_unlocked,
        }

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("LockedNamespace est immuable et protégé par le tuteur.")

    def __getattr__(self, name: str) -> Any:
        wrapped = _LOCK_VAULT[self]["wrapped"]
        if name in wrapped:
            return wrapped[name]
        raise AttributeError(f"Aucune donnée nommée {name!r} dans cet exercice.")

    def __getitem__(self, name: str) -> Any:
        return _LOCK_VAULT[self]["wrapped"][name]

    def keys(self) -> list[str]:
        """Noms des données de l'exercice, accessibles même verrouillées."""
        return list(_LOCK_VAULT[self]["wrapped"].keys())

    def raw_dict(self) -> dict[str, Any]:
        """Renvoie les données brutes uniquement si la session est déverrouillée (ou mode enseignant)."""
        st = _LOCK_VAULT[self]
        if not st["is_unlocked"]():
            raise LockedExerciseDataError(
                f"Accès direct à 'raw_dict()' refusé : {_LOCKED_MSG}"
            )
        return dict(st["raw"])

    def __repr__(self) -> str:
        wrapped = _LOCK_VAULT[self]["wrapped"]
        items = ", ".join(f"{k}={v!r}" for k, v in wrapped.items())
        return f"ExerciseData({items})"


def _get_namespace_raw_dict(ns: LockedNamespace) -> dict[str, Any]:
    """Données brutes d'un exercice, pour les vérificateurs, sans les exposer à l'étudiant."""
    return dict(_LOCK_VAULT[ns]["raw"])
