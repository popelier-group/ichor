from ichor.hpc.machine import Machine


def get_machine_from_name(platform_name: str):

    m = Machine.local
    if "csf3." in platform_name:
        m = Machine.csf3
    elif "csf4." in platform_name:
        m = Machine.csf4
    elif "ffluxlab" in platform_name:
        m = Machine.ffluxlab

    # if ichor.hpc.global_variables.BATCH_SYSTEM.Host in os.environ.keys():
    #     host = os.environ[ichor.hpc.global_variables.BATCH_SYSTEM.Host]
    #     if host == "ffluxlab":
    #         m = Machine.ffluxlab

    return m


# def get_machine_from_file(machine_file: Path) -> Machine:
#     if machine_file.exists():
#         with open(machine_file, "r") as f:
#             _machine = f.read().strip()
#             if _machine:
#                 if _machine not in Machine.names:
#                     raise MachineNotFound(f"Unknown machine '{_machine}, cannot use.")
#                 else:
#                     return Machine.from_name(_machine)


def init_machine(machine_name: str) -> Machine:

    machine = get_machine_from_name(machine_name)

    # if machine is Machine.local and machine_file.exists():
    #     machine = get_machine_from_file(machine_file)

    # # if machine has been successfully identified, write to ichor.hpc.global_variables.FILE_STRUCTURE['machine']
    # if machine is not Machine.local and (
    #     not machine_file.exists()
    #     or machine_file.exists()
    #     and get_machine_from_file(machine_file) != machine
    # ):
    #     mkdir(machine_file.parent)
    #     machine_filepart = Path(str(machine_file) + f".{get_uid()}.filepart")
    #     with open(machine_filepart, "w") as f:
    #         f.write(f"{machine.name}")
    #     move(machine_filepart, machine_file)

    return machine
