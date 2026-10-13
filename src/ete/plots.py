"""Charts for the model notebooks (week 3). Every function draws on a given axis."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

COLOURS = {"Regressão logística": "#7f8c8d", "Random Forest": "#27ae60", "Gradient Boosting (HistGB)": "#e67e22",
           "XGBoost": "#2980b9", "regra simples": "#8e44ad"}


def roc_and_pr(ax_roc, ax_pr, y, probabilities: dict, weight=None):
    """ROC curves (left) and precision-recall curves (right), one line per model."""
    for name, p in probabilities.items():
        fpr, tpr, _ = roc_curve(y, p, sample_weight=weight)
        precision, recall, _ = precision_recall_curve(y, p, sample_weight=weight)
        colour = COLOURS.get(name)
        ax_roc.plot(fpr, tpr, label=name, color=colour)
        ax_pr.plot(recall, precision, label=name, color=colour)
    ax_roc.plot([0, 1], [0, 1], color="black", linewidth=0.6, linestyle=":")
    ax_roc.set_xlabel("falsos alarmes (parte da não-água chamada água)")
    ax_roc.set_ylabel("recall (parte da água encontrada)")
    ax_roc.set_title("Curva ROC (melhor = canto superior esquerdo)")
    ax_roc.legend(loc="lower right")
    ax_pr.set_xlabel("recall (parte da água encontrada)")
    ax_pr.set_ylabel("precisão (parte do que foi chamado água que era água)")
    ax_pr.set_title("Curva precisão-recall (melhor = canto superior direito)")
    ax_pr.set_ylim(0.5, 1.01)


def fold_scores(ax, per_fold: pd.DataFrame, metric: str = "iou"):
    """Bar = mean over the spatial folds; dots = each fold. `per_fold` has columns modelo, fold, <metric>."""
    names = list(dict.fromkeys(per_fold["modelo"]))
    means = per_fold.groupby("modelo")[metric].mean().reindex(names)
    ax.bar(range(len(names)), means, color=[COLOURS.get(n, "#95a5a6") for n in names], alpha=0.75)
    for i, name in enumerate(names):
        values = per_fold.loc[per_fold["modelo"] == name, metric]
        ax.scatter(np.full(len(values), i), values, color="black", s=18, zorder=3)
        ax.text(i, means[name] + 0.012, f"{means[name]:.3f}", ha="center", fontsize=10)
    ax.set_xticks(range(len(names)), names, rotation=12)
    ax.set_ylabel(metric.upper())
    ax.set_ylim(max(0, per_fold[metric].min() - 0.1), 1.0)
    ax.set_title(f"{metric.upper()} por algoritmo (barra = média; pontos = cada grupo de blocos)")


def confusion(ax, y, predicted, weight, unit_km2_per_weight: float, labels=("não alagado", "alagado")):
    """2 x 2 table in km2: rows = reference, columns = model."""
    y, predicted, weight = np.asarray(y).astype(bool), np.asarray(predicted).astype(bool), np.asarray(weight, "float64")
    area = np.array([[weight[~y & ~predicted].sum(), weight[~y & predicted].sum()],
                     [weight[y & ~predicted].sum(), weight[y & predicted].sum()]]) * unit_km2_per_weight
    ax.imshow(area, cmap="Blues")
    for (i, j), value in np.ndenumerate(area):
        ax.text(j, i, f"{value:,.0f} km²\n({100 * value / area.sum():.1f} %)", ha="center", va="center",
                color="white" if value > area.max() / 2 else "black", fontsize=11)
    ax.set_xticks([0, 1], [f"modelo: {l}" for l in labels])
    ax.set_yticks([0, 1], [f"referência:\n{l}" for l in labels])
    ax.set_title("Matriz de confusão em área")


def calibration(ax, y, probability, weight=None, bins: int = 10):
    """Does a probability of 0.8 mean water 80 % of the time? Points on the diagonal = yes."""
    y, p = np.asarray(y, "float64"), np.asarray(probability, "float64")
    w = np.ones_like(p) if weight is None else np.asarray(weight, "float64")
    edges = np.linspace(0, 1, bins + 1)
    which = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    xs = [np.average(p[which == b], weights=w[which == b]) for b in range(bins) if (which == b).any()]
    ys = [np.average(y[which == b], weights=w[which == b]) for b in range(bins) if (which == b).any()]
    ax.plot([0, 1], [0, 1], color="black", linewidth=0.6, linestyle=":")
    ax.plot(xs, ys, marker="o", color="#2980b9")
    ax.set_xlabel("probabilidade dada pelo modelo")
    ax.set_ylabel("parte que era mesmo água")
    ax.set_title("Calibração (ideal: sobre a diagonal)")


def capture_curve(ax, flooded, score, weight=None, label=None, colour=None):
    """Share of the flooded area found when the land is ranked from highest to lowest score."""
    flooded, score = np.asarray(flooded, "float64"), np.asarray(score, "float64")
    w = np.ones_like(score) if weight is None else np.asarray(weight, "float64")
    order = np.argsort(-score)
    land = np.cumsum(w[order]) / w.sum()
    found = np.cumsum((w * flooded)[order]) / (w * flooded).sum()
    ax.plot(land, found, label=label, color=colour)
    ax.set_xlabel("parte do território, do mais para o menos suscetível")
    ax.set_ylabel("parte da área alagada encontrada")
