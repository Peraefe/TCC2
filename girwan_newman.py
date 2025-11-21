import networkx as nx
import osmnx as ox
import plotly.graph_objects as go
from shapely.geometry import Polygon
import os
import pickle
from networkx.algorithms.community import girvan_newman



CACHE_DIR = "dados_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

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


def save_pickle(obj, filename):
    with open(filename, "wb") as f:
        pickle.dump(obj, f)

def load_pickle(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)

#Carregar / gerar grafo
def iniciarGrafo():
    graph_path = os.path.join(CACHE_DIR, "grafo.graphml")

    if os.path.exists(graph_path):
        print("Carregando grafo do cache...")
        G = ox.load_graphml(graph_path)
    else:
        print("Gerando grafo a partir do polígono...")
        G = ox.graph_from_polygon(poly, custom_filter=custom_filter, network_type='drive')
        ox.save_graphml(G, graph_path)
        print("Grafo salvo em cache.")

    return G 

G = iniciarGrafo()


gn_cache = os.path.join(CACHE_DIR, "girvan_newman_partition.pkl")

if os.path.exists(gn_cache):
    print("Carregando clusters Girvan-Newman do cache...")
    partition = load_pickle(gn_cache)
else:
    print("Aplicando o algoritmo de Girvan-Newman...")
    comp = girvan_newman(G)
    limited = next(comp) 

    partition = {}
    for i, community in enumerate(limited):
        for node in community:
            partition[node] = i

    save_pickle(partition, gn_cache)
    print("Resultado Girvan-Newman salvo.")


print("Projetando grafo para UTM e rotacionando 90°...")
G_proj = ox.project_graph(G)
G_proj = nx.Graph(G_proj) 

pos = {}
for n in G_proj.nodes():
    x = G_proj.nodes[n]["x"]
    y = G_proj.nodes[n]["y"]
    pos[n] = (y, -x)  


node_x, node_y, node_color = [], [], []
for node in G_proj.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_color.append(partition.get(node, -1)) 


node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    marker=dict(
        size=4,
        color=node_color,
        colorscale='Viridis',
        line=dict(width=1)
    ),
    hoverinfo='text'
)


edge_x, edge_y = [], []
for u, v in G_proj.edges():
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=2, color='DarkSlateGrey'),
    hoverinfo='none',
    mode='lines'
)


fig = go.Figure(data=[edge_trace, node_trace])
fig.update_layout(
    title='Grafo com clusters Girvan-Newman',
    showlegend=False,
    hovermode='closest',
    margin=dict(b=20, l=5, r=5, t=40),
    xaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False)
)
fig.update_yaxes(scaleanchor="x", scaleratio=1)  

fig.show()
