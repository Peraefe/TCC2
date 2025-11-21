import os
import pickle
import random
import igraph as ig
from tqdm import tqdm
import osmnx as ox
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

CACHE_DIR = "dados_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def save_pickle(obj, filename):
    with open(filename, "wb") as f:
        pickle.dump(obj, f)

def load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)
    

# Polígono de Palmas

coords = [
    (-48.36696955241467, -10.16042180576919),
    (-48.37886688384131, -10.336359895479362),
    (-48.35982289686413, -10.35628534841031),
    (-48.342471323758105, -10.357751575597831),
    (-48.33666333289699, -10.370889148819813),
    (-48.30672563561052, -10.378178731196513),
    (-48.25570954866717, -10.34419542890619),
    (-48.249420868902234, -10.321439608338196),
    (-48.29231253625048, -10.28068681395601),
    (-48.30943053325848, -10.24007484517854),
    (-48.30981880008265, -10.229993635704872),
    (-48.303957402338625, -10.220574128399832),
    (-48.29577028867692, -10.159450203497599),
    (-48.317091634855245, -10.132453181528646),
    (-48.36696955241467, -10.16042180576919)
]
poly = Polygon(coords)

custom_filter = (
    '["highway"!~"footway|path|cycleway|pedestrian|steps"]'
    '["area"!~"yes"]["highway"]'
)



# Converter NetworkX p iGraph

def nx_to_igraph(G_nx, directed=True):
    mapping = {node: idx for idx, node in enumerate(G_nx.nodes())}
    G_ig = ig.Graph(directed=directed)
    G_ig.add_vertices(len(mapping))

    for node, idx in mapping.items():
        n = G_nx.nodes[node]
        G_ig.vs[idx]["id"] = node
        G_ig.vs[idx]["x"] = n.get("x", None)
        G_ig.vs[idx]["y"] = n.get("y", None)

    edges = []
    weights = []
    for u, v, data in G_nx.edges(data=True):
        edges.append((mapping[u], mapping[v]))
        weights.append(data.get("length", 1.0))
    G_ig.add_edges(edges)
    G_ig.es["weight"] = weights

    return G_ig, mapping


# Centralidades

def compute_centralities_igraph(G):
    degree = G.degree()
    closeness = G.closeness(mode="ALL")
    betweenness = G.betweenness()
    return {
        "degree": {v.index: degree[v.index] for v in G.vs},
        "closeness": {v.index: closeness[v.index] for v in G.vs},
        "betweenness": {v.index: betweenness[v.index] for v in G.vs},
    }

def sort_ranking(centrality_dict):
    return sorted(centrality_dict.keys(), key=lambda k: centrality_dict[k], reverse=True)


# Remoção de nós

def remove_nodes_by_centrality_fixed_ranking(G_original, k, ranking):
    G = G_original.copy()
    if k > 0:
        G.delete_vertices(ranking[:k])
    return G

def remove_nodes_random(G_original, k):
    G = G_original.copy()
    if k > 0:
        G.delete_vertices(random.sample(range(G.vcount()), k))
    return G


# Métricas de conectividade

def compute_connectivity_metrics(G):
    if G.vcount() == 0:
        return {"n_components": 0, "largest_cc_size": 0, "disconnected_pairs": 0}

    comps = G.connected_components(mode="STRONG")
    if len(comps) == 0:
        return {"n_components": 0, "largest_cc_size": 0, "disconnected_pairs": 0}

    num_components = len(comps)
    largest_cc = max(comps, key=len)
    largest_cc_size = len(largest_cc)

    n = G.vcount()
    disconnected_pairs = sum(len(c) * (n - len(c)) for c in comps) // 2

    return {
        "n_components": num_components,
        "largest_cc_size": largest_cc_size,
        "disconnected_pairs": disconnected_pairs
    }


#Processamento do Grafo

