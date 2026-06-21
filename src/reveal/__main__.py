# -*- coding: utf-8 -*-
"""REveal console entry point."""

import argparse
import importlib.resources
import logging.config
import os
import pathlib
import sys

from reveal import differ


__author__ = "Chariton Karamitas <huku@census-labs.com>"


def main(argv: list[str] | None = None) -> int:

    argv = argv or sys.argv

    parser = argparse.ArgumentParser(
        prog="REveal", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--no-match-inexact",
        "-x",
        action="store_true",
        help="disable inexact matching",
    )
    parser.add_argument(
        "--no-match-imports", "-i", action="store_true", help="disable import matching"
    )
    parser.add_argument(
        "--match-exports", "-e", action="store_true", help="enable export matching"
    )
    parser.add_argument(
        "--match-names", "-n", action="store_true", help="enable name matching"
    )
    parser.add_argument(
        "--match-hierarchical",
        "-l",
        type=str,
        choices=["louvain", "modular_decomposition", "recover-apsnse", "recover-apspse", "recover-agglnse", "recover-agglpse"],
        default=None,
        help="algorithm to use for hierarchical matching",
    )
    parser.add_argument(
        "-m",
        "--time",
        dest="write_time",
        action="store_true",
        help="write timing information",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="enable debugging output"
    )
    parser.add_argument(
        "dataset1_path",
        metavar="DATASET1_PATH",
        type=pathlib.Path,
        help="path to exported dataset #1",
    )
    parser.add_argument(
        "dataset2_path",
        metavar="DATASET2_PATH",
        type=pathlib.Path,
        help="path to exported dataset #2",
    )
    parser.add_argument(
        "results_path",
        metavar="RESULTS_PATH",
        type=pathlib.Path,
        help="path to store results to",
    )
    args = parser.parse_args(argv[1:])

    if args.debug:
        path = importlib.resources.files("reveal.data") / "logging-debug.ini"
    else:
        path = importlib.resources.files("reveal.data") / "logging.ini"

    logging.config.fileConfig(str(path))

    differ.Differ(
        args.dataset1_path,
        args.dataset2_path,
        args.results_path,
        match_inexact=not args.no_match_inexact,
        match_imports=not args.no_match_imports,
        match_exports=args.match_exports,
        match_names=args.match_names,
        match_hierarchical=args.match_hierarchical,
        write_time=args.write_time,
    ).diff()

    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
