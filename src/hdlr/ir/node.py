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

        # Store only the parameters that are specific to this module
        # (not inherited from parent contexts)
        module_specific_params = {}
        for param in module.parameters:
            if param.name in local_params:
                module_specific_params[param.name] = local_params[param.name]
        
        node = Node(
            module_name=module.name,
            instance_name=instance_name,
            parameters=dict(module_specific_params),
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

    # -------------------------------------------------
    # 2.5️⃣ Support Verilog ternary operator
    # -------------------------------------------------

    def convert_ternary(match):
        condition = match.group(1).strip()
        true_expr = match.group(2).strip()
        false_expr = match.group(3).strip()

        # Evaluate condition first
        cond_value = eval_expr(condition, context)

        # Return the appropriate branch
        if cond_value:
            return str(eval_expr(true_expr, context))
        else:
            return str(eval_expr(false_expr, context))

    # Handle ternary operators - need to be careful with nested expressions
    # Use a more robust pattern that handles the full ternary expression
    # Handle nested ternary operators by processing from innermost to outermost

    # First, handle innermost ternary operators (not preceded by other ternaries)
    # This pattern matches ternary operators that are not nested within other ternaries
    def convert_ternary_inner(match):
        condition = match.group(1).strip()
        true_expr = match.group(2).strip()
        false_expr = match.group(3).strip()

        # Evaluate condition first
        cond_value = eval_expr(condition, context)

        # Return the appropriate branch
        if cond_value:
            return str(eval_expr(true_expr, context))
        else:
            return str(eval_expr(false_expr, context))

    # Pattern to match ternary operators, handling nested ones by processing multiple times
    # This matches: (condition) ? true_expr : false_expr
    # We need to be careful with nested ternaries, so we process multiple times
    # Use a non-greedy match for the true_expr to avoid capturing nested ternaries
    pattern = r"\(([^?]*)\)\s*\?\s*([^:]*?):\s*([^:]+?)(?=\W|$)"

    # Apply the substitution multiple times to handle nested ternaries
    max_iterations = 10  # Prevent infinite loops
    for _ in range(max_iterations):
        new_expr = re.sub(pattern, convert_ternary_inner, expr)
        if new_expr == expr:  # No more changes
            break
        expr = new_expr

    # -------------------------------------------------
    # 3️⃣ Eval final
    # -------------------------------------------------

    # Strip whitespace and remove any remaining comments
    expr = expr.strip()

    # If the expression still contains a colon, it means the ternary operator
    # was not properly processed. This can happen with complex nested expressions.
    # For now, let's try to handle simple cases where we have "X : Y" format
    if ":" in expr and "?" not in expr:
        # This looks like a malformed ternary operator result
        # Try to extract just the number part
        number_match = re.search(r'\d+', expr)
        if number_match:
            expr = number_match.group(0)

    return eval(expr, {}, context)
