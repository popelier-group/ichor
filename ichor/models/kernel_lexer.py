from abc import ABC

class TokenType(Enum):
    Number = 1
    Plus = 2
    Minus = 3
    Mul = 4
    Div = 5
    LParen = 6
    RParen = 7
    Id = 8
    Eof = -1

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return "Token({type.name}, {value})".format(
            type=self.type, value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Lexer(object):
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self):
        raise Exception("Invalid character")

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        if self.current_char == ".":
            result += self.current_char
            self.advance()
            while (
                self.current_char is not None and self.current_char.isdigit()
            ):
                result += self.current_char
                self.advance()

        if self.current_char.lower() == "e":
            result += self.current_char
            self.advance()
            if self.current_char in ["+", "-"]:
                result += self.current_char
                self.advance()
            while (
                self.current_char is not None and self.current_char.isdigit()
            ):
                result += self.current_char
                self.advance()

        return Token(TokenType.Number, float(result))

    def id(self):
        result = ""
        while self.current_char is not None and self.current_char.isalnum():
            result += self.current_char
            self.advance()

        return Token(TokenType.Id, result)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isalpha():
                return self.id()

            if self.current_char.isdigit():
                return self.number()

            if self.current_char == "+":
                self.advance()
                return Token(TokenType.Plus, "+")

            if self.current_char == "-":
                self.advance()
                return Token(TokenType.Minus, "-")

            if self.current_char == "*":
                self.advance()
                return Token(TokenType.Mul, "*")

            if self.current_char == "/":
                self.advance()
                return Token(TokenType.Div, "/")

            if self.current_char == "(":
                self.advance()
                return Token(TokenType.LParen, "(")

            if self.current_char == ")":
                self.advance()
                return Token(TokenType.RParen, ")")

            self.error()

        return Token(TokenType.Eof, None)


class AST(ABC):
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


class Parser:
    def __init__(self, text):
        self.lexer = Lexer(text)
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception("invalid syntax")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def variable(self):
        node = Var(self.current_token)
        self.eat(TokenType.Id)
        return node

    def factor(self):
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

    def term(self):
        node = self.factor()
        while self.current_token.type in (TokenType.Mul, TokenType.Div):
            token = self.current_token
            if token.type == TokenType.Mul:
                self.eat(TokenType.Mul)
            elif token.type == TokenType.Div:
                self.eat(TokenType.Div)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token.type in (TokenType.Plus, TokenType.Minus):
            token = self.current_token
            if token.type == TokenType.Plus:
                self.eat(TokenType.Plus)
            elif token.type == TokenType.Minus:
                self.eat(TokenType.Minus)
            node = BinOp(left=node, op=token, right=self.term())
        return node

    def parse(self):
        return self.expr()


class NodeVisitor:
    def visit(self, node):
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")


class KernelInterpreter(NodeVisitor):
    def __init__(self, text, global_scope):
        self.parser = Parser(text)
        self.global_scope = global_scope

    def visit_BinOp(self, node):
        if node.op.type == TokenType.Plus:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.Minus:
            # return self.visit(node.left) - self.visit(node.right)
            # TODO: Convert this to error
            print("Error: Not implemented minus kernel")
            quit()
        elif node.op.type == TokenType.Mul:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.Div:
            # return self.visit(node.left) / self.visit(node.right)
            # TODO: Convert this to error
            print("Error: Not implemented divide kernel")
            quit()

    def visit_UnaryOp(self, node):
        op = node.op.type
        if op == TokenType.Plust:
            return self.visit(node.expr)
        elif op == TokenType.Minus:
            # return -self.visit(node.expr)
            # TODO: Convert this to error
            print("Error: Not implemented minus kernel")
            quit()

    def visit_Num(self, node):
        return Constant(node.value)

    def visit_Var(self, node):
        var_name = node.value
        val = self.global_scope.get(var_name)
        if val is None:
            raise NameError(repr(var_name))
        else:
            return val

    def interpret(self):
        tree = self.parser.parse()
        return self.visit(tree)