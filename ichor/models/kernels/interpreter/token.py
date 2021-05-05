from ichor.models.kernels.interpreter.token_type import TokenType
from typing import Union, Optional


class Token:
    def __init__(self, ty: TokenType, value: Optional[Union[str, float]]):
        self.type = ty
        self.value = value

    def __str__(self) -> str:
        return "Token({type.name}, {value})".format(
            type=self.type, value=repr(self.value)
        )

    def __repr__(self) -> str:
        return self.__str__()
