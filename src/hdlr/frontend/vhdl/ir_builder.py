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
                            module = self._build_module_from_entity_arch(entity_node, sub_child)
                            if module:
                                modules.append(module)
                                # Remove from entities to avoid duplicates
                                del entities[arch_entity_name]

        # Any remaining entities without architectures
        for entity_name, entity_node in entities.items():
            module = self._build_module_from_entity_only(entity_node)
            if module:
                modules.append(module)

        return modules

    def _build_module_from_entity_arch(self, entity_node, architecture_node):
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

        # Extract architecture information
        self._extract_signals(architecture_node, module, None)
        self._extract_instances(architecture_node, module, None)

        return module

    def _build_module_from_entity_only(self, entity_node):
        """
        Build module from standalone entity (no architecture).

        Args:
            entity_node: entity_declaration node

        Returns:
            Module object
        """
        entity_name = self._extract_entity_name(entity_node)
        module = Module(name=entity_name)

        # Extract entity information
        self._extract_parameters(entity_node, module)
        self._extract_ports(entity_node, module)

        return module

    def _build_design_unit(self, node):
        """
        Build module from a design unit (entity + architecture).

        Args:
            node: design_unit node

        Returns:
            Module object or None
        """
        entity_node = None
        architecture_node = None

        for child in node.children:
            if child.type == "entity_declaration":
                entity_node = child
            elif child.type == "architecture_definition":
                architecture_node = child

        if entity_node and architecture_node:
            entity_name = self._extract_entity_name(entity_node)
            module = Module(name=entity_name)

            # Extract entity information
            self._extract_parameters(entity_node, module)
            self._extract_ports(entity_node, module)

            # Extract architecture information
            self._extract_signals(architecture_node, module)
            self._extract_instances(architecture_node, module)

            return module

        return None

    def _extract_entity_name(self, entity_node):
        """
        Extract entity name from entity_declaration node.

        Args:
            entity_node: entity_declaration node

        Returns:
            Entity name as string
        """
        for child in entity_node.children:
            if child.type == "identifier":
                return child.text.decode("utf8")
        return "unknown"

    def _extract_architecture_entity_name(self, architecture_node):
        """
        Extract entity name from architecture_definition node.

        Args:
            architecture_node: architecture_definition node

        Returns:
            Entity name as string
        """
        for child in architecture_node.children:
            if child.type == "name":
                # The name node contains the entity name
                for name_child in child.children:
                    if name_child.type == "identifier":
                        return name_child.text.decode("utf8")
        return "unknown"

    def _extract_parameters(self, entity_node, module):
        """
        Extract generics from entity and map them to parameters.

        Args:
            entity_node: entity_declaration node
            module: Module object to populate
        """
        # Find generic clause in entity (could be in entity_head)
        generic_clause = None
        for child in entity_node.children:
            if child.type == "generic_clause":
                generic_clause = child
                break
            elif child.type == "entity_head":
                # Look inside entity_head for generic_clause
                for sub_child in child.children:
                    if sub_child.type == "generic_clause":
                        generic_clause = sub_child
                        break

        if not generic_clause:
            return

        # Find interface_list in generic clause
        interface_list = None
        for child in generic_clause.children:
            if child.type == "interface_list":
                interface_list = child
                break

        if not interface_list:
            return

        # Extract each generic declaration
        for child in interface_list.children:
            if child.type == "interface_declaration":
                self._extract_single_parameter(child, module)

    def _extract_single_parameter(self, interface_decl, module):
        """
        Extract a single parameter from interface_declaration node.

        Args:
            interface_decl: interface_declaration node
            module: Module object to populate
        """
        name = ""
        value = None

        # Extract name and value from interface_declaration children
        for child in interface_decl.children:
            if child.type == "identifier_list":
                # Get first identifier (VHDL allows multiple names, but we take first)
                for id_child in child.children:
                    if id_child.type in ["identifier", "library_type"]:
                        name = id_child.text.decode("utf8")
                        break
            elif child.type == "simple_mode_indication":
                # In VHDL generics, the value might be in the simple_mode_indication
                # Look for initialiser node
                for sub_child in child.children:
                    if sub_child.type == "initialiser":
                        # Extract value from initialiser
                        for init_child in sub_child.children:
                            if init_child.type in [
                                "expression",
                                "literal",
                                "identifier",
                                "conditional_expression",
                            ]:
                                value = init_child.text.decode("utf8")
                                break
                        break

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
        port_clause = None
        for child in entity_node.children:
            if child.type == "port_clause":
                port_clause = child
                break
            elif child.type == "entity_head":
                # Look inside entity_head for port_clause
                for sub_child in child.children:
                    if sub_child.type == "port_clause":
                        port_clause = sub_child
                        break

        if not port_clause:
            return

        # Find interface_list in port clause
        interface_list = None
        for child in port_clause.children:
            if child.type == "interface_list":
                interface_list = child
                break

        if not interface_list:
            return

        # Map VHDL directions to IR directions
        direction_map = {
            "in": "input",
            "out": "output",
            "inout": "inout",
            "buffer": "output",  # VHDL buffer maps to output
        }

        # Extract each port declaration
        for child in interface_list.children:
            if child.type == "interface_declaration":
                self._extract_single_port(child, module, direction_map)

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

        # Extract name, direction, and width
        for child in interface_decl.children:
            if child.type == "identifier_list":
                # Get first identifier (VHDL allows multiple names, but we take first)
                for id_child in child.children:
                    if id_child.type == "identifier":
                        name = id_child.text.decode("utf8")
                        break
            elif child.type == "simple_mode_indication":
                # Extract direction
                for mode_child in child.children:
                    if mode_child.type == "mode":
                        direction = direction_map.get(mode_child.text.decode("utf8"), "input")
                        break
                # Extract width from std_logic_vector in simple_mode_indication
                width = self._extract_width_from_simple_mode(child)

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
        for child in simple_mode_node.children:
            if child.type == "subtype_indication":
                return self._extract_width_from_subtype(child)

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
        for child in subtype_node.children:
            if child.type == "array_range_constraint":
                # Should have format like (7 downto 0)
                for range_child in child.children:
                    if range_child.type == "range":
                        # Extract msb and lsb
                        msb = None
                        lsb = None
                        direction = None

                        for part in range_child.children:
                            if part.type == "expression":
                                if msb is None:
                                    msb = part.text.decode("utf8")
                                else:
                                    lsb = part.text.decode("utf8")
                            elif part.type in ["downto", "to"]:
                                direction = part.text.decode("utf8")

                        if msb and lsb:
                            # For "downto", return (msb, lsb)
                            # For "to", return (lsb, msb) since VHDL "to" is ascending
                            if direction == "downto":
                                return (msb, lsb)
                            else:  # "to"
                                return (lsb, msb)

        # Look for parenthesis_group (VHDL-style)
        for child in subtype_node.children:
            if child.type == "name":
                for name_child in child.children:
                    if name_child.type == "parenthesis_group":
                        # Extract range from parenthesis_group like "(3 downto 0)"
                        group_text = name_child.text.decode("utf8")
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
                self._extract_signals_from_head(child, module, condition)
                self._extract_constants_from_head(child, module, condition)
            elif child.type == "concurrent_block":
                self._extract_signals_from_block(child, module, condition)
            elif child.type == "for_generate_statement":
                self._extract_for_generate_statement(child, module)
            elif child.type == "if_generate_statement":
                self._extract_if_generate_statement(child, module)

    def _extract_signals_from_head(self, head_node, module, condition=None):
        """
        Extract signals from architecture_head.

        Args:
            head_node: architecture_head node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        # Signal declarations can be direct children of architecture_head
        for child in head_node.children:
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
        # Extract signal names
        identifier_list = None
        subtype = None

        for child in signal_decl.children:
            if child.type == "identifier_list":
                identifier_list = child
            elif child.type == "subtype_indication":
                subtype = child

        if not identifier_list or not subtype:
            return

        # Extract width from subtype
        width = self._extract_width_from_subtype(subtype)

        # Determine signal kind based on subtype
        kind = self._determine_signal_kind(subtype)

        # Extract each signal name
        for id_child in identifier_list.children:
            if id_child.type == "identifier":
                name = id_child.text.decode("utf8")
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

        # Extract name and value from constant_declaration children
        for child in const_decl.children:
            if child.type == "identifier_list":
                # Get first identifier (VHDL allows multiple names, but we take first)
                for id_child in child.children:
                    if id_child.type == "identifier":
                        name = id_child.text.decode("utf8")
                        break
            elif child.type == "initialiser":
                # Extract value from initialiser
                for init_child in child.children:
                    if init_child.type == "conditional_expression":
                        # Look for the actual value in conditional_expression
                        for expr_child in init_child.children:
                            if expr_child.type in ["decimal_integer", "identifier", "literal", "simple_expression"]:
                                value = expr_child.text.decode("utf8")
                                break
                        else:
                            # If no specific child matched, use the whole conditional_expression
                            value = init_child.text.decode("utf8")
                        break
                    elif init_child.type in ["decimal_integer", "identifier", "literal"]:
                        value = init_child.text.decode("utf8")
                        break

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

    def _determine_signal_kind(self, subtype_node):
        """
        Determine signal kind from subtype_indication.

        Args:
            subtype_node: subtype_indication node

        Returns:
            Signal kind as string
        """
        # Look for the base type name
        for child in subtype_node.children:
            if child.type == "name":
                type_name = ""
                # Build the full type name
                for part in child.children:
                    if part.type == "identifier":
                        type_name += part.text.decode("utf8")

                # Map VHDL types to IR kinds
                if type_name in ["std_logic", "std_ulogic", "bit"]:
                    return "logic"
                elif type_name == "std_logic_vector":
                    return "logic"
                elif type_name == "integer":
                    return "logic"  # Treat integer as logic for now
                else:
                    return "logic"  # Default

        return "logic"

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
                    elif label_child.type == "label":
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
        module_name = ""
        for child in name_node.children:
            if child.type == "identifier":
                if module_name:
                    module_name += "_"
                module_name += child.text.decode("utf8")
        return module_name

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
                        self._extract_signals_from_generate_head(body_child, module, condition)

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
                self._extract_signals_from_block(child, module, condition)
                self._extract_instances_from_block(child, module, condition)
            elif child.type == "component_instantiation_statement":
                # Direct instance in generate block
                self._extract_component_instance(child, module, condition)

    def _extract_signals_from_block(self, block_node, module, condition=None):
        """
        Extract signals from a block (concurrent_block).

        Args:
            block_node: concurrent_block node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        for child in block_node.children:
            if child.type == "signal_declaration":
                self._extract_signal_declaration(child, module, condition)

    def _extract_signals_from_generate_head(self, generate_head_node, module, condition=None):
        """
        Extract signals from a generate_head node.

        Args:
            generate_head_node: generate_head node
            module: Module object to populate
            condition: Optional condition string for generate blocks
        """
        for child in generate_head_node.children:
            if child.type == "signal_declaration":
                self._extract_signal_declaration(child, module, condition)

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
        for child in generic_map_node.children:
            if child.type == "association_list":
                for assoc in child.children:
                    if assoc.type == "association_element":
                        param_name = ""
                        param_value = ""

                        # VHDL structure: name => value (no formal/actual parts)
                        # Look for name and value directly in children
                        for i, part in enumerate(assoc.children):
                            if part.type == "name":
                                # Extract parameter name
                                param_name = part.text.decode("utf8")
                            elif part.type == "conditional_expression":
                                # Extract parameter value
                                param_value = part.text.decode("utf8")
                            elif part.type == "literal":
                                # Alternative: value in literal
                                param_value = part.text.decode("utf8")
                            elif part.type == "identifier":
                                # Alternative: value in identifier
                                param_value = part.text.decode("utf8")

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
        for child in port_map_node.children:
            if child.type == "association_list":
                for assoc in child.children:
                    if assoc.type == "association_element":
                        port_name = ""
                        signal_name = ""

                        # VHDL structure: name => conditional_expression
                        # Look for name and conditional_expression directly in children
                        for part in assoc.children:
                            if part.type == "name":
                                # Extract port name from name node
                                for name_child in part.children:
                                    if name_child.type in ["identifier", "library_type"]:
                                        port_name = name_child.text.decode("utf8")
                                        break
                            elif part.type == "conditional_expression":
                                # Extract signal name from conditional_expression
                                # Look for identifier in the expression
                                for expr_child in part.children:
                                    if expr_child.type == "simple_expression":
                                        for simple_child in expr_child.children:
                                            if simple_child.type == "name":
                                                for name_child in simple_child.children:
                                                    if name_child.type == "identifier":
                                                        signal_name = name_child.text.decode("utf8")
                                                        break
                                            elif simple_child.type == "identifier":
                                                signal_name = simple_child.text.decode("utf8")
                                                break
                                    elif expr_child.type == "identifier":
                                        signal_name = expr_child.text.decode("utf8")
                                        break

                        if port_name and signal_name:
                            connections[port_name] = signal_name

        return connections
