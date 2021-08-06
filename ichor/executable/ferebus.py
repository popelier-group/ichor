from ichor.executable.executable import Executable

class Ferebus(Executable):
    def __init__(self):
        Executable.__init__(self, git_repository="https://github.com/popelier-group/FEREBUS")
