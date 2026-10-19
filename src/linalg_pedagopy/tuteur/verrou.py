"""Verrou sur les données d'exercice du tuteur (§7.3 Principe 5)."""

from __future__ import annotations

from typing import Any, Callable, Iterator, Mapping

from linalg_pedagopy.core.exceptions import LockedExerciseDataError
from linalg_pedagopy.objects.matrix import Matrix
from linalg_pedagopy.objects.vector import Vector

_LOCKED_MSG = (
    "Les données de cet exercice sont verrouillées tant que vous n'avez pas proposé et validé "
    "votre propre réponse avec ex.verifier(...). Effectuez le calcul par vous-même "
    "(ou demandez un indice avec ex.indice()) avant d'utiliser les méthodes automatiques !"
)


class LockedVector:
    """Enveloppe verrouillée autour d'un Vector d'exercice (§7.3 Principe 5)."""

    def __init__(self, vec: Vector, is_unlocked: Callable[[], bool], name: str = "x") -> None:
        self._vec = vec
        self._is_unlocked = is_unlocked
        self._name = name

    def _require_unlocked(self, method_name: str) -> Vector:
        if not self._is_unlocked():
            raise LockedExerciseDataError(
                f"Calcul direct '{self._name}.{method_name}' refusé : {_LOCKED_MSG}"
            )
        return self._vec

    @property
    def entries(self) -> tuple[Any, ...]:
        return self._vec.entries

    @property
    def size(self) -> int:
        return self._vec.size

    @property
    def shape(self) -> tuple[int, int]:
        return self._vec.shape

    def __len__(self) -> int:
        return len(self._vec)

    def __getitem__(self, index: int) -> Any:
        return self._vec[index]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._vec)

    def rms(self) -> Any:
        return self._require_unlocked("rms()").rms()

    def norm(self) -> Any:
        return self._require_unlocked("norm()").norm()

    def avg(self) -> Any:
        return self._require_unlocked("avg()").avg()

    def std(self) -> Any:
        return self._require_unlocked("std()").std()

    def demean(self) -> Vector:
        return self._require_unlocked("demean()").demean()

    def dot(self, other: Any) -> Any:
        u = self._require_unlocked("dot()")
        v = other._vec if isinstance(other, LockedVector) else other
        return u.dot(v)

    def distance(self, other: Any) -> Any:
        u = self._require_unlocked("distance()")
        v = other._vec if isinstance(other, LockedVector) else other
        return u.distance(v)

    def angle(self, other: Any) -> Any:
        u = self._require_unlocked("angle()")
        v = other._vec if isinstance(other, LockedVector) else other
        return u.angle(v)

    def correlation(self, other: Any) -> Any:
        u = self._require_unlocked("correlation()")
        v = other._vec if isinstance(other, LockedVector) else other
        return u.correlation(v)

    def __add__(self, other: Any) -> Vector:
        u = self._require_unlocked("+")
        v = other._vec if isinstance(other, LockedVector) else other
        return u + v

    def __sub__(self, other: Any) -> Vector:
        u = self._require_unlocked("-")
        v = other._vec if isinstance(other, LockedVector) else other
        return u - v

    def __mul__(self, scalar: Any) -> Vector:
        return self._require_unlocked("*") * scalar

    def __rmul__(self, scalar: Any) -> Vector:
        return scalar * self._require_unlocked("*")

    def __repr__(self) -> str:
        status = "déverrouillé" if self._is_unlocked() else "verrouillé"
        return f"LockedVector({list(self._vec.entries)}, {status})"

    def __str__(self) -> str:
        return str(self._vec)


class LockedMatrix:
    """Enveloppe verrouillée autour d'une Matrix d'exercice (§7.3 Principe 5)."""

    def __init__(self, mat: Matrix, is_unlocked: Callable[[], bool], name: str = "A") -> None:
        self._mat = mat
        self._is_unlocked = is_unlocked
        self._name = name

    def _require_unlocked(self, method_name: str) -> Matrix:
        if not self._is_unlocked():
            raise LockedExerciseDataError(
                f"Calcul direct '{self._name}.{method_name}' refusé : {_LOCKED_MSG}"
            )
        return self._mat

    @property
    def rows(self) -> int:
        return self._mat.rows

    @property
    def cols(self) -> int:
        return self._mat.cols

    @property
    def shape(self) -> tuple[int, int]:
        return self._mat.shape

    def __getitem__(self, key: Any) -> Any:
        return self._mat[key]

    @property
    def T(self) -> Matrix:
        return self._require_unlocked("T").T

    def gram(self) -> Matrix:
        return self._require_unlocked("gram()").gram()

    def rref(self) -> Any:
        return self._require_unlocked("rref()").rref()

    def rank(self) -> Any:
        return self._require_unlocked("rank()").rank()

    def nullspace(self) -> Any:
        return self._require_unlocked("nullspace()").nullspace()

    def inv(self, *, strict: bool = True) -> Any:
        return self._require_unlocked("inv()").inv(strict=strict)

    def solve(self, b: Any, *, strict: bool = False) -> Any:
        m = self._require_unlocked("solve()")
        rhs = b._vec if isinstance(b, LockedVector) else (b._mat if isinstance(b, LockedMatrix) else b)
        return m.solve(rhs, strict=strict)

    def __matmul__(self, other: Any) -> Any:
        m = self._require_unlocked("@")
        rhs = other._vec if isinstance(other, LockedVector) else (other._mat if isinstance(other, LockedMatrix) else other)
        return m @ rhs

    def __repr__(self) -> str:
        status = "déverrouillé" if self._is_unlocked() else "verrouillé"
        return f"LockedMatrix(shape={self._mat.shape}, {status})"

    def __str__(self) -> str:
        return str(self._mat)


class LockedNamespace:
    """Espace de noms ex.donnees exposant les données verrouillées d'un exercice."""

    def __init__(self, raw_data: Mapping[str, Any], is_unlocked: Callable[[], bool]) -> None:
        self._raw: dict[str, Any] = {}
        self._wrapped: dict[str, Any] = {}
        self._is_unlocked = is_unlocked

        for key, val in raw_data.items():
            if isinstance(val, Vector):
                self._raw[key] = val
                self._wrapped[key] = LockedVector(val, is_unlocked, name=key)
            elif isinstance(val, Matrix):
                self._raw[key] = val
                self._wrapped[key] = LockedMatrix(val, is_unlocked, name=key)
            elif isinstance(val, list) and val and isinstance(val[0], list):
                m = Matrix(val)
                self._raw[key] = m
                self._wrapped[key] = LockedMatrix(m, is_unlocked, name=key)
            elif isinstance(val, list):
                v = Vector(val)
                self._raw[key] = v
                self._wrapped[key] = LockedVector(v, is_unlocked, name=key)
            else:
                self._raw[key] = val
                self._wrapped[key] = val

    def __getattr__(self, name: str) -> Any:
        if name in self._wrapped:
            return self._wrapped[name]
        raise AttributeError(f"Aucune donnée nommée {name!r} dans cet exercice.")

    def __getitem__(self, name: str) -> Any:
        return self._wrapped[name]

    def keys(self) -> list[str]:
        return list(self._wrapped.keys())

    def raw_dict(self) -> dict[str, Any]:
        """Accès interne réservé aux vérificateurs du tuteur."""
        return dict(self._raw)

    def __repr__(self) -> str:
        items = ", ".join(f"{k}={v!r}" for k, v in self._wrapped.items())
        return f"DonneesExercice({items})"
