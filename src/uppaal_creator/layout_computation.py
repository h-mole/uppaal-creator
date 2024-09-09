"""
利用PyDot，计算UPPAAL的布局
"""

import random
import networkx as nx


def generate_new_node_id(G):
    """
    为给定的NetworkX图G生成新节点的ID。
    新节点ID为一个随机生成的整数,且不与现有节点ID重复。

    参数:
    G (networkx.Graph或networkx.DiGraph): 输入的NetworkX图。

    返回:
    int: 新节点的ID。
    """
    existing_ids = set(G.nodes)
    new_id = random.randint(100, 100000)

    # 确保新ID不与现有ID重复
    while new_id in existing_ids:
        new_id = random.randint(100, 100000)

    return new_id


def insert_nodes(G1: nx.DiGraph):
    new_edges = []
    nail_ids: dict[tuple[int, int], list[int]] = {}
    graph_for_layout = nx.DiGraph(G1)
    for u, v in list(graph_for_layout.edges):
        if u == v or (v, u) in G1.edges:
            # 如果起始和终止节点是同一节点，插入两个新节点
            node_id1 = generate_new_node_id(graph_for_layout)
            node_id2 = generate_new_node_id(graph_for_layout)
            graph_for_layout.add_node(node_id1, type="nail")
            graph_for_layout.add_node(node_id2, type="nail")
            new_edges.append((u, node_id1))
            new_edges.append((node_id1, node_id2))
            new_edges.append((node_id2, v))
            # 记住钉子所属的边
            nail_ids[(u, v)] = [node_id1, node_id2]

    # 在原有图上添加新边
    graph_for_layout.add_edges_from(new_edges)
    # cycles = list(nx.simple_cycles(graph_for_layout))
    # for cycle in cycles:
    #     G.remove_edge(cycle[0], cycle[1])
    # DAG = nx.DiGraph(list(nx.topological_sort(graph_for_layout)))
    return graph_for_layout, nail_ids


def calc_layout(graph: nx.DiGraph):
    graph_for_layout, nail_ids = insert_nodes(graph)
    zoom_ratio = 3.0
    pydot_layout = nx.nx_pydot.pydot_layout(graph_for_layout, "neato")
    layout = {
        node: (
            int(pydot_layout[node][0] * zoom_ratio),
            int(pydot_layout[node][1] * zoom_ratio),
        )
        for node in graph.nodes()
    }
    nail_positions = {
        edge: [
            (
                int(pydot_layout[nail_id][0] * zoom_ratio),
                int(pydot_layout[nail_id][1] * zoom_ratio),
            )
            for nail_id in nail_ids
        ]
        for edge, nail_ids in nail_ids.items()
    }
    return layout, nail_positions
