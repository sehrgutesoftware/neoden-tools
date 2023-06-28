#!/usr/bin/env python

"""
Convert a KiCad position file (CSV) to NeoDen4 CSV format
"""

import argparse
import csv
import re
from io import TextIOWrapper
from typing import Callable

PACKAGE_REGEXES: list[re.Pattern] = [
    re.compile(r'\w+_(?P<value>\d+)_\d+Metric'),
    re.compile(r'(?P<value>SOIC\-8).*'),
    re.compile(r'(?P<value>Fiducial)_.*'),
    re.compile(r'R_Array_Convex_(?P<value>\d+x\d+)'),
]


def format_package(input: str) -> str:
    for expression in PACKAGE_REGEXES:
        match = expression.match(input)
        if match is not None:
            return match.group("value")
    return input


def format_value(input: str) -> str:
    return input.replace("µ", "u").replace("Ω", "")


def format_position(input: str) -> str:
    position = float(input)
    return '{:.2f}mm'.format(position)


def map_layer(input: str) -> str:
    if input == "top":
        return "T"
    if input == "bottom":
        return "B"
    return ""


def format_rotation(input: str) -> str:
    angle = float(input)
    if angle > 180:
        angle = -1 * (360-angle)
    return '{:.1f}'.format(angle)


"""
This dictionary maps NeoDen CSV fields to their corresponding
KiCad fields along with an optional transformation function.
"""
FIELDS_MAP: dict[str, tuple[str, Callable[[str], str] | None]] = {
    "Designator": ("Ref", None),
    "Footprint": ("Package", format_package),
    "Mid X": ("PosX", format_position),
    "Mid Y": ("PosY", format_position),
    "Layer": ("Side", map_layer),
    "Rotation": ("Rot", format_rotation),
    "Comment": ("Val", format_value),
}


def transform_row(input: dict[str, str]) -> dict[str, str]:
    output: dict[str, str] = {}

    for neoden_field, (kicad_field, transform_function) in FIELDS_MAP.items():
        value: str = input[kicad_field]
        if transform_function is not None:
            value = transform_function(value)
        output[neoden_field] = value

    return output


def main(input: TextIOWrapper, output: TextIOWrapper) -> int:
    neoden_fields = FIELDS_MAP.keys()
    kicad_fields = [i[0] for i in FIELDS_MAP.values()]

    reader = csv.DictReader(input)

    writer = csv.DictWriter(output, neoden_fields)
    writer.writeheader()
    # "empty" line with just commas
    writer.writerow({key: "" for key in neoden_fields})

    for row in reader:
        writer.writerow(transform_row(row))

    input.close()
    output.close()

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=argparse.FileType(
        "r"), help="Input file (KiCad CSV position file)")
    parser.add_argument("output", type=argparse.FileType(
        "w"), help="Output filename")
    args = parser.parse_args()
    exit(main(args.input, args.output))
