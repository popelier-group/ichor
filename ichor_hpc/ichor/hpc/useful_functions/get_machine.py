from typing import Optional


def init_machine(platform_name: str, ichor_config: dict) -> Optional[str]:
    """Loops through the keys of the config file, which contain the
    machine abbreviation/name which is also found in the platform name

    :param platform_name: The platform name given by `platform.node()`
    :param ichor_config: A dictionary of the ichor config file, containing names of machines as keys
    :return: The key of the config file whose name appears in the platform name,
        or None if the config is empty or names no machine that matches. Callers
        warn when this is None, as without a machine ichor does not know which
        modules to load or where any of the programs are.
    """

    if ichor_config:

        for k in ichor_config.keys():

            if k in platform_name:

                return k
