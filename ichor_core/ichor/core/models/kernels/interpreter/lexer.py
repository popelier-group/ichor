from ichor.core.models.kernels.interpreter.token import Token
from ichor.core.models.kernels.interpreter.token_type import TokenType


class Lexer(object):
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]

    def error(self) -> None:
        raise Exception("Invalid character")

    def advance(self) -> None:
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Indicates end of input
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self) -> None:
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self) -> Token:
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        if self.current_char == ".":
            result += self.current_char
            self.advance()
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()

        if self.current_char.lower() == "e":
            result += self.current_char
            self.advance()
            if self.current_char in ["+", "-"]:
                result += self.current_char
                self.advance()
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()

        return Token(TokenType.Number, float(result))

    def id(self) -> Token:
        result = ""
        while self.current_char is not None and self.current_char.isalnum():
            result += self.current_char
            self.advance()

        return Token(TokenType.Id, result)

    def get_next_token(self) -> Token:
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
