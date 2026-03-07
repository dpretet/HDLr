#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
HDLr main()
"""

from hdlr.core.cli import build_parser
from hdlr.core.scanner import collect_files
from hdlr.frontend import get_frontend

def is_verilog(path: str):
    return path.suffix == ".v"

def is_systemverilog(path: str):
    return path.suffix == ".sv"


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":

        files = collect_files(args.inputs)

        for f in files:

            if is_verilog(f):
                frontend = get_frontend("verilog")
            elif is_systemverilog(f):
                frontend = get_frontend("systemverilog")
            else:
                continue

            print(f"\n📄 {f}")

            modules = frontend.parse_file(f)

            for m in modules:
                print(f"📦 Module: {m.name}")

                for p in m.parameters:
                    print(f"   🔧 parameter {p.name} = {p.value}")

                for port in m.ports:
                    if port.width:
                        msb, lsb = port.width
                        width_str = f"[{msb}:{lsb}] "
                    else:
                        width_str = ""

                    print(f"   └── {port.direction} {width_str}{port.name}")

                for sig in m.signals:
                    if sig.width:
                        msb, lsb = sig.width
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



if __name__ == "__main__":
    main()
