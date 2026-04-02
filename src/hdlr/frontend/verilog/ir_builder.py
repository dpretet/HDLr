#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from ...ir.instance import Instance
from ...ir.module import Module
from ...ir.parameter import Parameter
from ...ir.port import Port
from ...ir.signal import Signal
from ..common.ir_builder_base import IRBuilder

# from ..common.debugging import ts_print


class VerilogIRBuilder(IRBuilder):
    """ Verilog Class to buidl the IR """

    # ---------------------------------------------------------
    # Entry
    # ---------------------------------------------------------

    def build(self, tree):
        modules = []

        root = tree.root_node
        for child in root.children:
            if child.type == "module_declaration":
                modules.append(self._build_module(child))

        return modules

    # ---------------------------------------------------------
    # Module
    # ---------------------------------------------------------

    def _build_module(self, node):

        name = self._extract_module_name(node)
        module = Module(name=name)
        self._extract_parameters(node, module)
        self._extract_ports(node, module)
        self._extract_signals(node, module)
        self._extract_instances(node, module)

        return module

    def _extract_module_name(self, node):

        header = self._first(node, "module_header")

        if header is None:
            raise RuntimeError("module_header introuvable")

        name_node = self._first(header, "simple_identifier")

        if name_node is None:
            raise RuntimeError("Nom du module introuvable")

        return self._get_text(name_node)

    # ---------------------------------------------------------
    # Ports (ANSI style)
    # ---------------------------------------------------------

    def _extract_ports(self, node, module):

        ansi_header = self._first(node, "module_ansi_header")

        if ansi_header is None:
            return

        port_list = self._first(ansi_header, "list_of_port_declarations")

        if port_list is None:
            return

        for port_decl in port_list.children:
            if port_decl.type == "ansi_port_declaration":
                port = self._build_ansi_port(port_decl)
                if port:
                    module.ports.append(port)

    def _build_ansi_port(self, node):
        direction = None
        width = None
        name = None

        for child in node.children:

            # direction + net type
            if child.type in ("net_port_header1", "variable_port_header"):
                direction = self._extract_direction(child)
                width = self._extract_width(child)

            # port name
            if child.type == "port_identifier":
                ident = self._first(child, "simple_identifier")
                if ident:
                    name = self._get_text(ident)

        if name is None:
            return None

        return Port(
            name=name,
            direction=direction,
            width_str=width
        )

    # ---------------------------------------------------------
    # Parameters (ANSI style)
    # ---------------------------------------------------------

    def _extract_parameters(self, node, module):

        # -------------------------------------------------
        # 1️⃣ Header (ANSI + non-ANSI)
        # -------------------------------------------------

        header_nodes = [
            self._first(node, "module_ansi_header"),
            self._first(node, "module_nonansi_header"),
        ]

        for header in header_nodes:
            if not header:
                continue

            param_port_list = self._first(header, "parameter_port_list")

            if not param_port_list:
                continue

            for param_port_decl in param_port_list.children:

                param_decl = self._first(param_port_decl, "parameter_declaration")

                if param_decl:
                    self._handle_parameter_declaration(param_decl, module)

        # -------------------------------------------------
        # 2️⃣ Body parameters
        # -------------------------------------------------

        for item in node.children:

            if item.type != "module_or_generate_item":
                continue

            for pkg_decl in item.children:

                if pkg_decl.type != "package_or_generate_item_declaration":
                    continue

                for child in pkg_decl.children:

                    if child.type == "parameter_declaration":
                        self._handle_parameter_declaration(child, module)

                    elif child.type == "local_parameter_declaration":
                        self._handle_parameter_declaration(child, module)

    def _handle_parameter_declaration(self, node, module):

        list_node = self._first(node, "list_of_param_assignments")

        if not list_node:
            return

        for assignment in list_node.children:

            if assignment.type != "param_assignment":
                continue

            name_node = self._first(assignment, "parameter_identifier")

            value_node = None
            for child_type in ["expression", "constant_expression", "mintypmax_expression", "constant_param_expression"]:
                potential_node = self._first(assignment, child_type)
                if potential_node:
                    value_node = potential_node
                    break

            if not name_node:
                continue

            name = self._get_text(name_node)
            value = self._get_text(value_node) if value_node else None

            module.parameters.append(
                Parameter(
                    name=name,
                    value_str=value
                )
            )


    # ---------------------------------------------------------
    # Direction
    # ---------------------------------------------------------

    def _extract_direction(self, node):
        for child in node.children:
            if child.type == "port_direction":
                # child text = "input", "output", "inout"
                return child.text.decode()
        return None

    # ---------------------------------------------------------
    # Width extraction
    # ---------------------------------------------------------

    def _extract_width(self, node):
        """
        Cherche packed_dimension → constant_range
        Retourne tuple (msb, lsb) ou None
        """

        for child in node.children:
            if child.type == "data_type":
                return self._find_packed_dimension(child)

            if child.type.startswith("net_port_type"):
                return self._find_packed_dimension(child)

        return None

    def _find_packed_dimension(self, node):
        for child in node.children:
            if child.type == "packed_dimension":
                return self._extract_range(child)

            # récursif
            result = self._find_packed_dimension(child)
            if result:
                return result

        return None

    def _extract_range(self, node):
        """
        packed_dimension
            → constant_range
                → constant_expression
                → constant_expression
        """

        range_node = next(
            (c for c in node.children if c.type == "constant_range"),
            None
        )

        if range_node is None:
            return None

        exprs = [
            c for c in range_node.children
            if c.type == "constant_expression"
        ]

        if len(exprs) != 2:
            return None

        msb = exprs[0].text.decode()
        lsb = exprs[1].text.decode()

        return (msb, lsb)


    # ---------------------------------------------------------
    # Internal Signals
    # ---------------------------------------------------------

    def _extract_signals(self, node, module):

        for item in node.children:

            # 🆕 Handle generate blocks for Verilog (at module level)
            if item.type == "generate_region":
                self._extract_from_generate_blocks(item, module)
                continue

            if item.type != "module_or_generate_item":
                continue

            for pkg_decl in item.children:

                if pkg_decl.type != "package_or_generate_item_declaration":
                    continue

                # -------------------------
                # data_declaration
                # -------------------------
                for child in pkg_decl.children:

                    if child.type == "data_declaration":
                        signals = self._handle_data_declaration(child, module)
                        module.signals.extend(signals)

                    elif child.type == "net_declaration":
                        signals = self._handle_net_declaration(child, module)
                        module.signals.extend(signals)

    def _extract_from_generate_blocks(self, node, module):
        """Extract signals, parameters, and instances from Verilog generate blocks."""
        for item in node.children:
            if item.type == "module_or_generate_item":
                for subitem in item.children:
                    if subitem.type == "loop_generate_construct":
                        self._process_loop_generate(subitem, module)
                    elif subitem.type == "if_generate_construct":
                        self._process_conditional_generate(subitem, module)

    def _process_loop_generate(self, node, module):
        """Process Verilog loop generate constructs."""
        # Extract loop condition (e.g., "i < DEPTH")
        condition = self._extract_loop_condition(node)

        # Process each generate block in the loop
        for block in node.children:
            if block.type == "generate_block":
                self._extract_signals_from_block(block, module, condition)
                self._extract_instances_from_block(block, module, condition)

    def _process_conditional_generate(self, node, module):
        """Process Verilog conditional generate constructs."""
        # Extract the if condition (e.g., "WIDTH > 8")
        condition = self._extract_if_condition(node)

        for block in node.children:
            if block.type == "generate_block":
                self._extract_signals_from_block(block, module, condition)
                self._extract_instances_from_block(block, module, condition)

    def _extract_signals_from_block(self, block, module, condition):
        """Extract signals from a Verilog generate block with condition."""
        self._extract_signals_from_node_recursive(block, module, condition)

    def _extract_signals_from_node_recursive(self, node, module, condition):
        """Recursively extract signals from any node in Verilog generate blocks."""

        # Handle direct signal declarations
        if node.type == "data_declaration":
            signals = self._handle_data_declaration(node, module, condition)
            module.signals.extend(signals)
        elif node.type == "net_declaration":
            signals = self._handle_net_declaration(node, module, condition)
            module.signals.extend(signals)
        elif node.type == "loop_generate_construct":
            # Handle nested loop generate constructs - process the block but don't recurse into children
            nested_condition = self._extract_loop_condition(node)
            for block in node.children:
                if block.type == "generate_block":
                    self._extract_signals_from_node_recursive(block, module, nested_condition)
            return  # Don't process children of loop_generate_construct
        elif node.type == "if_generate_construct":
            # Handle nested conditional generate constructs - process the block but don't recurse into children
            nested_condition = self._extract_if_condition(node)
            for block in node.children:
                if block.type == "generate_block":
                    self._extract_signals_from_node_recursive(block, module, nested_condition)
            return  # Don't process children of if_generate_construct

        # Recursively process children (but not for generate constructs)
        for child in node.named_children:
            self._extract_signals_from_node_recursive(child, module, condition)

    def _extract_instances_from_block(self, block, module, condition):
        """Extract instances from a Verilog generate block with condition."""
        # Verilog has nested structure: generate_block -> module_or_generate_item -> udp_instantiation
        for item in block.named_children:
            if item.type == "module_instantiation":
                self._handle_module_instantiation(item, module, condition)
            elif item.type == "module_or_generate_item":
                # Deeper nesting in Verilog generate blocks
                for subitem in item.named_children:
                    if subitem.type == "udp_instantiation":
                        self._handle_module_instantiation(subitem, module, condition)
                    elif subitem.type == "package_or_generate_item_declaration":
                        for subsubitem in subitem.named_children:
                            if subsubitem.type == "udp_instantiation":
                                self._handle_module_instantiation(subsubitem, module, condition)

    def _extract_loop_condition(self, node):
        """Extract the loop condition from a Verilog loop generate construct."""
        # Look for constant_expression nodes that contain comparison operators
        for child in node.children:
            if child.type == "constant_expression":
                # Check if this looks like a comparison (contains operators)
                text = child.text.decode()
                if any(op in text for op in ['<', '>', '==', '!=', '<=', '>=']):
                    return text
            elif child.type == "generate_loop_statement":
                # Also check inside generate_loop_statement
                for subchild in child.children:
                    if subchild.type == "constant_expression":
                        text = subchild.text.decode()
                        if any(op in text for op in ['<', '>', '==', '!=', '<=', '>=']):
                            return text
        return None

    def _extract_if_condition(self, node):
        """Extract the if condition from a Verilog conditional generate construct."""
        # Find the condition expression
        # Verilog uses constant_expression for if conditions, not generate_conditional_expression
        for child in node.children:
            if child.type == "constant_expression":
                return child.text.decode()
        return None


    def _handle_data_declaration(self, node, module, condition=None):

        kind = None
        width = None

        # ✅ récupérer data_type_or_implicit1
        dtype_wrapper = next(
            (c for c in node.children if c.type.startswith("data_type_or_implicit")),
            None
        )

        if dtype_wrapper:
            data_type = next(
                (c for c in dtype_wrapper.children if c.type == "data_type"),
                None
            )

            if data_type:
                # type (logic, reg, etc.)
                base_type = next(
                    (c for c in data_type.children
                    if c.type in ("integer_vector_type", "net_type")),
                    None
                )

                if base_type:
                    kind = base_type.text.decode()

                # width
                packed_dim = next(
                    (c for c in data_type.children
                    if c.type == "packed_dimension"),
                    None
                )

                if packed_dim:
                    width = self._extract_range(packed_dim)

        # ✅ variables
        list_node = next(
            (c for c in node.children
            if c.type == "list_of_variable_decl_assignments"),
            None
        )

        if list_node is None:
            return []

        signals = []
        for var_decl in list_node.children:

            if var_decl.type != "variable_decl_assignment":
                continue

            ident = next(
                (c for c in var_decl.children
                if c.type == "simple_identifier"),
                None
            )

            if ident is None:
                continue

            signal = Signal(
                name=ident.text.decode(),
                kind=kind,
                width_str=width,
                condition=condition
            )
            signals.append(signal)

        return signals

    def _handle_net_declaration(self, node, module, condition=None):

        kind = None
        width = None

        # -------------------------
        # net_type (wire, tri, etc.)
        # -------------------------
        net_type_node = next(
            (c for c in node.children if c.type == "net_type"),
            None
        )

        if net_type_node:
            kind = net_type_node.text.decode()

        # -------------------------
        # packed_dimension (width)
        # -------------------------
        dtype_wrapper = next(
            (c for c in node.children
            if c.type.startswith("data_type_or_implicit")),
            None
        )

        if dtype_wrapper:
            width = self._find_packed_dimension(dtype_wrapper)

        # -------------------------
        # list_of_net_decl_assignments
        # -------------------------
        list_node = next(
            (c for c in node.children
            if c.type == "list_of_net_decl_assignments"),
            None
        )

        if not list_node:
            return []

        signals = []
        for decl in list_node.children:

            if decl.type != "net_decl_assignment":
                continue

            ident = next(
                (c for c in decl.children
                if c.type == "simple_identifier"),
                None
            )

            if not ident:
                continue

            signal = Signal(
                name=ident.text.decode(),
                kind=kind,   # "wire"
                width_str=width,
                condition=condition
            )
            signals.append(signal)

        return signals


    def _extract_instances(self, node, module):

        for item in node.children:

            if item.type != "module_or_generate_item":
                # 🆕 Handle generate blocks for instances (at module level)
                if item.type == "generate_region":
                    self._extract_instances_from_generate(item, module)
                continue

            # Handle both module_instantiation (normal instances) and udp_instantiation (generate block instances)
            for inst_node in self._all(item, "module_instantiation"):
                self._handle_module_instantiation(inst_node, module)

            for inst_node in self._all(item, "udp_instantiation"):
                self._handle_module_instantiation(inst_node, module)

    def _extract_instances_from_generate(self, node, module):
        """Extract instances from Verilog generate blocks."""
        for item in node.children:
            if item.type == "loop_generate_construct":
                self._process_loop_generate_instances(item, module)
            elif item.type == "conditional_generate_construct":
                self._process_conditional_generate_instances(item, module)

    def _process_loop_generate_instances(self, node, module):
        """Process Verilog loop generate constructs for instances."""
        condition = self._extract_loop_condition(node)
        for block in self._all(node, "generate_block"):
            self._extract_instances_from_block(block, module, condition)

    def _process_conditional_generate_instances(self, node, module):
        """Process Verilog conditional generate constructs for instances."""
        condition = self._extract_if_condition(node)
        for block in self._all(node, "generate_block"):
            self._extract_instances_from_block(block, module, condition)

    def _handle_module_instantiation(self, node, module, condition=None):

        # -------------------------
        # Module name
        # -------------------------
        module_name_node = next(
            (c for c in node.children
            if c.type == "simple_identifier"),
            None
        )

        if not module_name_node:
            return

        module_name = module_name_node.text.decode()

        # -------------------------
        # Parameter override
        # -------------------------
        param_node = next(
            (c for c in node.children
            if c.type == "parameter_value_assignment"),
            None
        )

        parameters = self._extract_param_override(param_node)

        # -------------------------
        # Instance (Verilog uses udp_instance, not hierarchical_instance)
        # -------------------------

        hier_nodes = list(self._all(node, "hierarchical_instance"))
        udp_instance_nodes = list(self._all(node, "udp_instance"))

        for hier_node in hier_nodes:
            instance = self._build_instance_from_hier(
                hier_node,
                module_name,
                parameters,
                condition
            )
            if instance:
                module.instances.append(instance)

        for udp_inst_node in udp_instance_nodes:
            instance = self._build_instance_from_udp_instance(
                udp_inst_node,
                module_name,
                parameters,
                condition
            )
            if instance:
                module.instances.append(instance)


    def _build_instance_from_hier(self, node, module_name, parameters, condition=None):

        # Instance name - Verilog uses simple_identifier for udp_instantiation
        name_node = next(
            (c for c in node.children
            if c.type in ("name_of_instance", "simple_identifier")),
            None
        )

        if not name_node:
            return None

        instance_name = name_node.text.decode()

        connections = {}

        port_list = next(
            (c for c in node.children
            if c.type == "list_of_port_connections"),
            None
        )

        if port_list:
            for conn in port_list.children:

                if conn.type != "named_port_connection":
                    continue

                port = next(
                    (c for c in conn.children
                    if c.type == "port_identifier"),
                    None
                )

                expr = next(
                    (c for c in conn.children
                    if "expression" in c.type),
                    None
                )

                if port and expr:
                    connections[port.text.decode()] = expr.text.decode()

        return Instance(
            name=instance_name,
            module_name=module_name,
            parameters=parameters.copy(),
            connections=connections,
            condition=condition
        )

    def _build_instance_from_udp_instance(self, node, module_name, parameters, condition=None):
        """Build instance from Verilog udp_instance node."""

        # Instance name - udp_instance uses name_of_instance -> instance_identifier -> simple_identifier
        name_of_instance_node = next(
            (c for c in node.children
            if c.type == "name_of_instance"),
            None
        )

        if not name_of_instance_node:
            return None

        instance_identifier_node = next(
            (c for c in name_of_instance_node.children
            if c.type == "instance_identifier"),
            None
        )

        if not instance_identifier_node:
            return None

        simple_identifier_node = next(
            (c for c in instance_identifier_node.children
            if c.type == "simple_identifier"),
            None
        )

        if not simple_identifier_node:
            return None

        instance_name = simple_identifier_node.text.decode()

        # Connections - udp_instance uses terminals (output_terminal, input_terminal)
        connections = {}

        # Find all terminals
        terminal_index = 0
        for child in node.children:
            if child.type == "output_terminal":
                # First terminal is output
                connections[f"port_{terminal_index}"] = self._extract_terminal_connection(child)
                terminal_index += 1
            elif child.type == "input_terminal":
                # Subsequent terminals are inputs
                connections[f"port_{terminal_index}"] = self._extract_terminal_connection(child)
                terminal_index += 1

        return Instance(
            name=instance_name,
            module_name=module_name,
            parameters=parameters.copy(),
            connections=connections,
            condition=condition
        )

    def _extract_terminal_connection(self, terminal_node):
        """Extract connection from udp terminal node."""
        # Look for simple_identifier in the terminal
        for child in terminal_node.children:
            if child.type == "simple_identifier":
                return child.text.decode()
            # Recursively search
            result = self._extract_terminal_connection(child)
            if result:
                return result
        return None

    def _extract_param_override(self, node):

        if not node:
            return {}

        parameters = {}

        # Descend vers list_of_parameter_assignments
        list_node = next(
            (c for c in node.children
            if c.type == "list_of_parameter_assignments"),
            None
        )

        if not list_node:
            return parameters

        for child in list_node.children:

            if child.type != "named_parameter_assignment":
                continue

            # Nom du parameter
            name_node = next(
                (c for c in child.children
                if c.type == "parameter_identifier"),
                None
            )

            # Valeur
            value_node = next(
                (c for c in child.children
                if "expression" in c.type),
                None
            )

            if name_node and value_node:
                parameters[name_node.text.decode()] = value_node.text.decode()

        return parameters
