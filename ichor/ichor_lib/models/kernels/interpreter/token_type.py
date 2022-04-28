from enum import Enum


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