def process_graph(graphml_path):

    if os.path.exists(graphml_path):
        print("Carregando grafo do cache...")
        G_nx = ox.load_graphml(graphml_path)
    else:
        print("Baixando grafo do OSM...")
        G_nx = ox.graph_from_polygon(poly, custom_filter=custom_filter, network_type="drive")
        ox.save_graphml(G_nx, graphml_path)
        print("Grafo salvo no cache.")

    #Checar cache do igraph
    igraph_cache = os.path.join(CACHE_DIR, "grafo_igraph.pkl")
    if os.path.exists(igraph_cache):
        print("Carregando grafo iGraph do cache...")
        G_ig, mapping = load_pickle(igraph_cache)
    else:
        print("Convertendo para iGraph...")
        G_ig, mapping = nx_to_igraph(G_nx)
        save_pickle((G_ig, mapping), igraph_cache)
        print("Grafo iGraph salvo em cache.")

    #Checar cache das centralidades 
    centralities_cache = os.path.join(CACHE_DIR, "centralities.pkl")
    if os.path.exists(centralities_cache):
        print("🔹 Carregando centralidades do cache...")
        centralities = load_pickle(centralities_cache)
    else:
        print("Calculando centralidades...")
        centralities = compute_centralities_igraph(G_ig)
        save_pickle(centralities, centralities_cache)
        print("Centralidades salvas em cache.")

    deg_rank = sort_ranking(centralities["degree"])
    clo_rank = sort_ranking(centralities["closeness"])
    bet_rank = sort_ranking(centralities["betweenness"])

    #Checar cache de resultados 
    results_cache = os.path.join(CACHE_DIR, "resultados.pkl")
    if os.path.exists(results_cache):
        print("🔹 Carregando resultados do cache...")
        return load_pickle(results_cache)

    # Simulações 
    print("🔹 Executando simulações...")
    resultados = {
        "centralities": centralities,
        "degree_rank": deg_rank,
        "closeness_rank": clo_rank,
        "betweenness_rank": bet_rank,
        "simulations": {}
    }

    N = G_ig.vcount()
    ks = [int(N * p / 100) for p in range(1, 101)]
    random_runs_list = [10, 20, 100]

    for k in tqdm(ks, desc="Simulações", unit="k removidos"):
        res = {}
        # por centralidade
        res["degree"] = compute_connectivity_metrics(remove_nodes_by_centrality_fixed_ranking(G_ig, k, deg_rank))
        res["closeness"] = compute_connectivity_metrics(remove_nodes_by_centrality_fixed_ranking(G_ig, k, clo_rank))
        res["betweenness"] = compute_connectivity_metrics(remove_nodes_by_centrality_fixed_ranking(G_ig, k, bet_rank))

        # aleatórios
        for r in random_runs_list:
            metrics_list = []
            for _ in range(r):
                metrics_list.append(compute_connectivity_metrics(remove_nodes_random(G_ig, k)))
            res[f"random_{r}"] = metrics_list

        resultados["simulations"][k] = res

    save_pickle(resultados, results_cache)
    print("✅ Resultados salvos em cache.")
    return resultados


#Executa

if __name__ == "__main__":
    graph_file = "dados_cache/grafo.graphml"
    resultados = process_graph(graph_file)

    ks = sorted(resultados["simulations"].keys())

    def get_metric_series(metric):
        series = {}
        for label in ["degree", "closeness", "betweenness"]:
            series[label] = [resultados["simulations"][k][label][metric] for k in ks]
        for r in [10, 20, 50]:
            series[f"random_{r}"] = [sum(res[metric] for res in resultados["simulations"][k][f"random_{r}"]) / r for k in ks]
        return series

    disconnected_pairs = get_metric_series("disconnected_pairs")
    n_components = get_metric_series("n_components")
    largest_cc = get_metric_series("largest_cc_size")


    def plot_metric(series, title, ylabel):

        linestyles = ['-', '--', ':', '-.', '--', '--']
        markers = [None, None, None, None, 'o', '^']
        markersizes = [None, None, None, None, 3, 3]

        # Eixo normal
        plt.figure()
        for i, (label, values) in enumerate(series.items()):
            ls = linestyles[i % len(linestyles)]
            m = markers[i % len(markers)]
            ms = markersizes[i % len(markersizes)]
            plt.plot([k/len(ks)*100 for k in ks], values, label=label,
                    linestyle=ls, marker=m, markersize=ms if ms else None)
        plt.xlabel("Percentage of nodes removed")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(False)
        plt.legend()

        plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x):,}'))
        plt.show()

        # Eixo logarítmico
        plt.figure()
        for i, (label, values) in enumerate(series.items()):
            ls = linestyles[i % len(linestyles)]
            m = markers[i % len(markers)]
            ms = markersizes[i % len(markersizes)]
            plt.plot([k/len(ks)*100 for k in ks], values, label=label,
                    linestyle=ls, marker=m, markersize=ms if ms else None)
        plt.xlabel("Percentage of nodes removed")
        plt.ylabel(ylabel)
        plt.title(title + " (Logarithmic Scale)")
        plt.yscale("log")
        plt.grid(False)
        plt.legend()
        plt.show()



    plot_metric(disconnected_pairs, "Disconnected Pairs vs Node Removal", "Disconnected Pairs")
    plot_metric(n_components, "Number of Components vs Node Removal", "Number of Components")
    plot_metric(largest_cc, "Largest Connected Component vs Node Removal", "Largest CC Size")
