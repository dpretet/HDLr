#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Command line argument parser for HDLr.

This module defines the CLI interface for the HDLr tool,
including subcommands for scanning and elaborating designs.
"""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for HDLr CLI.

    Returns:
        Configured ArgumentParser object
    """
    parser = argparse.ArgumentParser(
        prog="hdlr",
        description="HDLr - SystemVerilog/Verilog design parser and elaborator"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # Scan command
    scan = sub.add_parser("scan", help="Scan HDL files and display module structure")
    scan.add_argument("inputs", nargs="+", help="Files or directories to scan")

    # Elaborate command
    elaborate = sub.add_parser("elaborate", help="Elaborate design hierarchy")
    elaborate.add_argument("inputs", nargs="+", help="Files or directories to scan")
    elaborate.add_argument("--top", required=True, help="Top module name for hierarchy")

    return parser
