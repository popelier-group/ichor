from ichor.core.itypes import Scalar
from ichor.core.units import Temperature


def format_number_with_comma(n: Scalar) -> str:
    return f"{n,}"


def temperature_formatter(
    temperature: float, unit: Temperature = Temperature.Kelvin
) -> str:
    return f"{temperature} {unit.name}"
