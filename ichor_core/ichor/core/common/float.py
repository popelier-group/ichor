def from_scientific_double(x: str) -> float:
    """
    e.g. "1.0D-2" -> 0.01
    """
    return float(x.upper().replace("D", "E"))
