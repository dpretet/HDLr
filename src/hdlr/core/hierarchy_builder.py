#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

class HierNode:
    def __init__(self, module_def, instance_name, param_values):
        self.module_def = module_def
        self.instance_name = instance_name
        self.param_values = param_values
        self.children = []

class HierarchyBuilder:
    def __init__(self, design):
        self.design = design

    def build(self, top_name):
        top_module = self.design.get(top_name)
        return self._expand(top_module, top_name, {})

    def _expand(self, module_def, inst_name, parent_params):
        node = HierNode(module_def, inst_name, parent_params)

        for inst in module_def.instances:
            child_def = self.design.get(inst.module_name)

            merged_params = self._resolve_params(
                child_def,
                inst.parameters,
                parent_params
            )

            child_node = self._expand(
                child_def,
                inst.name,
                merged_params
            )

            node.children.append(child_node)

        return node
