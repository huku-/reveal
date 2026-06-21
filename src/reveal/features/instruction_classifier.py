# -*- coding: utf-8 -*-

from __future__ import annotations

from collections.abc import Iterator

from numpy import ndarray
from pyvex import IRSB

from relib.model import Function, Program
from relib.vex import lifter

import contextlib
import enum
import importlib
import json
import logging

import numpy

__author__ = "Chariton Karamitas <huku@census-labs.com>"

__all__ = ["InstructionClass", "InstructionClassifier"]


# fmt: off
@enum.unique
class InstructionClass(enum.IntFlag):
    """VEX instruction class."""

    OP_ADD = enum.auto()            # Addition
    OP_V_ADD = enum.auto()          # Vector addition
    OP_FP_ADD = enum.auto()         # Floating-point addition
    OP_FPV_ADD = enum.auto()        # Floating-point vector addition
    OP_SUB = enum.auto()            # Subtraction
    OP_V_SUB = enum.auto()          # Vector subtraction
    OP_FP_SUB = enum.auto()         # Floating-point subtraction
    OP_FPV_SUB = enum.auto()        # Floating-point vector subtraction
    OP_MUL = enum.auto()            # Multiplication
    OP_V_MUL = enum.auto()          # Vector multiplication
    OP_FP_MUL = enum.auto()         # Floating-point multiplication
    OP_FPV_MUL = enum.auto()        # Floating-point vector multiplication
    OP_DIV = enum.auto()            # Division
    OP_V_DIV = enum.auto()          # Vector division
    OP_FP_DIV = enum.auto()         # Floating-point division
    OP_FPV_DIV = enum.auto()        # Floating-point vector division
    OP_MOD = enum.auto()            # Modulo
    OP_AND = enum.auto()            # Logic AND
    OP_NOT = enum.auto()            # Logic NOT
    OP_OR = enum.auto()             # Logic OR
    OP_XOR = enum.auto()            # Logic XOR
    OP_SHL = enum.auto()            # Shift left
    OP_V_SHL = enum.auto()          # Vector shift left
    OP_SHR = enum.auto()            # Logical shift right
    OP_V_SHR = enum.auto()          # Vector logical shift right
    OP_SAR = enum.auto()            # Arithmetic shift right
    OP_V_SAR = enum.auto()          # Vector arithmetic shift right
    OP_BITCNT = enum.auto()         # Bit counting
    OP_V_BITCNT = enum.auto()       # Vector bit counting
    OP_V_ARITH = enum.auto()        # Various vector arithmetic operations
    OP_FP_ARITH = enum.auto()       # Various floating-point arithmetic operations
    OP_FPV_ARITH = enum.auto()      # Various floating-point vector arithmetic operations
    OP_CMP = enum.auto()            # Comparison
    OP_V_CMP = enum.auto()          # Vector comparison
    OP_FP_CMP = enum.auto()         # Floating-pointer comparison
    OP_FPV_CMP = enum.auto()        # Floating-point vector comparison
    OP_I2I_CONV = enum.auto()       # Integer to integer conversion
    OP_I2FP_CONV = enum.auto()      # Integer to floating-point conversion
    OP_FP2I_CONV = enum.auto()      # Floating-point to integer conversion
    OP_FP2FP_CONV = enum.auto()     # Floating-point to floating-point conversion
    OP_I2FPV_CONV = enum.auto()     # Integer to floating-point vector conversion
    OP_FP2IV_CONV = enum.auto()     # Floating-point to integer version conversion
    OP_FP2FPV_CONV = enum.auto()    # Floating-point to floating-point vector conversion
    OP_V_TRANS = enum.auto()        # Vector transformations
    OP_V_ACCESS = enum.auto()       # Vector element access
    OP_CRYPTO = enum.auto()         # Cryptographic primitives
    OP_CALL = enum.auto()           # Call to function
    OP_RET  = enum.auto()           # Return from function
    OP_JUMP = enum.auto()           # Jump to address
    OP_LOAD = enum.auto()           # Read from memory
    OP_STORE = enum.auto()          # Write to memory
    OP_GET = enum.auto()            # Read register value
    OP_PUT = enum.auto()            # Write register value
    OP_UNKNOWN = enum.auto()        # Unknown operation

    def __init__(self, value: int) -> None:
        super().__init__()
        self.ordinal = value.bit_length() - 1

    def unpack(self) -> Iterator[InstructionClass]:
        for i in range(self.bit_length()):
            if self & (1 << i):
                yield InstructionClass(1 << i)
# fmt: on


class InstructionClassifier(object):
    """Classify the instructions of a program function."""

    _VEX_INSN_CLS_MAP: dict[str, int] = {}

    def __init__(self, program: Program, function: Function) -> None:
        super().__init__()
        self._logger = logging.getLogger()
        self._program = program
        self._function = function
        if not InstructionClassifier._VEX_INSN_CLS_MAP:
            self._logger.debug("Loading VEX instruction classes")
            path = importlib.resources.files("reveal.data") / "vex_insn_cls.json"
            with open(path, "r", encoding="utf-8") as fp:
                InstructionClassifier._VEX_INSN_CLS_MAP = json.load(fp)

    def _process_irsb(self, irsb: IRSB, v: ndarray) -> None:
        for stmt in irsb.statements:
            if stmt.tag == "Ist_LoagG":
                v[InstructionClass.OP_LOAD.ordinal] += 1
            elif stmt.tag in ["Ist_Store", "Ist_StoreG"]:
                v[InstructionClass.OP_STORE.ordinal] += 1
            elif stmt.tag in ["Ist_Put", "Ist_PutI"]:
                v[InstructionClass.OP_PUT.ordinal] += 1
            for expr in stmt.expressions:
                if expr.tag in ["Iex_Unop", "Iex_Binop", "Iex_Triop", "Iex_Qop"]:
                    if expr.op not in InstructionClassifier._VEX_INSN_CLS_MAP:
                        self._logger.warning("VEX expression %s not found!", expr.op)
                    for cls in InstructionClass(
                        InstructionClassifier._VEX_INSN_CLS_MAP.get(
                            expr.op, InstructionClass.OP_UNKNOWN
                        )
                    ).unpack():
                        v[cls.ordinal] += 1
                elif expr.tag in ["Iex_Get", "Iex_GetI"]:
                    v[InstructionClass.OP_GET.ordinal] += 1
                elif expr.tag == "Iex_Load":
                    v[InstructionClass.OP_LOAD.ordinal] += 1

    def classify_instructions(self) -> ndarray:
        """Return instruction classfication vector.

        Returns:
            An array of integers where element *i* holds the number of instruction
            of class *i* in the target function.
        """
        v = numpy.zeros(len(InstructionClass), dtype=numpy.int32)
        vex_lifter = lifter.Lifter(self._program)
        cfg = self._function.get_cfg()
        for bb_ea in cfg:
            bb = self._function.get_bb_at_ea(bb_ea)
            start_ea = bb.start_ea
            end_ea = bb.end_ea
            size = end_ea - start_ea
            with contextlib.suppress(ValueError):
                for irsb in vex_lifter.lift(start_ea, size):
                    self._process_irsb(irsb, v)
                    if irsb.jumpkind == "Ijk_Call":
                        v[InstructionClass.OP_CALL.ordinal] += 1
                    elif irsb.jumpkind == "Ijk_Ret":
                        v[InstructionClass.OP_RET.ordinal] += 1
        return v
