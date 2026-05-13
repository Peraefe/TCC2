import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os
import numpy as np
from matplotlib.ticker import FuncFormatter


CACHE_DIR = "dados_cache"
results_path = os.path.join(CACHE_DIR, "resultados.pkl")

if not os.path.exists(results_path):
    raise FileNotFoundError(f"Arquivo {results_path} não encontrado!")

# Carregar resultados
print("Carregando resultados...")
with open(results_path, "rb") as f:
    data = pickle.load(f)

ks = sorted(data["simulations"].keys())

deterministic_labels = ["Degree", "Closeness", "Betweenness"]
random_label = ["Random10", "Random20", "Random100"]


# =========================================================
# EXTRAÇÃO DOS DADOS
# =========================================================

def extract_boxplot_data(metric):
    rows = []

    for k in ks:

        # determinísticos
        for label in deterministic_labels:
            rows.append({
                "strategy": label,
                "value": data["simulations"][k][label.lower()][metric]
            })

        # random10
        for res in data["simulations"][k]["random_10"]:
            rows.append({
                "strategy": "Random10",
                "value": res[metric]
            })

        # random20
        for res in data["simulations"][k]["random_20"]:
            rows.append({
                "strategy": "Random20",
                "value": res[metric]
            })

        # random100
        for res in data["simulations"][k]["random_100"]:
            rows.append({
                "strategy": "Random100",
                "value": res[metric]
            })

    return pd.DataFrame(rows)


df_components = extract_boxplot_data("n_components")
df_disconnected = extract_boxplot_data("disconnected_pairs")
df_largest_cc = extract_boxplot_data("largest_cc_size")


# =========================================================
# FUNÇÃO CUSTOMIZADA
# =========================================================

def custom_boxplot(ax, df, title, ylabel):

    names = df["strategy"].unique()

    vals = [
        df[df["strategy"] == name]["value"].values
        for name in names
    ]

    # cores
    palette = ['red', 'green', 'blue', 'orange', 'purple', 'brown']

    # boxplot
    box = ax.boxplot(
        vals,
        labels=names,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(
            linewidth=1.5,
            linestyle='-',
            color='#01FBEE'
        )

    )

    # colorir caixas
    for patch, color in zip(box['boxes'], palette):
        patch.set_facecolor(color)
        patch.set_alpha(0.3)

    # scatter
    xs = np.arange(1, len(vals) + 1)

    for x, val, c in zip(xs, vals, palette):

        jitter = np.random.normal(
            loc=x,
            scale=0.04,
            size=len(val)
        )

        ax.scatter(
            jitter,
            val,
            alpha=0.4,
            color=c,
            s=20
        )

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.grid(True)


# =========================================================
# PLOTS
# =========================================================

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

fig.suptitle(
    "Resilience Metrics Distribution Under Different Removal Strategies",
    fontsize=14
)

# 1
custom_boxplot(
    axes[0,0],
    df_components,
    "Strongly Connected Components (SCCs)",
    "Number of SCCs"
)

# 2
custom_boxplot(
    axes[0,1],
    df_disconnected,
    "Disconnected Pairs",
    "Number of Disconnected Pairs"
)

axes[0,1].yaxis.set_major_formatter(
    FuncFormatter(lambda x, _: f'{int(x):,}')
)

# 3
custom_boxplot(
    axes[1,0],
    df_largest_cc,
    "Size of Largest Strongly Connected Component (LSCC)",
    "Number of vertices in the LSCC"
)

# remover subplot vazio
axes[1,1].axis("off")

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()