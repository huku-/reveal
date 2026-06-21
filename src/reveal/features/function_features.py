# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Features used for representing program functions."""

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["FunctionFeatureVector"]


from reveal.features.features import Feature, FeatureVector

from relib.model import Program, Function

from numpy import ndarray

import contextlib

import numpy

from reveal.algorithms import (
    dominators,
    edge_classifier,
    signatures,
    vertex_classifier,
)

from reveal.features import cfg_markov_lumping, instruction_classifier, util

FUNCTION_TYPE_HIDDEN = 0
FUNCTION_TYPE_IMPORT = 1
FUNCTION_TYPE_EXPORT = 2


def get_function_type(program: Program, function: Function) -> ndarray:
    if function.ep_ea in program.get_import_eas():
        value = FUNCTION_TYPE_IMPORT
    elif function.ep_ea in program.get_export_eas():
        value = FUNCTION_TYPE_EXPORT
    else:
        value = FUNCTION_TYPE_HIDDEN
    return numpy.array([value], dtype=numpy.int8)


def get_vertex_classification(program: Program, function: Function) -> ndarray:
    return numpy.array(
        vertex_classifier.classify_vertices(function.get_cfg()), dtype=numpy.int32
    )


def get_edge_classification(program: Program, function: Function) -> ndarray:
    return numpy.array(
        edge_classifier.classify_edges(function.get_cfg()), dtype=numpy.int32
    )


def get_in_degree(program: Program, function: Function) -> ndarray:
    return numpy.array(
        [
            len(program.get_func_xrefs_to_ea(function.ep_ea)),
            len(program.get_data_xrefs_to_ea(function.ep_ea)),
        ],
        dtype=numpy.int32,
    )


def get_out_degree(program: Program, function: Function) -> ndarray:
    return numpy.array(
        [program.get_fcg().out_degree(function.ep_ea)], dtype=numpy.int32
    )


def get_cfg_signature(program: Program, function: Function) -> ndarray:
    cfg = function.get_cfg()
    return numpy.array([signatures.get_string_signature(cfg)], dtype=object)


def get_idt_signature(program: Program, function: Function) -> ndarray:
    cfg = function.get_cfg()
    idt = dominators.get_immediate_dominator_tree(cfg)
    return numpy.array([signatures.get_string_signature(idt)], dtype=object)


def get_insn_bow(program: Program, function: Function) -> ndarray:
    return instruction_classifier.InstructionClassifier(
        program, function
    ).classify_instructions()


def get_string_bow(program: Program, function: Function) -> ndarray:

    def _get_strings_at_ea(program: Program, ea: int) -> str:
        s = ""
        for ref_ea in program.get_data_xrefs_from_ea(ea):
            item_ea = program.get_item_at_ea(ref_ea)
            item_size = program.get_item_size_at_ea(item_ea)
            size = item_size - (ref_ea - item_ea)
            with contextlib.suppress(ValueError, UnicodeDecodeError):
                ref_s = program.read_from_ea(ref_ea, size).decode("utf-8")
                if ref_s.isascii():
                    s += ref_s
        return s

    bow = numpy.zeros(shape=(256,), dtype=numpy.int32)
    for ea in function.get_cfg():
        for insn in function.get_bb_at_ea(ea).get_insns():
            for i in _get_strings_at_ea(program, insn.ea):
                bow[ord(i)] += 1
    return bow


def get_markov_lumping(program: Program, function: Function) -> ndarray:
    return cfg_markov_lumping.CFGMarkovLumper(program, function).lump_cfg()


FunctionFeatureVector = FeatureVector(
    [
        Feature(
            numpy.int32, 1, util.point_distance, util.pairwise_sum, "function_type"
        ),
        Feature(
            numpy.int32,
            7,
            util.euclidean_distance,
            util.pairwise_sum,
            "vertex_classification",
        ),
        Feature(
            numpy.int32,
            4,
            util.euclidean_distance,
            util.pairwise_sum,
            "edge_classification",
        ),
        Feature(
            numpy.int32, 2, util.euclidean_distance, util.pairwise_sum, "in_degree"
        ),
        Feature(numpy.int32, 1, util.point_distance, util.pairwise_sum, "out_degree"),
        Feature(object, 1, util.hamming_distance, util.no_sum, "cfg_signature"),
        Feature(object, 1, util.hamming_distance, util.no_sum, "idt_signature"),
        Feature(
            numpy.int32,
            47 + 7,
            util.euclidean_distance,
            util.pairwise_sum,
            "insn_bow",
        ),
        Feature(
            numpy.int32,
            256,
            util.euclidean_distance,
            util.pairwise_sum,
            "string_bow",
        ),
        Feature(
            numpy.float64,
            64,
            util.euclidean_distance,
            util.pairwise_sum,
            "markov_lumping",
        ),
    ]
)
