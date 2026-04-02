#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
HDLr main module - Hardware Design Language parser and elaborator.

This module provides the main entry point for the HDLr tool, which can:
- Scan SystemVerilog/Verilog files to extract module definitions
- Elaborate designs by building module hierarchies with resolved parameters
"""

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from hdlr.core.argparser import build_parser
from hdlr.core.scanner import collect_files
from hdlr.frontend import get_frontend
from hdlr.ir.node import Design, HierarchyBuilder


def is_verilog(path: str) -> bool:
    """Check if a file path has a Verilog (.v) extension.

    Args:
        path: Path object to check

    Returns:
        True if the path has a .v extension, False otherwise
    """
    return path.suffix == ".v"


def is_systemverilog(path: str) -> bool:
    """Check if a file path has a SystemVerilog (.sv) extension.

    Args:
        path: Path object to check

    Returns:
        True if the path has a .sv extension, False otherwise
    """
    return path.suffix == ".sv"


def is_vhdl(path: str) -> bool:
    """Check if a file path has a VHDL (.vhd) extension.

    Args:
        path: Path object to check

    Returns:
        True if the path has a .vhd extension, False otherwise
    """
    return path.suffix == ".vhd"


def main():
    """Main entry point for HDLr tool.

    Parses command line arguments and dispatches to appropriate function.
    """
    console = Console()

    # Welcome banner
    console.print(
        Panel.fit(
            "[bold cyan]HDLr[/bold cyan] - Hardware Design Language Parser & Elaborator",
            border_style="bold blue",
            title="Welcome",
            subtitle="Verilog/SystemVerilog/VHDL Analysis Tool"
        )
    )

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        console.print("\n[bold green]🔍 Scanning modules...[/bold green]")
        for m in scan(args.inputs):
            pretty_print_module(m)

    if args.command == "elaborate":
        console.print(f"\n[bold green]🏗️  Elaborating design with top module: {args.top}[/bold green]")
        elaborate(args.inputs, args.top)


def scan(inputs):
    """Scan input files and extract module definitions.

    Args:
        inputs: List of file/directory paths to scan

    Returns:
        List of Module objects extracted from the input files
    """
    console = Console()
    files = collect_files(inputs)
    all_modules = []

    for f in files:
        if is_verilog(f):
            frontend = get_frontend("verilog")
        elif is_systemverilog(f):
            frontend = get_frontend("systemverilog")
        elif is_vhdl(f):
            frontend = get_frontend("vhdl")
        else:
            continue

        console.print(f"\n📄 Scanning [bold]{f}[/bold]")

        modules = frontend.parse_file(f)

        for m in modules:
            all_modules.append(m)

    return all_modules


def elaborate(inputs, top):
    """Elaborate a design hierarchy starting from a top module.

    Args:
        inputs: List of file/directory paths containing the design
        top: Name of the top module to elaborate
    """
    console = Console()
    design = Design()
    all_modules = scan(inputs)

    # Add all modules to the design
    for module in all_modules:
        design.add_module(module)

    builder = HierarchyBuilder(design)
    root = builder.build(top)

    console.print("\n[bold yellow]📊 Design Hierarchy:[/bold yellow]")
    print_tree(root, design)


def pretty_print_module(m):
    """Pretty print a module's structure including parameters, ports, signals, and instances.

    Args:
        m: Module object to print
    """
    console = Console()

    # Module header
    console.print(Panel.fit(
        f"[bold]📦 {m.name}[/bold]",
        border_style="green",
        title="Module"
    ))

    # Create a table for parameters
    if m.parameters:
        param_table = Table(title="🔧 Parameters", box=ROUNDED, border_style="blue")
        param_table.add_column("Name", style="cyan")
        param_table.add_column("Value", style="magenta")

        for p in m.parameters:
            param_table.add_row(p.name, p.value_str)

        console.print(param_table)

    # Ports section
    if m.ports:
        console.print("\n[bold]🔌 Ports:[/bold]")
        # Calculate max rendered width for alignment (including ANSI codes)
        rendered_widths = []
        for p in m.ports:
            if p.width_str:
                msb, lsb = p.width_str
                rendered = f"[{msb}:{lsb}]"
                rendered_widths.append(len(rendered))
            else:
                rendered_widths.append(0)

        max_width_len = max(rendered_widths) if rendered_widths else 0

        for port in m.ports:
            if port.width_str:
                msb, lsb = port.width_str
                width_str = f"[dim][{msb}:{lsb}][/dim]"
                # Pad to align with single-bit ports
                current_width = len(f"[{msb}:{lsb}]")
                width_str += " " * (max_width_len - current_width + 1)
            else:
                width_str = " " * (max_width_len + 1)

            if port.direction == "input":
                console.print(f"  {width_str}[green]{port.direction}[green]  {port.name}")
            else:
                console.print(f"  {width_str}[yellow]{port.direction}[yellow] {port.name}")

    # Signals section
    if m.signals:
        console.print("\n[bold]🔹 Signals:[/bold]")
        for sig in m.signals:
            if sig.width_str:
                msb, lsb = sig.width_str
                width_str = f"[dim][{msb}:{lsb}][/dim] "
            else:
                width_str = ""

            kind = sig.kind or ""
            console.print(f"  {width_str}{sig.name} [dim]({kind})[/dim]")

    # Instances section
    if m.instances:
        console.print("\n[bold]🔸 Instances:[/bold]")
        for inst in m.instances:
            console.print(f"  [bold]{inst.name}[/bold] : {inst.module_name}")

            if inst.parameters:
                console.print("    ⚙ Parameters:")
                for k, v in inst.parameters.items():
                    console.print(f"      • {k} = [magenta]{v}[/magenta]")

            if inst.connections:
                console.print("    🔌 Connections:")
                for port, expr in inst.connections.items():
                    console.print(f"      • .{port}([cyan]{expr}[/cyan])")

    console.print()


def _collect_all_width_specs(module, width_specs):
    """Collect all width specifications from the hierarchy for global alignment."""
    if module and module.ports:
        for port in module.ports:
            if port.width_str:
                msb, lsb = port.width_str
                spec = f"[{msb}:{lsb}]"
                width_specs.append(len(spec))

def print_tree(node, design, indent=0):
    """Print the design hierarchy tree.

    Args:
        node: Current node in the hierarchy
        design: Design object containing all modules
        indent: Current indentation level
    """
    console = Console()

    # Create a root tree structure
    tree = Tree("[bold]Top Level[/bold]", guide_style="bright_blue")

    _add_to_tree(tree, node, design)
    console.print(tree)
    return

def _add_to_tree(parent_tree, node, design):
    """Helper function to recursively add nodes to the tree."""

    # Grab the module
    module = design.modules.get(node.module_name)

    # Get the maximum IO declaration width
    all_width_specs = []
    _collect_all_width_specs(module, all_width_specs)
    global_max_width = max(all_width_specs) if all_width_specs else 0

    # Add a new node in the tree
    node_tree = parent_tree.add(f"[bold]{node.module_name}[/bold]")

    if node.instance_name:
        node_tree.label += f" [dim]({node.instance_name})[/dim]"

    if node.parameters:
        param_tree = node_tree.add("⚙ Parameters")
        for k, v in node.parameters.items():
            if isinstance(v, int):
                param_tree.add(f"[cyan]{k}[/cyan] = [magenta]{hex(v)}[/magenta]")
            else:
                param_tree.add(f"[cyan]{k}[/cyan] = [magenta]{v}[/magenta]")

    if module and module.ports:
        io_tree = node_tree.add("🔌 I/O Ports")

        for port in module.ports:
            if port.width_str:
                msb, lsb = port.width_str
                width_str = f"[dim][{msb}:{lsb}][/dim]"
                # Pad to align with single-bit ports using global max
                current_width = len(f"[{msb}:{lsb}]")
                width_str += " " * (global_max_width - current_width + 1)
            else:
                width_str = " " * (global_max_width + 1)  # +3 for brackets and space

            if port.direction == "input":
                io_tree.add(f"{width_str}[cyan]{port.direction}[/cyan]  {port.name}")
            else:
                io_tree.add(f"{width_str}[cyan]{port.direction}[/cyan] {port.name}")

    for child in node.children:
        _add_to_tree(node_tree, child, design)


if __name__ == "__main__":
    main()
