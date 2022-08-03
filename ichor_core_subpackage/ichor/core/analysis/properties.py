ENERGY_PROPERTIES = {"iqa", "dispersion"}


def is_energy_property(prop: str) -> bool:
    if '+' in prop:
        return all(is_energy_property(p) for p in prop.split('+'))
    return prop in ENERGY_PROPERTIES
