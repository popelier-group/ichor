class Version:
    def __init__(self, rep=None):
        self.major = 0
        self.minor = 0
        self.patch = 0

        if rep:
            if isinstance(rep, str):
                self.parse_from_string(rep)
            elif isinstance(rep, Version):
                self.parse_from_version(rep)

    def parse_from_string(self, str_rep):
        split_rep = str_rep.split(".")
        if len(split_rep) > 0:
            self.major = int(split_rep[0])
        if len(split_rep) > 1:
            self.minor = int(split_rep[1])
        if len(split_rep) > 2:
            self.patch = int(split_rep[2])

    def parse_from_version(self, ver_rep):
        self.major = ver_rep.major
        self.minor = ver_rep.minor
        self.patch = ver_rep.patch

    def __gt__(self, other):
        if self.major > other.major:
            return True
        elif self.major < other.major:
            return False

        if self.minor > other.minor:
            return True
        elif self.minor < other.minor:
            return False

        if self.patch > other.patch:
            return True
        elif self.patch < other.patch:
            return False

        return False

    def __ge__(self, other):
        return self > other or self == other

    def __lt__(self, other):
        if self.major < other.major:
            return True
        elif self.major > other.major:
            return False

        if self.minor < other.minor:
            return True
        elif self.minor > other.minor:
            return False

        if self.patch < other.patch:
            return True
        elif self.patch > other.patch:
            return False

        return False

    def __le__(self, other):
        return self < other or self == other

    def __eq__(self, other):
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
        )

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self):
        return str(self)
