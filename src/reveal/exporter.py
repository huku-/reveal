# -*- coding: utf-8 -*-
"""REveal export entry point."""

from pathlib import Path

from relib.model import Program

from reveal import util
from reveal.features import function_features

import logging
import pickle
import time

import numpy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["Exporter"]


class Exporter(object):

    def __init__(self, program: Program) -> None:
        super().__init__()
        self._logger = logging.getLogger()
        self._program = program

    def _export_fvs(self, path: str | Path) -> None:
        path = util.to_path(path)
        program = self._program
        num_funcs = program.get_num_funcs()

        with open(path / "fvs.pcl", "wb") as fp:
            for i, function in enumerate(program.get_funcs()):
                ea = function.ep_ea
                self._logger.info(
                    "Exporting function at %#x (%d/%d)", ea, i + 1, num_funcs
                )

                fv = numpy.concat(
                    [
                        function_features.get_function_type(program, function),
                        function_features.get_vertex_classification(program, function),
                        function_features.get_edge_classification(program, function),
                        function_features.get_in_degree(program, function),
                        function_features.get_out_degree(program, function),
                        function_features.get_cfg_signature(program, function),
                        function_features.get_idt_signature(program, function),
                        function_features.get_insn_bow(program, function),
                        function_features.get_string_bow(program, function),
                        function_features.get_markov_lumping(program, function),
                    ]
                )

                fv = [
                    ea,
                    function.name,
                ] + list(fv)

                pickle.dump(fv, fp)

    def export(self) -> None:
        self._logger.info("Starting export")
        start_time = int(time.time())

        path = self._program.get_db_path().with_suffix(".export")
        path.mkdir(exist_ok=True)
        self._logger.info("Exporting in directory %s", path)

        self._logger.info("Exporting FCG")
        fcg = self._program.get_fcg()
        with open(path / "fcg.pcl", "wb") as fp:
            pickle.dump(fcg, fp)

        self._logger.info("Exporting function features")
        self._export_fvs(path)

        end_time = int(time.time())
        self._logger.info("Export took %d sec.", end_time - start_time)
