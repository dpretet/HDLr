#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Hierarchy and parameter resolution module for HDLr.

This module provides the core functionality for building design hierarchies
and resolving parameter expressions in SystemVerilog/Verilog designs.
"""

import math
import re
from dataclasses import dataclass, field


@dataclass
class Node:
    """Represents a node in the design hierarchy.

    Attributes:
        module_name: Name of the module
        instance_name: Name of the instance (None for top module)
        parameters: Dictionary of resolved parameter values
        children: List of child nodes in the hierarchy
    """
    module_name: str
    instance_name: str | None
    parameters: dict[str, int]
    children: list["Node"] = field(default_factory=list)


@dataclass
class Design:
    """Container for all modules in a design.

    Attributes:
        modules: Dictionary mapping module names to module objects
    """
    modules: dict = field(default_factory=dict)

    def add_module(self, module):
        """Add a module to the design.

        Args:
            module: Module object to add

        Raises:
            ValueError: If a module with the same name already exists
        """
        if module.name in self.modules:
            raise ValueError(f"Duplicate module {module.name}")
        self.modules[module.name] = module

    def get(self, name):
        """Get a module by name.

        Args:
            name: Name of the module to retrieve

        Returns:
            The module object, or None if not found
        """
        return self.modules.get(name)


@dataclass
class HierarchyBuilder:
    """Builds design hierarchies with resolved parameters.

    Attributes:
        design: Design object containing all modules
    """
    design: Design

    def build(self, top_name: str) -> Node:
        """Build hierarchy starting from a top module.

        Args:
            top_name: Name of the top module

        Returns:
            Root node of the hierarchy
        """
        print("Available modules:")
        for name in self.design.modules:
            print(" -", name)
        top_module = self.design.modules[top_name]
        return self._elaborate(
            module=top_module,
            instance_name=None,
            parent_params={}
        )

    def _evaluate_condition(self, condition: str, context: dict[str, int]) -> bool:
        """Evaluate a generate condition in the current parameter context.

        Args:
            condition: The condition string to evaluate
            context: Dictionary of available parameters

        Returns:
            True if condition evaluates to true, False otherwise
        """
        try:
            # Use the existing eval_expr function to evaluate the condition
            result = eval_expr(condition, context)
            return bool(result)
        except Exception:
            # If evaluation fails, assume condition is false
            return False

    def _elaborate(
        self,
        module,
        instance_name: str | None,
        parent_params: dict[str, int],
    ) -> Node:
        """Recursively elaborate a module and its children.

        Args:
            module: Module object to elaborate
            instance_name: Name of this instance (None for top)
            parent_params: Parameters inherited from parent context

        Returns:
            Elaborated node with resolved parameters and children
        """
        # Step 1: Resolve local parameters
        local_params = parent_params.copy()

        for param in module.parameters:
            # Only resolve parameter if it hasn't been overridden by parent instance
            if param.name not in local_params:
                if param.value_int is not None:
                    local_params[param.name] = int(param.value_int)

                elif param.value_str is not None:
                    local_params[param.name] = eval_expr(
                        param.value_str,
                        local_params
                    )

        # Store only module-specific parameters (not inherited ones)
        module_specific_params = {}
        for param in module.parameters:
            if param.name in local_params:
                module_specific_params[param.name] = local_params[param.name]

        node = Node(
            module_name=module.name,
            instance_name=instance_name,
            parameters=dict(module_specific_params),
        )

        # Step 2: Elaborate child instances (filtering conditional ones)
        for inst in module.instances:
            # Skip conditional instances that don't meet their condition
            if inst.condition and not self._evaluate_condition(inst.condition, local_params):
                continue
            child_module = self.design.modules[inst.module_name]

            # 1. Start with parent context
            child_params = dict(local_params)

            # 2. Resolve child module's default parameters
            for param in child_module.parameters:
                if param.value_int is not None:
                    child_params[param.name] = int(param.value_int)

                elif param.value_str is not None:
                    child_params[param.name] = eval_expr(
                        param.value_str,
                        child_params
                    )

            # 3. Apply parameter overrides from instance
            overridden_params = set()
            for name, expr in inst.parameters.items():
                child_params[name] = eval_expr(expr, child_params)
                overridden_params.add(name)

            # 4. Re-evaluate dependent parameters
            # Parameters that depend on overridden parameters need to be re-evaluated
            for param in child_module.parameters:
                if (param.name not in overridden_params and
                    param.value_str is not None and
                    any(override in param.value_str for override in overridden_params)):
                    # This parameter depends on an overridden parameter, re-evaluate it
                    child_params[param.name] = eval_expr(param.value_str, child_params)

            # 5. Recursively elaborate child
            child_node = self._elaborate(
                module=child_module,
                instance_name=inst.name,
                parent_params=child_params,
            )

            node.children.append(child_node)

        return node


def eval_expr(expr: str, context: dict[str, int]) -> int:
    """Evaluate a SystemVerilog parameter expression.

    Supports:
    - Verilog number formats (e.g., 8'hFF, 16'd42)
    - $clog2 function
    - Ternary operators (condition ? true : false)
    - Basic arithmetic expressions

    Args:
        expr: Expression string to evaluate
        context: Dictionary of available variables/parameters

    Returns:
        Evaluated integer result

    Raises:
        ValueError: If expression contains invalid $clog2 argument
    """
    # Step 1: Convert Verilog number formats
    def convert_verilog_number(match):
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

    # Step 2: Support $clog2 function
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

    # Step 2.5: Support Verilog ternary operators
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

    # Handle nested ternary operators by processing multiple times
    pattern = r"\(([^?]*)\)\s*\?\s*([^:]*?):\s*([^:]+?)(?=\W|$)"

    max_iterations = 10  # Prevent infinite loops
    for _ in range(max_iterations):
        new_expr = re.sub(pattern, convert_ternary_inner, expr)
        if new_expr == expr:  # No more changes
            break
        expr = new_expr

    # Step 3: Clean up comments and final evaluation
    expr = expr.strip()

    # Remove C-style comments /* ... */
    expr = re.sub(r'/\*.*?\*/', '', expr)
    # Remove C++ style comments // ...
    expr = re.sub(r'//.*$', '', expr)

    # Clean up multiple spaces
    expr = re.sub(r'\s+', ' ', expr).strip()

    # Handle malformed ternary operator results
    if ":" in expr and "?" not in expr:
        number_match = re.search(r'\d+', expr)
        if number_match:
            expr = number_match.group(0)

    return eval(expr, {}, context)
