#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
File / Dir Scanner
"""

from pathlib import Path


def collect_files(inputs):
    """ Gather the files to scan """

    files = []

    for item in inputs:
        p = Path(item)

        if p.is_file():
            files.append(p)

        elif p.is_dir():
            for ext in ("*.v", "*.sv"):
                files.extend(p.rglob(ext))

    return files
