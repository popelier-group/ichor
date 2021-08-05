import os

from .common.functools import get_functions_to_run, run_function


class Problem:
    def __init__(self, name="", problem="", solution=""):
        self.name = name
        self.problem = problem
        self.solution = solution

    def __str__(self):
        return (
            f"Problem:     {self.name}\n"
            f"Description: {self.problem}\n"
            f"Solution:    {self.solution}"
        )

    def __repr__(self):
        return str(self)


class ProblemFinder:
    unknown_settings = []
    protected_settings = []
    incorrect_settings = {}

    _no_reference_file = False

    def __init__(self):
        self.problems = []

    @run_function(1)
    def check_alf(self):
        from .globals import GLOBALS

        if len(GLOBALS.ALF) < 1:
            self.add(
                Problem(
                    name="ALF",
                    problem="ALF not set due to error in calculation",
                    solution="Set 'ALF_REFERENCE_FILE' or manually set 'ALF' in config file",
                )
            )

    @run_function(1.1)
    def check_atoms(self):
        from .globals import GLOBALS

        if not GLOBALS.ATOMS:
            self.add(
                Problem(
                    name="ATOMS",
                    problem="ATOMS not set due to missing reference file",
                    solution="Set 'ALF_REFERENCE_FILE' in config file",
                )
            )

    # @run_function(2)
    def check_directories(self):
        from .globals import GLOBALS

        dirs_to_check = ["training_set", "sample_pool"]

        for dir_name in dirs_to_check:
            dir_path = GLOBALS.FILE_STRUCTURE[dir_name]
            if not os.path.isdir(dir_path):
                self.add(
                    Problem(
                        name="Directory Not Found",
                        problem=f"Could not find: {dir_path}",
                        solution="Setup directory structure or create manually",
                    )
                )

    @run_function(3)
    def check_system(self):
        from .globals import GLOBALS

        if GLOBALS.SYSTEM_NAME == "SYSTEM":
            self.add(
                Problem(
                    name="SYSTEM_NAME",
                    problem="SYSTEM_NAME not been set, defaulted to SYSTEM",
                    solution="Set 'SYSTEM_NAME' in config file",
                )
            )

    @run_function(4)
    def check_settings(self):
        for setting in ProblemFinder.unknown_settings:
            self.add(
                Problem(
                    name=f"Unknown setting found in config",
                    problem=f"Unknown setting: {setting}",
                    solution="See documentation or check [o]ptions [settings] for full list of settings",
                )
            )

        for setting in ProblemFinder.protected_settings:
            self.add(
                Problem(
                    name=f"Tried to modify protected setting in config",
                    problem=f"Protected setting: {setting}",
                    solution="This setting cannot be modified in config, remove from config",
                )
            )

        for setting, error in ProblemFinder.incorrect_settings.items():
            self.add(
                Problem(
                    name=f"Setting variable ({setting}) to incorrect value",
                    problem=f"{error}",
                    solution="Consult documentation to check allowed values",
                )
            )

    def add(self, problem):
        self.problems.append(problem)

    def find(self):
        from .globals import GLOBALS

        if not GLOBALS.DISABLE_PROBLEMS:
            problems_to_find = UsefulTools.get_functions_to_run(self)
            for find_problem in problems_to_find:
                find_problem()

    def __getitem__(self, i):
        return self.problems[i]

    def __len__(self):
        return len(self.problems)

    def __str__(self):
        return "\n\n".join(str(problem) for problem in self.problems)

    def __repr__(self):
        return str(self)
