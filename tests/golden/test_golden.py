#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

#!/usr/bin/env python3
# coding: utf-8

import json
from pathlib import Path

import pytest

from hdlr.frontend import get_frontend


BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "inputs"
REF_DIR = BASE_DIR / "refs"

EXTENSION_MAP = {
    ".v": "verilog",
    ".sv": "systemverilog",
}


def normalize(data):
    return json.loads(json.dumps(data, sort_keys=True))


def list_test_cases():
    # on garde la logique existante
    return [p.stem for p in INPUT_DIR.glob("*.sv")] + \
           [p.stem for p in INPUT_DIR.glob("*.v")]


@pytest.mark.parametrize("name", list_test_cases())
def test_golden(name):
    # détecte automatiquement .sv ou .v
    input_file = None
    for ext in (".sv", ".v"):
        candidate = INPUT_DIR / f"{name}{ext}"
        if candidate.exists():
            input_file = candidate
            break

    assert input_file is not None, f"Missing input file: {name}"

    ref_file = REF_DIR / f"{name}.json"

    assert ref_file.exists(), (
        f"Missing golden reference for {name}."
    )

    # ✅ même logique que le CLI
    lang = EXTENSION_MAP.get(input_file.suffix)
    assert lang, f"Unsupported extension: {input_file.suffix}"

    frontend = get_frontend(lang)

    # le CLI parse des fichiers, pas des strings
    ir = frontend.parse_file(input_file)

    result = normalize({
        m.name: m.to_dict()
        for m in ir
    })
    expected = json.loads(ref_file.read_text())

    print("Results:")
    print(result)
    print("Expected:")
    print(expected)

    assert result == expected
