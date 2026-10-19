"""Figures géométriques 2D et 3D avec Matplotlib."""

from __future__ import annotations

from typing import Any, Sequence

from linalg_pedagopy.algorithms.gram_schmidt import GSResult, GramSchmidt
from linalg_pedagopy.algorithms.least_squares import LSResult
from linalg_pedagopy.objects.vector import Vector
from linalg_pedagopy.trace.tracer import suspend_tracing


def _require_matplotlib() -> Any:
    try:
        import matplotlib.pyplot as plt
        return plt
    except ImportError as exc:
        raise ImportError(
            "Le module plot requiert matplotlib (pip install linalg_pedagopy[plot])."
        ) from exc


def _vec_floats(v: Vector) -> list[float]:
    return [float(e.evalf()) for e in v.entries]


def plot_linear_combination_2d(
    u: Vector,
    v: Vector,
    c1: Any = 1,
    c2: Any = 1,
    *,
    ax: Any = None,
) -> Any:
    """Trace en 2D la combinaison linéaire w = c1 * u + c2 * v (règle du parallélogramme)."""
    if len(u) != 2 or len(v) != 2:
        raise ValueError("plot_linear_combination_2d requiert des vecteurs de dimension 2.")
    plt = _require_matplotlib()
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))
    else:
        fig = ax.figure

    with suspend_tracing():
        u_s = c1 * u
        v_s = c2 * v
        w = u_s + v_s

    uf = _vec_floats(u_s)
    vf = _vec_floats(v_s)
    wf = _vec_floats(w)

    ax.axhline(0, color="gray", lw=0.8)
    ax.axvline(0, color="gray", lw=0.8)
    ax.quiver(0, 0, uf[0], uf[1], angles="xy", scale_units="xy", scale=1, color="tab:blue", label="c₁ u")
    ax.quiver(0, 0, vf[0], vf[1], angles="xy", scale_units="xy", scale=1, color="tab:green", label="c₂ v")
    ax.quiver(uf[0], uf[1], vf[0], vf[1], angles="xy", scale_units="xy", scale=1, color="tab:green", alpha=0.4)
    ax.quiver(0, 0, wf[0], wf[1], angles="xy", scale_units="xy", scale=1, color="tab:red", label="c₁ u + c₂ v")

    xs = [0.0, uf[0], vf[0], wf[0]]
    ys = [0.0, uf[1], vf[1], wf[1]]
    pad = max(1.0, 0.2 * max(max(xs) - min(xs), max(ys) - min(ys)))
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    ax.set_title("Combinaison linéaire dans R²")
    return fig


def plot_orthogonal_projection_2d(
    a: Vector,
    q: Vector,
    *,
    ax: Any = None,
) -> Any:
    """Trace la projection orthogonale de a sur la droite engendrée par q dans R²."""
    if len(a) != 2 or len(q) != 2:
        raise ValueError("plot_orthogonal_projection_2d requiert des vecteurs de dimension 2.")
    plt = _require_matplotlib()
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))
    else:
        fig = ax.figure

    with suspend_tracing():
        proj = (q.dot(a) / q.norm_sq()) * q
        r = a - proj

    af = _vec_floats(a)
    pf = _vec_floats(proj)
    rf = _vec_floats(r)

    ax.axhline(0, color="gray", lw=0.8)
    ax.axvline(0, color="gray", lw=0.8)
    ax.quiver(0, 0, af[0], af[1], angles="xy", scale_units="xy", scale=1, color="tab:blue", label="a")
    ax.quiver(0, 0, pf[0], pf[1], angles="xy", scale_units="xy", scale=1, color="tab:orange", label="proj_q(a)")
    ax.quiver(pf[0], pf[1], rf[0], rf[1], angles="xy", scale_units="xy", scale=1, color="tab:red", label="a - proj_q(a)")
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    ax.set_title("Projection orthogonale")
    return fig


def plot_gram_schmidt_2d(
    vectors: Sequence[Vector],
    *,
    ax: Any = None,
) -> Any:
    """Trace les vecteurs initiaux et la base orthonormée issue de Gram-Schmidt en 2D."""
    plt = _require_matplotlib()
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))
    else:
        fig = ax.figure

    with suspend_tracing():
        gs_res = GramSchmidt(vectors).run()
        assert isinstance(gs_res, GSResult)

    ax.axhline(0, color="gray", lw=0.8)
    ax.axvline(0, color="gray", lw=0.8)
    for idx, v in enumerate(vectors, start=1):
        vf = _vec_floats(v)
        ax.quiver(0, 0, vf[0], vf[1], angles="xy", scale_units="xy", scale=1, color="tab:blue", alpha=0.6, label=f"a_{idx}")
    for idx, q in enumerate(gs_res.orthonormal, start=1):
        qf = _vec_floats(q)
        ax.quiver(0, 0, qf[0], qf[1], angles="xy", scale_units="xy", scale=1, color="tab:red", label=f"q_{idx}")

    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    ax.set_title("Étapes de Gram-Schmidt")
    return fig


def plot_least_squares_fit(
    x_data: Sequence[Any],
    y_data: Sequence[Any],
    ls_result: LSResult,
    *,
    ax: Any = None,
) -> Any:
    """Trace le nuage de points, la droite ajustée et les résidus verticaux."""
    plt = _require_matplotlib()
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 5))
    else:
        fig = ax.figure

    xs = [float(x) for x in x_data]
    ys = [float(y) for y in y_data]
    y_hats = _vec_floats(ls_result.y_hat)

    ax.scatter(xs, ys, color="tab:blue", label="Données (x_i, y_i)", zorder=3)
    order = sorted(range(len(xs)), key=lambda k: xs[k])
    ax.plot(
        [xs[k] for k in order],
        [y_hats[k] for k in order],
        color="tab:orange",
        lw=2,
        label="Modèle ajusté y_hat = A x_hat",
    )
    for xi, yi, yhi in zip(xs, ys, y_hats):
        ax.plot([xi, xi], [yi, yhi], color="tab:red", linestyle="--", lw=1)

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    ax.set_title("Ajustement au sens des moindres carrés")
    return fig


def plot_least_squares_geometry_3d(ls_result: LSResult) -> Any:
    """Vue géométrique 3D de b, sa projection orthogonale y_hat = A x_hat et le résidu r_hat."""
    if len(ls_result.b) != 3:
        raise ValueError("plot_least_squares_geometry_3d requiert b dans R³ (m = 3).")
    plt = _require_matplotlib()
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")

    bf = _vec_floats(ls_result.b)
    yf = _vec_floats(ls_result.y_hat)
    rf = _vec_floats(ls_result.r_hat)

    ax.quiver(0, 0, 0, bf[0], bf[1], bf[2], color="tab:blue", label="b")
    ax.quiver(0, 0, 0, yf[0], yf[1], yf[2], color="tab:green", label="ŷ = A x̂")
    ax.quiver(bf[0], bf[1], bf[2], rf[0], rf[1], rf[2], color="tab:red", label="r̂ = A x̂ - b")
    ax.set_title("Géométrie 3D des moindres carrés (A^T r̂ = 0)")
    ax.legend()
    return fig
