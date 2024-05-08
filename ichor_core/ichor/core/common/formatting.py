from ichor.core.common.types.itypes import Scalar
from ichor.core.common.units import Temperature


def format_number_with_comma(n: Scalar) -> str:
    """
    10000 -> '10,000'

    Parameters
    ----------
    n

    Returns
    -------

    """
    return f"{n,}"


def temperature_formatter(
    temperature: float, unit: Temperature = Temperature.Kelvin
) -> str:
    """
    100 -> '100 K'

    Parameters
    ----------
    temperature
    unit

    Returns
    -------

    """
    return f"{temperature} {unit.name}"
