#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass, field
import re
import math

@dataclass
class Node:
    module_name: str
    instance_name: str | None
    parameters: dict[str, int]
    children: list["HierarchyNode"] = field(default_factory=list)

class Design:
    def __init__(self):
        self.modules = {}

    def add_module(self, module):
        self.modules[module.name] = module


class HierarchyBuilder:

    def __init__(self, design):
        self.design = design

    def build(self, top_name: str) -> Node:

        print("Available modules:")
        for name in self.design.modules:
            print(" -", name)
        top_module = self.design.modules[top_name]
        return self._elaborate(
            module=top_module,
            instance_name=None,
            parent_params={}
        )

    def _elaborate(
        self,
        module,
        instance_name: str | None,
        parent_params: dict[str, int],
    ) -> Node:

        # 🔹 1. Résoudre paramètres locaux
        local_params = parent_params.copy()

        for param in module.parameters:

            if param.value_int is not None:
                local_params[param.name] = int(param.value_int)

            elif param.value_str is not None:
                local_params[param.name] = eval_expr(
                    param.value_str,
                    local_params
                )

        node = Node(
            module_name=module.name,
            instance_name=instance_name,
            parameters=dict(local_params),
        )

        # 🔹 2. Elaborer les instances enfants
        for inst in module.instances:

            child_module = self.design.modules[inst.module_name]

            # 1️⃣ contexte = paramètres parent
            child_params = dict(local_params)

            # 2️⃣ résoudre paramètres par défaut du module enfant
            for param in child_module.parameters:

                if param.value_int is not None:
                    child_params[param.name] = int(param.value_int)

                elif param.value_str is not None:
                    child_params[param.name] = eval_expr(
                        param.value_str,
                        child_params
                    )

            # 3️⃣ appliquer overrides après
            for name, expr in inst.parameters.items():
                child_params[name] = eval_expr(expr, child_params)

            # 4️⃣ élaborer récursivement
            child_node = self._elaborate(
                module=child_module,
                instance_name=inst.name,
                parent_params=child_params,
            )

            node.children.append(child_node)


        return node


def eval_expr(expr: str, context: dict[str, int]) -> int:

    # -------------------------------------------------
    # 1️⃣ Convertir nombres Verilog
    # -------------------------------------------------

    def convert_verilog_number(match):
        width = match.group(1)
        base = match.group(2).lower()
        value = match.group(3).replace("_", "")

        if base == "h":
            return str(int(value, 16))
        elif base == "d":
            return str(int(value, 10))
        elif base == "b":
            return str(int(value, 2))
        elif base == "o":
            return str(int(value, 8))
        else:
            return value

    expr = re.sub(
        r"(\d+)?'([hdboxHDBOX])([0-9a-fA-F_]+)",
        convert_verilog_number,
        expr,
    )

    # -------------------------------------------------
    # 2️⃣ Support $clog2
    # -------------------------------------------------

    def convert_clog2(match):
        inner_expr = match.group(1)
        value = eval_expr(inner_expr, context)

        if value <= 0:
            raise ValueError(f"$clog2 invalid value: {value}")

        return str(math.ceil(math.log2(value)))

    expr = re.sub(
        r"\$clog2\s*\((.*?)\)",
        convert_clog2,
        expr,
    )

    print(context)
    print(expr)
    # -------------------------------------------------
    # 3️⃣ Eval final
    # -------------------------------------------------

    return eval(expr, {}, context)
