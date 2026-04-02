#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
VHDL IR Builder.

This module builds the HDLr IR from VHDL AST.
It maps VHDL constructs to the common IR used by Verilog/SystemVerilog.
"""

from ..common.ir_builder_base import IRBuilder

from ...ir.module import Module
from ...ir.port import Port
from ...ir.signal import Signal
from ...ir.parameter import Parameter
from ...ir.instance import Instance


class VhdlIRBuilder(IRBuilder):
    """VHDL Class to build the IR"""

    def build(self, tree):
        """
        Build IR from VHDL AST.

        Args:
            tree: Tree-sitter AST

        Returns:
            List of Module objects
        """
        modules = []

        # VHDL can have entities and architectures in separate design units
        # First pass: collect all entities
        entities = {}  # entity_name -> entity_node

        # Second pass: collect all architectures and match with entities
        root = tree.root_node
        for child in root.children:
            if child.type == "design_unit":
                for sub_child in child.children:
                    if sub_child.type == "entity_declaration":
                        # Extract entity name
                        entity_name = self._extract_entity_name(sub_child)
                        entities[entity_name] = sub_child
                    elif sub_child.type == "architecture_definition":
                        # Extract entity name that this architecture belongs to
                        arch_entity_name = self._extract_architecture_entity_name(sub_child)

                        # If we have the corresponding entity, build the module
                        if arch_entity_name in entities:
                            entity_node = entities[arch_entity_name]
                            module = self._build_module(entity_node, sub_child)
                            if module:
                                modules.append(module)
                                # Remove from entities to avoid duplicates
                                del entities[arch_entity_name]

        # Any remaining entities without architectures
        for entity_name, entity_node in entities.items():
            module = self._build_module(entity_node, None)
            if module:
                modules.append(module)

        return modules

    def _build_module(self, entity_node, architecture_node):
        """
        Build module from entity + architecture pair.

        Args:
            entity_node: entity_declaration node
            architecture_node: architecture_definition node

        Returns:
            Module object
        """
        entity_name = self._extract_entity_name(entity_node)
        module = Module(name=entity_name)

        # Extract entity information
        self._extract_parameters(entity_node, module)
        self._extract_ports(entity_node, module)

        if architecture_node is not None:
            # Extract architecture information
            self._extract_signals(architecture_node, module, None)
            self._extract_instances(architecture_node, module, None)

        return module

    # --------------------------------------------------------------
    # VHDL-specific helper methods
    # --------------------------------------------------------------

    def _get_name_text(self, node):
        """Get text from a name node (can be compound).

        Args:
            node: Name node

        Returns:
            Concatenated name text
        """
        if not node or node.type != "name":
            return ""

        parts = []
        for child in node.children:
            if child.type == "identifier":
                parts.append(self._get_text(child))

        return "_".join(parts) if parts else ""

    def _get_expression_text(self, node):
        """Get text from an expression node (VHDL-specific override).

        Args:
            node: Expression node

        Returns:
            Expression text, or empty string if not found
        """
        if not node:
            return ""

        # Try to find the most specific expression child (VHDL types)
        expr_types = ["decimal_integer", "identifier", "literal", "simple_expression"]
        for expr_type in expr_types:
            expr_node = self._first(node, expr_type)
            if expr_node:
                return self._get_text(expr_node)

        # For initialiser nodes, look for the actual value
        if node.type == "initialiser":
            # Look for variable_assignment (:=) and get what comes after
            for child in node.children:
                if child.type == "variable_assignment":
                    # Get the next sibling after variable_assignment
                    found_assignment = False
                    for child in node.children:
                        if found_assignment and child.type in ["decimal_integer", "identifier", "literal", "conditional_expression"]:
                            return self._get_text(child)
                        if child.type == "variable_assignment":
                            found_assignment = True
                    break

        # Fallback: return the whole node text
        return self._get_text(node)

    def _extract_entity_name(self, entity_node):
        """
        Extract entity name from entity_declaration node.

        Args:
            entity_node: entity_declaration node

        Returns:
            Entity name as string
        """
        # Use _first() method from base class
        id_node = self._first(entity_node, "identifier")
        if id_node:
            return self._get_text(id_node)
        return "unknown"

    def _extract_architecture_entity_name(self, architecture_node):
        """
        Extract entity name from architecture_definition node.

        Args:
            architecture_node: architecture_definition node

        Returns:
            Entity name as string
        """
        # Use _first() method from base class
        name_node = self._first(architecture_node, "name")
        if name_node:
            return self._get_name_text(name_node)
        return "unknown"

    def _extract_parameters(self, entity_node, module):
        """
        Extract generics from entity and map them to parameters.

        Args:
            entity_node: entity_declaration node
            module: Module object to populate
        """
        # Find generic clause in entity (could be in entity_head)
        generic_clause = self._first(entity_node, "generic_clause")
        if not generic_clause:
            # Look inside entity_head for generic_clause
            entity_head = self._first(entity_node, "entity_head")
            if entity_head:
                generic_clause = self._first(entity_head, "generic_clause")

        if not generic_clause:
            return

        # Find interface_list in generic clause
        interface_list = self._first(generic_clause, "interface_list")
        if not interface_list:
            return

        # Extract each generic declaration
        for interface_decl in self._all(interface_list, "interface_declaration"):
            self._extract_single_parameter(interface_decl, module)

    def _extract_single_parameter(self, interface_decl, module):
        """
        Extract a single parameter from interface_declaration node.

        Args:
            interface_decl: interface_declaration node
            module: Module object to populate
        """
        name = ""
        value = None

        # Extract name from identifier_list
        id_list = self._first(interface_decl, "identifier_list")
        if id_list:
            # Get first identifier (VHDL allows multiple names, but we take first)
            id_node = self._first(id_list, "identifier")
            if id_node:
                name = self._get_text(id_node)
            elif not name:  # Try library_type as fallback
                id_node = self._first(id_list, "library_type")
                if id_node:
                    name = self._get_text(id_node)

        # Extract value from simple_mode_indication
        mode_indication = self._first(interface_decl, "simple_mode_indication")
        if mode_indication:
            initialiser = self._first(mode_indication, "initialiser")
            if initialiser:
                value = self._get_expression_text(initialiser)

        if name:
            # Create parameter - store as string to match Verilog behavior
            if value is not None:
                param = Parameter(name=name, value_str=str(value))
            else:
                # No default value
                param = Parameter(name=name)

            module.parameters.append(param)

    def _extract_ports(self, entity_node, module):
        """
        Extract ports from entity and map VHDL directions to IR.

        Args:
            entity_node: entity_declaration node
            module: Module object to populate
        """
        # Find port clause in entity (could be in entity_head)
        port_clause = self._first(entity_node, "port_clause")
        if not port_clause:
            # Look inside entity_head for port_clause
            entity_head = self._first(entity_node, "entity_head")
            if entity_head:
                port_clause = self._first(entity_head, "port_clause")

        if not port_clause:
            return

        # Find interface_list in port clause
        interface_list = self._first(port_clause, "interface_list")
        if not interface_list:
            return

        # Map VHDL directions to IR directions, as done for verilog
        direction_map = {
            "in": "input",
            "out": "output",
            "inout": "inout",
            "buffer": "output",  # VHDL buffer maps to output
        }

        # Extract each port declaration
        for interface_decl in self._all(interface_list, "interface_declaration"):
            self._extract_single_port(interface_decl, module, direction_map)

    def _extract_single_port(self, interface_decl, module, direction_map):
        """
        Extract a single port from interface_declaration node.

        Args:
            interface_decl: interface_declaration node
            module: Module object to populate
            direction_map: Direction mapping dictionary
        """
        name = ""
        direction = "input"  # default
        width = None

        # Extract name from identifier_list
        id_list = self._first(interface_decl, "identifier_list")
        if id_list:
            id_node = self._first(id_list, "identifier")
            if id_node:
                name = self._get_text(id_node)

        # Extract direction and width from simple_mode_indication
        mode_indication = self._first(interface_decl, "simple_mode_indication")
        if mode_indication:
            # Extract direction
            mode_node = self._first(mode_indication, "mode")
            if mode_node:
                direction_text = self._get_text(mode_node)
                direction = direction_map.get(direction_text, "input")

            # Extract width from std_logic_vector in simple_mode_indication
            width = self._extract_width_from_simple_mode(mode_indication)

        if name:
            port_obj = Port(name=name, direction=direction)

            # Handle width if present
            if width:
                port_obj.width_str = width

            module.ports.append(port_obj)

    def _extract_width_from_simple_mode(self, simple_mode_node):
        """
        Extract width from simple_mode_indication (e.g., out std_logic_vector(7 downto 0)).

        Args:
            simple_mode_node: simple_mode_indication node

        Returns:
            Tuple of (msb, lsb) as strings, or None
        """
        # Look for subtype_indication within simple_mode_indication
        subtype_indication = self._first(simple_mode_node, "subtype_indication")
        if subtype_indication:
            return self._extract_width_from_subtype(subtype_indication)

        return None

    def _extract_width_from_subtype(self, subtype_node):
        """
        Extract width from subtype_indication (e.g., std_logic_vector(7 downto 0)).

        Args:
            subtype_node: subtype_indication node

        Returns:
            Tuple of (msb, lsb) as strings, or None
        """
        # Look for array_range_constraint (Verilog-style)
        range_constraint = self._first(subtype_node, "array_range_constraint")
        if range_constraint:
            # Should have format like (7 downto 0)
            range_node = self._first(range_constraint, "range")
            if range_node:
                # Extract msb, lsb, and direction
                msb = None
                lsb = None
                direction = None

                for part in range_node.children:
                    if part.type == "expression":
                        if msb is None:
                            msb = self._get_text(part)
                        else:
                            lsb = self._get_text(part)
                    elif part.type in ["downto", "to"]:
                        direction = self._get_text(part)

                if msb and lsb:
                    # For "downto"
                    if direction == "downto":
                        return (msb, lsb)
                    # For "to"
                    return (lsb, msb)

        # Look for parenthesis_group (VHDL-style)
        name_node = self._first(subtype_node, "name")
        if name_node:
            parenthesis_group = self._first(name_node, "parenthesis_group")
            if parenthesis_group:
                # Extract range from parenthesis_group like "(3 downto 0)"
                group_text = self._get_text(parenthesis_group)
                # Remove parentheses
                content = group_text.strip("()")
                # Split by downto/to
                if "downto" in content:
                    parts = content.split("downto")
                    if len(parts) == 2:
                        msb = parts[0].strip()
                        lsb = parts[1].strip()
                        return (msb, lsb)
                elif "to" in content:
                    parts = content.split("to")
                    if len(parts) == 2:
                        lsb = parts[0].strip()  # VHDL "to" is ascending
                        msb = parts[1].strip()
                        return (msb, lsb)

        return None

    def _extract_signals(self, architecture_node, module, condition=None):
        """
        Extract signals from architecture.

        Args:
            architecture_node: architecture_definition node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        # Look for signal declarations in architecture_head
        for child in architecture_node.children:
            if child.type == "architecture_head":
                self._get_signals(child, module, condition)
                self._extract_constants_from_head(child, module, condition)
            elif child.type == "concurrent_block":
                self._get_signals(child, module, condition)
            elif child.type == "for_generate_statement":
                self._extract_for_generate_statement(child, module)
            elif child.type == "if_generate_statement":
                self._extract_if_generate_statement(child, module)

    def _get_signals(self, node, module, condition=None):
        """
        Extract signals from architecture_head.

        Args:
            head_node: architecture_head node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        # Signal declarations can be direct children of architecture_head
        for child in node.children:
            if child.type == "signal_declaration":
                self._extract_signal_declaration(child, module, condition)

    def _extract_signal_declaration(self, signal_decl, module, condition=None):
        """
        Extract signals from a signal_declaration node.

        Args:
            signal_decl: signal_declaration node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        # Extract signal names and subtype using _first() method
        identifier_list = self._first(signal_decl, "identifier_list")
        subtype = self._first(signal_decl, "subtype_indication")

        if not identifier_list or not subtype:
            return

        # Extract width from subtype
        width = self._extract_width_from_subtype(subtype)

        # Any VHDL type is considered as verilog's logic type
        kind = "logic"

        # Extract each signal name
        for id_child in identifier_list.children:
            if id_child.type == "identifier":
                name = self._get_text(id_child)
                signal_obj = Signal(name=name, kind=kind)

                # Handle width if present
                if width:
                    signal_obj.width_str = width

                # Apply condition if this signal is in a generate block
                if condition:
                    signal_obj.condition = condition

                module.signals.append(signal_obj)

    def _extract_constants_from_head(self, head_node, module, condition=None):
        """
        Extract constants from architecture_head.

        Args:
            head_node: architecture_head node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        # Constant declarations can be direct children of architecture_head
        for child in head_node.children:
            if child.type == "constant_declaration":
                self._extract_constant_declaration(child, module, condition)

    def _extract_constant_declaration(self, const_decl, module, condition=None):
        """
        Extract a constant from a constant_declaration node.

        Args:
            const_decl: constant_declaration node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        name = ""
        value = None

        # Extract name from identifier_list
        id_list = self._first(const_decl, "identifier_list")
        if id_list:
            id_node = self._first(id_list, "identifier")
            if id_node:
                name = self._get_text(id_node)

        # Extract value from initialiser
        initialiser = self._first(const_decl, "initialiser")
        if initialiser:
            # Try to get conditional_expression first
            cond_expr = self._first(initialiser, "conditional_expression")
            if cond_expr:
                value = self._get_expression_text(cond_expr)
            else:
                # Fallback to direct value types
                value = self._get_expression_text(initialiser)

        if name:
            # Create parameter - store as string to match Verilog behavior
            if value is not None:
                param = Parameter(name=name, value_str=str(value))
            else:
                # No value (shouldn't happen for constants, but handle gracefully)
                param = Parameter(name=name)

            # Apply condition if this constant is in a generate block
            if condition:
                param.condition = condition

            module.parameters.append(param)

    def _extract_instances(self, architecture_node, module, condition=None):
        """
        Extract component instances from architecture.

        Args:
            architecture_node: architecture_definition node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        # Look for component instantiations in architecture
        for child in architecture_node.children:
            if child.type == "concurrent_block":
                self._extract_instances_from_block(child, module, condition)

    def _extract_instances_from_block(self, block_node, module, condition=None):
        """
        Extract instances from a block (concurrent_block).

        Args:
            block_node: concurrent_block node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        for child in block_node.children:
            if child.type == "component_instantiation_statement":
                self._extract_component_instance(child, module, condition)
            elif child.type == "for_generate_statement":
                self._extract_for_generate_statement(child, module)
            elif child.type == "if_generate_statement":
                self._extract_if_generate_statement(child, module)

    def _extract_component_instance(self, inst_node, module, condition=None):
        """
        Extract a component instance from component_instantiation_statement.

        Args:
            inst_node: component_instantiation_statement node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        name = ""
        module_name = ""
        parameters = {}
        connections = {}

        # Extract instance name (label_declaration)
        for child in inst_node.children:
            if child.type == "label_declaration":
                # label_declaration contains the instance name
                for label_child in child.children:
                    if label_child.type == "identifier":
                        name = label_child.text.decode("utf8")
                        break
                    if label_child.type == "label":
                        # Alternative: name is in label node
                        name = label_child.text.decode("utf8")
                        break
            elif child.type == "instantiated_unit":
                # Extract module name
                for unit_child in child.children:
                    if unit_child.type == "name":
                        module_name = self._extract_module_name_from_name(unit_child)
                        break
            elif child.type == "name":
                # Direct name (alternative VHDL syntax)
                module_name = self._extract_module_name_from_name(child)
            elif child.type == "generic_map_aspect":
                # Extract parameters
                parameters = self._extract_parameters_from_generic_map(child)
            elif child.type == "port_map_aspect":
                # Extract connections
                connections = self._extract_connections_from_port_map(child)

        if name and module_name:
            instance_obj = Instance(
                name=name, module_name=module_name, parameters=parameters, connections=connections
            )

            # Apply condition if this instance is in a generate block
            if condition:
                instance_obj.condition = condition

            module.instances.append(instance_obj)

    def _extract_module_name_from_name(self, name_node):
        """
        Extract module name from name node.

        Args:
            name_node: name node

        Returns:
            Module name as string
        """
        # Use the existing _get_name_text helper method
        return self._get_name_text(name_node)

    def _extract_for_generate_statement(self, for_gen_node, module):
        """
        Extract for generate statement and apply conditions to contained elements.

        Args:
            for_gen_node: for_generate_statement node
            module: Module object to populate
        """
        # Extract loop variable and range
        loop_var = ""
        range_start = ""
        range_end = ""
        direction = "to"  # default

        # Find parameter_specification (inside for_loop)
        for child in for_gen_node.children:
            if child.type == "for_loop":
                # Look inside for_loop for parameter_specification
                for loop_child in child.children:
                    if loop_child.type == "parameter_specification":
                        # Extract loop variable
                        for param_child in loop_child.children:
                            if param_child.type == "identifier":
                                loop_var = param_child.text.decode("utf8")
                            elif param_child.type == "simple_range":
                                # Extract range
                                for range_child in param_child.children:
                                    if range_child.type == "simple_expression":
                                        if not range_start:
                                            range_start = range_child.text.decode("utf8")
                                        else:
                                            range_end = range_child.text.decode("utf8")
                                    elif range_child.type in ["to", "downto"]:
                                        direction = range_child.text.decode("utf8")

        # Create condition string
        if loop_var and range_start and range_end:
            if direction == "downto":
                condition = f"{loop_var} <= {range_start}"
            else:  # "to"
                # For "to" direction, we need to handle the end range properly
                # If range_end contains arithmetic (like DEPTH-1), we need to adjust
                if "-" in range_end:
                    # Handle expressions like DEPTH-1 by adding 1 to both sides
                    condition = f"{loop_var} < {range_end.split('-')[0].strip()}"
                else:
                    condition = f"{loop_var} < {range_end}"
        else:
            condition = None

        # Extract generate body
        for child in for_gen_node.children:
            if child.type == "generate_body":
                # Process the body with the condition
                for body_child in child.children:
                    if body_child.type == "generate_block":
                        self._extract_generate_block(body_child, module, condition)
                    elif body_child.type == "generate_head":
                        # Extract signals declared in generate head
                        self._get_signals(body_child, module, condition)

    def _extract_if_generate_statement(self, if_gen_node, module):
        """
        Extract if generate statement and apply conditions to contained elements.

        Args:
            if_gen_node: if_generate_statement node
            module: Module object to populate
        """
        # Extract condition
        condition = None

        # Find condition expression
        for child in if_gen_node.children:
            if child.type == "condition":
                # Extract the condition expression
                for cond_child in child.children:
                    if cond_child.type == "expression":
                        condition = cond_child.text.decode("utf8")
                        break

        # Extract generate body
        for child in if_gen_node.children:
            if child.type == "generate_body":
                # Process the body with the condition
                for body_child in child.children:
                    if body_child.type == "generate_block":
                        self._extract_generate_block(body_child, module, condition)

    def _extract_generate_block(self, gen_block_node, module, condition=None):
        """
        Extract elements from a generate block.

        Args:
            gen_block_node: generate_block node
            module: Module object to populate
            condition: Condition string to apply
        """
        for child in gen_block_node.children:
            if child.type == "concurrent_block":
                # Extract signals and instances with condition
                self._get_signals(child, module, condition)
                self._extract_instances_from_block(child, module, condition)
            elif child.type == "component_instantiation_statement":
                # Direct instance in generate block
                self._extract_component_instance(child, module, condition)

    def _extract_parameters_from_generic_map(self, generic_map_node):
        """
        Extract parameters from generic_map_aspect.

        Args:
            generic_map_node: generic_map_aspect node

        Returns:
            Dictionary of parameter names and values
        """
        parameters = {}

        # Find association_list
        association_list = self._first(generic_map_node, "association_list")
        if not association_list:
            return parameters

        # Process each association element
        for assoc in self._all(association_list, "association_element"):
            param_name = ""
            param_value = ""

            # Extract parameter name from name node
            name_node = self._first(assoc, "name")
            if name_node:
                param_name = self._get_text(name_node)

            # Extract parameter value from various expression types
            value_node = None
            for value_type in ["conditional_expression", "literal", "identifier"]:
                potential_node = self._first(assoc, value_type)
                if potential_node:
                    value_node = potential_node
                    break

            if value_node:
                param_value = self._get_text(value_node)

            if param_name and param_value:
                parameters[param_name] = param_value

        return parameters

    def _extract_connections_from_port_map(self, port_map_node):
        """
        Extract connections from port_map_aspect.

        Args:
            port_map_node: port_map_aspect node

        Returns:
            Dictionary of port connections
        """
        connections = {}

        # Find association_list
        association_list = self._first(port_map_node, "association_list")
        if not association_list:
            return connections

        # Process each association element
        for assoc in self._all(association_list, "association_element"):
            port_name = ""
            signal_name = ""

            # Extract port name from name node
            name_node = self._first(assoc, "name")
            if name_node:
                # Try identifier first, then library_type
                port_name = self._get_identifier_text(name_node)
                if not port_name:
                    id_node = self._first(name_node, "library_type")
                    if id_node:
                        port_name = self._get_text(id_node)

            # Extract signal name from conditional_expression
            cond_expr = self._first(assoc, "conditional_expression")
            if cond_expr:
                signal_name = self._get_expression_text(cond_expr)

            if port_name and signal_name:
                connections[port_name] = signal_name

        return connections
