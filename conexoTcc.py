import os
import igraph as ig
import plotly.graph_objects as go
from shapely.geometry import Polygon
import osmnx as ox
import networkx as nx

CACHE_DIR = "dados_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# -------------------
# Polígono de Palmas
# -------------------
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

# -------------------
# Carregar ou baixar grafo
# -------------------
def iniciarGrafo():
    path = os.path.join(CACHE_DIR, "grafo.graphml")
    if os.path.exists(path):
        print("Carregando grafo do cache...")
        G = ox.load_graphml(path)
    else:
        print("Baixando grafo do OSM...")
        G = ox.graph_from_polygon(poly, custom_filter=custom_filter, network_type="drive")
        ox.save_graphml(G, path)
        print("Grafo salvo no cache.")
    return G

G_nx = iniciarGrafo()

def edge_dominators(G, s):
    """
    Retorna o conjunto DE(s):
    Todas as arestas (u, v) tais que u = idom[v]
    """
    idom = nx.immediate_dominators(G, s)
    EDom = set()

    for u, v in G.edges():
        if v in idom and idom[v] == u:
            EDom.add((u, v))

    return EDom


def StrongBridges(G):

    # 1. Escolhe vértice arbitrário s
    s = next(iter(G.nodes))

    # 2. Dominadores de arestas no grafo original
    DE = edge_dominators(G, s)

    # 3. Grafo reverso
    GR = G.reverse(copy=True)

    # 4. Dominadores no grafo reverso
    DER = edge_dominators(GR, s)

    # 5. Reverter arestas de DER
    DER_reversed = {(v, u) for (u, v) in DER}

    # União
    return DE.union(DER_reversed)


"""Trecho necessário por conta de 1 estacionamento de mão única que separa o grafo em 2 componentes fortemente conexas"""
sccs = list(nx.strongly_connected_components(G_nx))
if not sccs:
    raise ValueError("O grafo não possui componentes fortemente conexos.")
largest_scc_nodes = max(sccs, key=len)
H = G_nx.subgraph(largest_scc_nodes).copy()


strong_bridges = StrongBridges(H)

#Excluindo rotatórias
roundabout_edges = set()

for u, v, k, data in G_nx.edges(keys=True, data=True):
    if data.get("junction") == "roundabout":
        roundabout_edges.add((u, v))

filtered_strong_bridges = []
for (u, v) in strong_bridges:

    if (u, v) in roundabout_edges:
        continue
    filtered_strong_bridges.append((u, v))

strong_bridges = filtered_strong_bridges



# Converter NetworkX p igraph
nx_nodes = list(G_nx.nodes())
node_id_map = {node: idx for idx, node in enumerate(nx_nodes)}
edges_ig = [(node_id_map[u], node_id_map[v]) for u, v in G_nx.edges()]
G = ig.Graph(edges_ig, directed=True)


# Mapear strong_bridges para índices de arestas do igraph
critical_edges = []
for (u, v) in strong_bridges:
    
    if u not in node_id_map or v not in node_id_map:
        continue
    ui, vi = node_id_map[u], node_id_map[v]
    try:
        eid = G.get_eid(ui, vi)
        critical_edges.append(eid)
    except ig._igraph.InternalError:
        # aresta não existe no grafo global, ignora
        continue

critical_edges = list(set(critical_edges))

# Posições para plot
pos = {node_id_map[n]: (G_nx.nodes[n]["y"], -G_nx.nodes[n]["x"]) for n in G_nx.nodes()}


# Mapear de volta para índices do igraph
edge_map = {(e.source, e.target): e.index for e in G.es}



# Plot
fig = go.Figure()

# --- Arestas normais ---
edge_x, edge_y = [], []
for e in G.es:
    if e.index in critical_edges:
        continue
    u, v = e.tuple
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

fig.add_trace(go.Scatter(
    x=edge_x, y=edge_y,
    mode='lines',
    line=dict(width=1, color='gray'),
    hoverinfo='none'
))

# --- Arestas críticas ---
edge_x, edge_y = [], []
for e in G.es:
    if e.index not in critical_edges:
        continue
    u, v = e.tuple
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]

fig.add_trace(go.Scatter(
    x=edge_x, y=edge_y,
    mode='lines',
    line=dict(width=2, color='red'),
    hoverinfo='none',
    name='Arestas críticas'
))

# --- Todos os vértices mesma cor ---
node_x = [pos[i][0] for i in range(len(nx_nodes))]
node_y = [pos[i][1] for i in range(len(nx_nodes))]

fig.add_trace(go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    marker=dict(size=4, color='lightblue'),
    name="Nós"
))

fig.update_layout(
    title="Arestas Críticas (Strong Bridges)",
    showlegend=True,
    margin=dict(l=0, r=0, t=40, b=0),
    hovermode="closest",
    xaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False)
)
fig.update_yaxes(scaleanchor="x", scaleratio=1)
fig.show()