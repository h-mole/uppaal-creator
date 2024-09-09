import logging
from pyuppaal import UModel
from typing import Set
from textwrap import dedent
import networkx as nx
import pyuppaal
from pyuppaal.nta import Template, Location, Edge
import os
from .common import NodeType, FileManager
from .layout_computation import calc_layout


class UPPAALCreator:

    def __init__(
        self, output_dir: str, model_name: str, overwrite_model_file=False
    ) -> None:
        super().__init__()
        """
        :output_dir: The output directory of UPPAAL model
        :model_name: The name of UPPAAL model
        """
        self.file_manager = FileManager(output_dir)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_name = model_name
        self.umodel: UModel = self.create_model(overwrite_model_file)
        self.used_custom_types: Set[str] = set()

    def create_model(self, overwrite_model_file=False):
        """
        Create UPPAAL model from the control flow graph.
        """
        model_path = self.file_manager.get_abspath(self.model_name + ".xml")

        self.logger.info(f"Start creating the uppaal model at {model_path}")
        if overwrite_model_file and os.path.exists(model_path):
            os.remove(model_path)
            self.logger.info("Successfully removed the old model")

        self.umodel = pyuppaal.UModel.new(model_path)
        self.logger.info("Successfully created the new model")
        self.umodel.templates = []

        self.umodel.declaration = ""

        return self.umodel

    def finish_model_creation(
        self,
    ):
        model_creation_exprs = []
        object_names = []
        for template in self.umodel.templates:
            object_name = f"{template.name}_obj"
            object_names.append(object_name)
            model_creation_exprs.append(f"{object_name} = {template.name}();")
        model_creation_exprs.append(f"system {','.join(object_names)};")
        self.umodel.system = dedent("\n".join(model_creation_exprs))

    def rel_pos(self, orig_pos: tuple[int, int], diff: tuple[int, int]):
        return (orig_pos[0] + diff[0], orig_pos[1] + diff[1])

    def convert_graph(
        self,
        G: nx.DiGraph,
        template_name: str,
        init_node: NodeType,
        node_names: dict[NodeType, str],
        guards: dict[tuple[NodeType, NodeType], str],
        updates: dict[tuple[NodeType, NodeType], str],
    ):
        """ """
        func_template = Template(
            name=template_name,
            locations=[],
            init_ref=0,
            edges=[],
            declaration="\n".join([]),
        )
        # 创建一个新的空的有向图
        H = nx.DiGraph()

        # 将原始图中的所有节点添加到新图中
        H.add_nodes_from(G.nodes())

        # 将原始图中的所有边添加到新图中
        H.add_edges_from(G.edges())

        layout, nails = calc_layout(G)

        def get_position_middle(
            pos1: tuple[int, int], pos2: tuple[int, int]
        ) -> tuple[int, int]:
            return (
                int((pos1[0] + pos2[0]) / 2),
                int((pos1[1] + pos2[1]) / 2),
            )

        def get_middle_two(lst: list[tuple[int, int]]):
            """
            从列表中取出最靠近中间的两个数。

            参数:
            lst (list) - 输入的列表,长度大于等于2。

            返回:
            两个最靠近中间的数组成的元组。
            """
            if len(lst) < 2:
                raise ValueError("列表长度必须大于等于2")

            mid = len(lst) // 2
            if len(lst) % 2 == 0:
                return (lst[mid - 1], lst[mid])
            else:
                return (lst[mid - 1], lst[mid])

        def get_edge_midpoint(u: NodeType, v: NodeType) -> tuple[int, int]:
            if (u, v) not in nails:
                # 获取边的中点
                return (
                    int((layout[u][0] + layout[v][0]) / 2),
                    int((layout[u][1] + layout[v][1]) / 2),
                )
            else:
                if len(nails[(u, v)]) == 1:
                    return nails[(u, v)][0]
                else:
                    first_nail, second_nail = get_middle_two(nails[(u, v)])
                    # print(first_nail, second_nail)
                    return get_position_middle(
                        first_nail, second_nail
                    )

        for node_id in G.nodes:
            if node_id == init_node:
                loc = Location(
                    location_id=node_id,
                    location_pos=layout[node_id],
                    name=node_names.get(node_id, f"Node{node_id}"),
                    name_pos=self.rel_pos(layout[node_id], (-10, -20)),
                )
                func_template.init_ref = node_id
            else:
                loc = Location(
                    location_id=node_id,
                    location_pos=layout[node_id],
                    name=node_names.get(node_id, f"Node{node_id}"),
                    name_pos=self.rel_pos(layout[node_id], (-10, -20)),
                )
            func_template.locations.append(loc)

        for u, v in G.edges:
            update = updates.get((u, v), "")
            guard = guards.get((u, v), "")
            e = Edge(
                source_location_id=u,
                source_location_pos=layout[u],
                target_location_id=v,
                target_location_pos=layout[v],
                guard=guard,
                guard_pos=self.rel_pos(get_edge_midpoint(u, v), (10, 20)),
                update=update,
                update_pos=self.rel_pos(get_edge_midpoint(u, v), (10, -20)),
                nails=nails.get((u, v), []),
            )
            func_template.edges.append(e)
        self.umodel.templates = self.umodel.templates + [func_template]
