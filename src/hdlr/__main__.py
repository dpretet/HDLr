#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
HDLr main()
"""

from hdlr.core.argparser import build_parser
from hdlr.core.scanner import collect_files
from hdlr.frontend import get_frontend
from hdlr.core.design import Design
from hdlr.ir.node import HierarchyBuilder

def is_verilog(path: str):
    return path.suffix == ".v"

def is_systemverilog(path: str):
    return path.suffix == ".sv"


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        scan(args.inputs)

    if args.command == "elaborate":
        elaborate(args.inputs, args.top)


def scan(inputs):

    files = collect_files(inputs)
    all_modules = []

    for f in files:

        if is_verilog(f):
            frontend = get_frontend("verilog")
        elif is_systemverilog(f):
            frontend = get_frontend("systemverilog")
        else:
            continue

        print(f"\n📄 Scanning {f}")

        modules = frontend.parse_file(f)

        for m in modules:
            all_modules.append(m)
            pretty_print_module(m)

    return all_modules

def elaborate(inputs, top):

    design = Design()
    all_modules = scan(inputs)
    
    # Add all modules to the design
    for module in all_modules:
        design.add_module(module)
    
    builder = HierarchyBuilder(design)
    root = builder.build(top)
    print_tree(root)


def pretty_print_module(m):

    print(f"📦 Module: {m.name}")

    for p in m.parameters:
        print(f"   🔧 parameter {p.name} = {p.value_str}")

    for port in m.ports:
        if port.width_str:
            msb, lsb = port.width_str
            width_str = f"[{msb}:{lsb}] "
        else:
            width_str = ""

        print(f"   └── {port.direction} {width_str}{port.name}")

    for sig in m.signals:
        if sig.width_str:
            msb, lsb = sig.width_str
            width_str = f"[{msb}:{lsb}] "
        else:
            width_str = ""

        kind = sig.kind or ""
        print(f"   🔹 {kind} {width_str}{sig.name}")

    # -----------------
    # Instances
    # -----------------
    for inst in m.instances:
        print(f"   🔸 Instance {inst.name} : {inst.module_name}")

        if inst.parameters:
            print("      ⚙ Parameters:")
            for k, v in inst.parameters.items():
                print(f"         - {k} = {v}")

        if inst.connections:
            print("      🔌 Connections:")
            for port, expr in inst.connections.items():
                print(f"         - .{port}({expr})")

def print_tree(node, indent=0):
    pad = "  " * indent
    inst = f" ({node.instance_name})" if node.instance_name else ""
    print(f"{pad}- {node.module_name}{inst}")

    for k, v in node.parameters.items():
        print(f"{pad}    ⚙ {k} = {v}")

    for child in node.children:
        print_tree(child, indent + 1)


if __name__ == "__main__":
    main()
