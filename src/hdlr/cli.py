#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
HDLr CLI
"""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """ App argument parser """

    parser = argparse.ArgumentParser(prog="hdlr")

    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan HDL files")
    scan.add_argument("inputs", nargs="+", help="Files or directories")

    return parser
