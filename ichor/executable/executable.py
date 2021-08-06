from ichor.git import Repo


class Executable:
    def __init__(self, git_repository: str, branch: str = "master"):
        self.git_repository = git_repository
        self.branch = branch

    @property
    def name(self):
        return self.git_repository.split('.git')[0].split('/')[-1]

    def clone(self):
        from ichor.globals import GLOBALS
        Repo.clone_from(self.git_repository, GLOBALS.FILE_STRUCTURE["programs"] / self.name)
