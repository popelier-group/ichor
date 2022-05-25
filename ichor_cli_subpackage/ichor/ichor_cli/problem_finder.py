import os

from ichor.ichor_lib.common.functools import get_functions_to_run, run_function, run_once


class Problem:
    def __init__(self, name="", problem="", solution="", messages=None):
        self.name = name
        self.problem = problem
        self.solution = solution
        self.messages = messages or []

    def __str__(self):
        msg = ""
        msg += f"Problem:     {self.name}\n"
        msg += f"Description: {self.problem}\n"
        msg += f"Solution:    {self.solution}"
        for message in self.messages:
            msg += f"\n             {message}"
        return msg

    def __repr__(self):
        return str(self)


class ProblemFinder(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unknown_settings = []
        self.protected_settings = []
        self.incorrect_settings = {}

        self._no_reference_file = False

    # @run_function(1)
    def check_alf(self):
        from ichor.ichor_hpc import GLOBALS

        if len(GLOBALS.ALF) < 1:
            self.append(
                Problem(
                    name="ALF",
                    problem="ALF not set due to error in calculation",
                    solution="Set 'ALF_REFERENCE_FILE' or manually set 'ALF' in config file",
                )
            )

    # @run_function(1.1)
    def check_atoms(self):
        from ichor.ichor_hpc import GLOBALS

        if not GLOBALS.ATOMS:
            self.append(
                Problem(
                    name="ATOMS",
                    problem="ATOMS not set due to missing reference file",
                    solution="Set 'ALF_REFERENCE_FILE' in config file",
                )
            )

    # @run_function(2)
    def check_directories(self):
        from ichor.ichor_hpc import FILE_STRUCTURE

        dirs_to_check = ["training_set", "sample_pool"]

        for dir_name in dirs_to_check:
            dir_path = FILE_STRUCTURE[dir_name]
            if not os.path.isdir(dir_path):
                self.append(
                    Problem(
                        name="Directory Not Found",
                        problem=f"Could not find: {dir_path}",
                        solution="Setup directory structure or create manually",
                    )
                )

    @run_function(3)
    def check_system(self):
        from ichor.ichor_hpc import GLOBALS

        if GLOBALS.SYSTEM_NAME == "SYSTEM":
            self.append(
                Problem(
                    name="SYSTEM_NAME",
                    problem="SYSTEM_NAME not been set, defaulted to SYSTEM",
                    solution="Set 'SYSTEM_NAME' in config file",
                )
            )

    @run_function(4)
    def check_settings(self):
        import difflib

        from ichor.ichor_hpc import GLOBALS

        for setting in self.unknown_settings:
            close_matches = difflib.get_close_matches(
                setting, GLOBALS.global_variables, cutoff=0.5
            )
            messages = []
            if len(close_matches) > 0:
                messages += [f"Possible Matches: {close_matches}"]
            self.append(
                Problem(
                    name=f"Unknown setting found in config",
                    problem=f"Unknown setting: {setting}",
                    solution=f"See documentation or check [o]ptions [settings] for full list of settings",
                    messages=messages,
                )
            )

        for setting in self.protected_settings:
            self.append(
                Problem(
                    name=f"Tried to modify protected setting in config",
                    problem=f"Protected setting: {setting}",
                    solution="This setting cannot be modified in config, remove from config",
                )
            )

        for setting, error in self.incorrect_settings.items():
            self.append(
                Problem(
                    name=f"Setting variable ({setting}) to incorrect value",
                    problem=f"{error}",
                    solution="Consult documentation to check allowed values",
                )
            )

    @run_once
    def find(self):
        from ichor.ichor_hpc import GLOBALS

        if not GLOBALS.DISABLE_PROBLEMS:
            problems_to_find = get_functions_to_run(self)
            for find_problem in problems_to_find:
                find_problem()

    def __str__(self):
        return "\n\n".join(str(problem) for problem in self)

    def __repr__(self):
        return str(self)


PROBLEM_FINDER = ProblemFinder()
