# TCC2
Simulação de Ataques e Avaliação de Resiliência em Grafos da Infraestrutura Viária de Palmas-TO


Este repositório contém um conjunto de scripts para **baixar, processar, analisar e visualizar a malha viária da cidade de Palmas (TO)** através de técnicas de:

* Teoria dos grafos
* Análise estrutural
* Centralidades (degree, closeness, betweenness)
* Remoção de nós (direcionada e aleatória)
* Detecção de comunidades (Louvain e Girvan–Newman)
* Identificação de *strong bridges*
* Visualizações interativas com Plotly
* Estatísticas com Matplotlib e Pandas

Todos os dados são armazenados em cache para evitar downloads ou recomputações desnecessárias.

---

## 📁 Estrutura Geral

```
📦 repositorio
 ┣ 📂 dados_cache/          # Armazena todos os arquivos gerados
 ┃ ┣ grafo.graphml          # Grafo viário baixado do OSM
 ┃ ┣ grafo_igraph.pkl       # Representação iGraph
 ┃ ┣ centralities.pkl       # Centralidades calculadas
 ┃ ┣ resultados.pkl         # Resultados das simulações de robustez
 ┃ ┣ louvain_partition.pkl  # Clusters Louvain
 ┃ ┣ girvan_newman_partition.pkl
 ┃ ┗ outros caches...
 ┣ 🧠 centralidades_ataques.py            # Simulações de remoção de nós e métricas
 ┣ 🧭 louvain.py # Clusters Louvain + visualização
 ┣ 🧭 girwan_newman.py       # Clusters Girvan–Newman + visualização
 ┣ 🔥 conexo.py      # Identificação de arestas críticas
 ┣ 📊 boxplot.py    # Boxplots de métricas resultantes
 ┗ README.md
```

---

## 🛠️ Dependências

Instale com:

```bash
pip install osmnx igraph networkx plotly community tqdm shapely matplotlib pandas
```

---

## 🌐 Download e Cache da Malha Viária

Os scripts utilizam OSMnx para baixar vias de veículos dentro de um **polígono pré-definido de Palmas-TO**.
O download é feito **apenas na primeira execução**, sendo depois carregado de `dados_cache/grafo.graphml`.

```python
G = ox.graph_from_polygon(poly, custom_filter=custom_filter, network_type="drive")
```

O filtro exclui ciclovias, caminhos de pedestres e áreas.

---

## 📊 1. Análise de Fragilidade — *centralidades_ataque.py*

Arquivo principal que:

1. Carrega ou baixa a malha viária
2. Converte NetworkX → iGraph
3. Calcula degree/closeness/betweenness
4. Executa simulações removendo:

   * nós de maior centralidade
   * nós aleatórios (10, 20, 100 execuções)
5. Mede:

   * número de componentes fortemente conexas
   * tamanho da maior componente fortemente conexa
   * pares desconectados
6. Gera gráficos com matplotlib
7. Salva resultados em cache


## 🧭 2. Detecção de Comunidades — Louvain

Arquivo: **louvain.py**

* Usa `python-louvain`
* Projeta o grafo para coordenadas UTM
* Rotaciona para melhor visualização
* Gera desenho interativo com Plotly
* Cores aleatórias por cluster


## 🧭 3. Detecção de Comunidades — Girvan–Newman

Arquivo: **girwan_newman.py**

* Implementa Girvan–Newman
* Guarda 
* Exibe via Plotly com coloração por cluster

---

## 🔥 4. Arestas Críticas — *conexo*

Arquivo: **conexo.py**

Identifica arestas cuja remoção **desconecta componentes fortemente conexas** usando:

* Dominadores de arestas
* Grafo reverso
* União de dominadores e dominadores reversos
* Exclusão de rotatórias (*roundabouts*)

Gera visualização Plotly destacando:

* 🟥 arestas críticas
* 🟦 nós
* 🌫️ arestas normais

---

## 📊 5. Boxplots das Métricas de Fragilidade

Arquivo: **boxplot.py**

Gera boxplots 
Métricas plotadas:

* Número de componentes
* Pares desconectados
* Tamanho do maior CC

---


