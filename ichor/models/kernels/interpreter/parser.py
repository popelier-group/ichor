from ichor.models.kernels.interpreter.ast import (
    ASTNode,
    BinOp,
    Num,
    UnaryOp,
    Var,
)
from ichor.models.kernels.interpreter.lexer import Lexer
from ichor.models.kernels.interpreter.token_type import TokenType


class Parser:
    def __init__(self, text: str):
        self.lexer = Lexer(text)
        self.current_token = self.lexer.get_next_token()

    def error(self) -> None:
        raise Exception("invalid syntax")

    def eat(self, token_type: TokenType) -> None:
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def variable(self) -> Var:
        node = Var(self.current_token)
        self.eat(TokenType.Id)
        return node

    def factor(self) -> ASTNode:
        token = self.current_token
        if token.type == TokenType.Plus:
            self.eat(TokenType.Plus)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.Minus:
            self.eat(TokenType.Minus)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.Number:
            self.eat(TokenType.Number)
            return Num(token)
        elif token.type == TokenType.LParen:
            self.eat(TokenType.LParen)
            node = self.expr()
            self.eat(TokenType.RParen)
            return node
        else:
            node = self.variable()
            return node

    def term(self) -> ASTNode:
        node = self.factor()
        while self.current_token.type in (TokenType.Mul, TokenType.Div):
            token = self.current_token
            if token.type == TokenType.Mul:
                self.eat(TokenType.Mul)
            elif token.type == TokenType.Div:
                self.eat(TokenType.Div)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def expr(self) -> ASTNode:
        node = self.term()
        while self.current_token.type in (TokenType.Plus, TokenType.Minus):
            token = self.current_token
            if token.type == TokenType.Plus:
                self.eat(TokenType.Plus)
            elif token.type == TokenType.Minus:
                self.eat(TokenType.Minus)
            node = BinOp(left=node, op=token, right=self.term())
        return node

    def parse(self) -> ASTNode:
        return self.expr()
