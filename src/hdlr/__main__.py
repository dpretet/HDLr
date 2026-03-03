#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
HDLr main()
"""

from hdlr.cli import build_parser
from hdlr.core.scanner import collect_files
from hdlr.frontend.verilog import parse_verilog


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        files = collect_files(args.inputs)

        for f in files:
            print(f"\n📄 {f}")
            modules = parse_verilog(f)
            for m in modules:
                print(f"📦 Module: {m.name}")
                for p in m.ports:
                    print(f"   └── {p.direction} {p.name}")

if __name__ == "__main__":
    main()
