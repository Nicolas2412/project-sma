################################################################################
# PROJET : SMA (Systèmes Multi-Agents) - Groupe 6
# DATE DE CRÉATION : 16/04/2026
#
# MEMBRES DU GROUPE :
#   - Nicolas Charronidere
#   - Paul Guimbert
#
# FILE: compare_strategies.py
#
# USAGE : python compare_strategies.py
################################################################################

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from model import RobotModel
from objects import Waste

# CONFIGURATION

# Stratégies à comparer
STRATEGIES = ["random", "naive", "smart"]

# Paramètres fixes identiques pour tous les runs
FIXED_PARAMS = {
    "n_green_agents":  1,
    "n_yellow_agents": 1,
    "n_red_agents":    1,
    "n_green_wastes":  10,
    "n_yellow_wastes": 10,
    "n_red_wastes":    10,
    "height":          10,
    "width_z1":        10,
    "width_z2":        10,
    "width_z3":        10,
}

N_RUNS = 10
MAX_STEPS = 20_000

PALETTE = ["#2196F3", "#FF5722", "#4CAF50", "#9C27B0", "#FF9800"]

# HELPERS

def count_wastes(model):
    """Retourne le nombre de Waste par couleur (green, yellow, red)."""
    green = sum(1 for a in model.agents if isinstance(
        a, Waste) and a.color == 1)
    yellow = sum(1 for a in model.agents if isinstance(
        a, Waste) and a.color == 2)
    red = sum(1 for a in model.agents if isinstance(a, Waste) and a.color == 3)
    return green, yellow, red


def run_simulation(strategy: str, seed: int) -> dict:
    """
    Lance un run complet avec la stratégie donnée.

    Retourne un dict avec :
        - steps           : nombre de steps jusqu'à la fin (ou MAX_STEPS)
        - finished        : True si model.running est passé à False
        - waste_over_time : liste du nb total de déchets à chaque step
    """
    model = RobotModel(strategy=strategy, seed=seed, **FIXED_PARAMS)

    g, y, r = count_wastes(model)
    waste_over_time = [g + y + r]

    for step in range(1, MAX_STEPS + 1):
        model.step()
        g, y, r = count_wastes(model)
        waste_over_time.append(g + y + r)

        # model.running est mis à False dans model.step() 
        # quand la condition d'arret est satisfaite
        if not model.running:
            return {
                "steps": step,
                "finished": True,
                "waste_over_time": waste_over_time,
            }

    # Run non terminé
    return {
        "steps": MAX_STEPS,
        "finished": False,
        "waste_over_time": waste_over_time,
    }


# COLLECTE DES DONNÉES

def collect_results() -> dict:
    """
    Lance N_RUNS runs pour chaque stratégie.

    Structure retournée :
    {
    "naive":  {"steps": [...], "finished": [...], "waste_curves": [[...], ...]},
    "random": {...},
    ...
    }
    """
    results = {}

    for strategy in STRATEGIES:
        print(f"\n▶  Stratégie : {strategy}")
        steps_list = []
        finished_list = []
        waste_curves = []

        for run in range(N_RUNS):
            seed = run * 42  # seeds reproductibles
            r = run_simulation(strategy, seed)

            steps_list.append(r["steps"])
            finished_list.append(r["finished"])
            waste_curves.append(r["waste_over_time"])

            status = "✓" if r["finished"] else f"✗ (MAX_STEPS={MAX_STEPS})"
            print(
                f"   run {run + 1:2d}/{N_RUNS}  →  {r['steps']:5d} steps  {status}")

        results[strategy] = {
            "steps":        steps_list,
            "finished":     finished_list,
            "waste_curves": waste_curves,
        }

    return results


# VISUALISATION

def plot_results(results: dict):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        f"Comparaison des stratégies  —  {N_RUNS} runs, paramètres fixes",
        fontsize=13, fontweight="bold"
    )

    # Distribution des steps
    ax1 = axes[0]
    all_steps = [results[s]["steps"] for s in STRATEGIES]
    bp = ax1.boxplot(
        all_steps,
        labels=STRATEGIES,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=2),
    )
    for patch, color in zip(bp["boxes"], PALETTE):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Annotation de la médiane
    y_max = max(max(s) for s in all_steps)
    offset = y_max * 0.02
    for i, (steps, whisker) in enumerate(zip(all_steps, bp["whiskers"][1::2])):
        median = np.median(steps)
        whisker_top = whisker.get_ydata()[1]
        ax1.text(
            i + 1, whisker_top + offset,
            f"med={median:.0f}",
            ha="center", va="bottom", fontsize=8, color="black",
            bbox=dict(boxstyle="round,pad=0.2",
                    fc="white", ec="none", alpha=0.7),
        )

    ax1.set_title("Distribution du nombre de steps jusqu'à la fin")
    ax1.set_ylabel("Nombre de steps")
    ax1.set_xlabel("Stratégie")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # Evolution moyenne des déchets
    ax2 = axes[1]
    legend_handles = []

    for i, strategy in enumerate(STRATEGIES):
        color = PALETTE[i]
        curves = results[strategy]["waste_curves"]

        max_len = max(len(c) for c in curves)
        padded = [c + [0] * (max_len - len(c)) for c in curves]

        arr = np.array(padded, dtype=float)
        mean = arr.mean(axis=0)
        std = arr.std(axis=0)
        x = np.arange(max_len)

        ax2.plot(x, mean, color=color, linewidth=2, label=strategy)
        ax2.fill_between(x, mean - std, mean + std, color=color, alpha=0.15)

        legend_handles.append(
            mpatches.Patch(color=color, alpha=0.8,
                        label=f"{strategy}  (médiane={np.median(results[strategy]['steps']):.0f} steps)")
        )

    ax2.set_title("Évolution moyenne des déchets restants (± écart-type)")
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Nombre de déchets restants")
    ax2.legend(handles=legend_handles, fontsize=9)
    ax2.grid(linestyle="--", alpha=0.4)
    ax2.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig("images/results/comparison_results.png", dpi=150, bbox_inches="tight")
    print("\nGraphique sauvegardé : comparison_results.png")
    plt.show()


# RÉSUMÉ TEXTE

def print_summary(results: dict):
    print("\n" + "═" * 55)
    print("  RÉSUMÉ")
    print("═" * 55)
    print(
        f"  {'Stratégie':<18} {'Médiane':>8} {'Moyenne':>8} {'Std':>8} {'Taux fin':>9}")
    print("─" * 55)

    for strategy in STRATEGIES:
        steps = results[strategy]["steps"]
        finished = results[strategy]["finished"]
        rate = sum(finished) / len(finished) * 100
        print(
            f"  {strategy:<18}"
            f"  {np.median(steps):>7.0f}"
            f"  {np.mean(steps):>7.0f}"
            f"  {np.std(steps):>7.1f}"
            f"  {rate:>7.0f}%"
        )

    print("═" * 55)
    best = min(STRATEGIES, key=lambda s: np.median(results[s]["steps"]))
    print(f"\nMeilleure stratégie (médiane) : {best}")


if __name__ == "__main__":
    print("=" * 55)
    print("  COMPARAISON DES STRATÉGIES")
    print(
        f"  {len(STRATEGIES)} stratégies × {N_RUNS} runs  |  max {MAX_STEPS} steps/run")
    print("=" * 55)

    results = collect_results()
    print_summary(results)
    plot_results(results)
