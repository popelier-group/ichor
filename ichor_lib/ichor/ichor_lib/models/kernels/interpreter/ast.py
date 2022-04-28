from abc import ABC
from typing import Dict

import numpy as np

from ichor_lib.models.kernels.constant import ConstantKernel
from ichor_lib.models.kernels.interpreter.token_type import TokenType
from ichor_lib.models.kernels.kernel import Kernel


class ASTNode(ABC):
    def visit(self, global_state: Dict[str, Kernel]) -> Kernel:
        raise NotImplementedError(
            f"No visit method implemented for '{type(self).__name__}'"
        )


class BinOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

    def visit(self, global_state: Dict[str, Kernel]) -> Kernel:
        if self.op.type == TokenType.Plus:
            return self.left.visit(global_state) + self.right.visit(
                global_state
            )
        elif self.op.type == TokenType.Minus:
            raise NotImplementedError("Error: Not implemented minus kernel")
        elif self.op.type == TokenType.Mul:
            return self.left.visit(global_state) * self.right.visit(
                global_state
            )
        elif self.op.type == TokenType.Div:
            raise NotImplementedError("Error: Not implemented divide kernel")


class UnaryOp(ASTNode):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr

    def visit(self, global_state: Dict[str, Kernel]) -> Kernel:
        if self.op.type == TokenType.Plus:
            return self.expr.visit(global_state)
        elif self.op.type == TokenType.Minus:
            raise NotImplementedError("Error: Not implemented minus kernel")


class Var(ASTNode):
    def __init__(self, token):
        self.token = token
        self.value = token.value

    def visit(self, global_state: Dict[str, Kernel]) -> Kernel:
        val = global_state.get(self.value)
        if val is not None:
            return val
        else:
            raise NameError(f"{self.value} not defined")


ck = 0


class Num(ASTNode):
    def __init__(self, token):
        self.token = token
        self.value = token.value

    def visit(self, global_state: Dict[str, Kernel]) -> Kernel:
        global ck
        ck += 1
        return ConstantKernel(f"ck{ck}", self.value, np.array([0]))
