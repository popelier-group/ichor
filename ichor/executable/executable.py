from ichor.git import Repo
from ichor.git.util import get_git_credentials
from ichor.globals import GLOBALS
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Optional


class Executable(ABC):
    def __init__(self, git_repository: str, branch: str = "master", path: Optional[Path] = None):
        self.git_repository = git_repository
        self.branch = branch
        self.path = path or GLOBALS.FILE_STRUCTURE["programs"] / self.name

    @property
    def name(self):
        return self.git_repository.split('.git')[0].split('/')[-1]

    @property
    def _sanitised_url(self) -> str:
        return self.git_repository.lstrip("https://").lstrip("www.")

    def authenticated_token_url(self, token: str) -> str:
        return f"https://{token}:x-oauth-basic@{self._sanitised_url}"

    def authenticated_user_url(self, user: str, password: str) -> str:
        return f"https://{user}:{password}@{self._sanitised_url}"

    @property
    def authenticated_url(self):
        from ichor.globals import GLOBALS
        if GLOBALS.GIT_TOKEN:
            return self.authenticated_token_url(GLOBALS.GIT_TOKEN)
        elif not GLOBALS.GIT_USERNAME and GLOBALS.GIT_PASSWORD:
            GLOBALS.GIT_USERNAME, GLOBALS.GIT_PASSWORD = get_git_credentials()
        return self.authenticated_user_url(GLOBALS.GIT_USERNAME, GLOBALS.GIT_PASSWORD)

    @property
    def repo(self) -> Repo:
        return Repo(self.path)

    def update(self):
        if not self.path.exists():
            self.clone()
        for remote in self.repo.remotes:
            remote.fetch()

    def clone(self):
        if not self.path.exists():
            Repo.clone_from(self.authenticated_url, self.path)

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    @property
    def exepath(self):
        # if not self.up_to_date
        self.update()
        self.build()
        return

    @abstractmethod
    def build(self):
        pass
