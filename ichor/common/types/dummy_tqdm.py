from typing import IO, Callable, Dict, Iterable


class dummy_tqdm:
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable.

    Used to replace tqdm when not writing to std.out, prevents ugly
    output files, should function identically while doing nothing

    Can be used as a substitution to make tqdm not a required dependency.
    """

    def __new__(cls, *args, **kwargs):
        # Create a new instance
        instance = object.__new__(cls)
        return instance

    def __init__(
        self,
        iterable: Iterable = None,
        desc: str = None,
        total: int = None,
        leave: bool = True,
        file: IO = None,
        ncols: int = None,
        mininterval: float = 0.1,
        maxinterval: float = 10.0,
        miniters: int = None,
        ascii: str = None,
        disable: bool = False,
        unit: str = "it",
        unit_scale: bool = False,
        dynamic_ncols: bool = False,
        smoothing: float = 0.3,
        bar_format: str = None,
        initial: int = 0,
        position: int = None,
        postfix: int = None,
        unit_divisor: int = 1000,
        write_bytes: IO = None,
        lock_args: str = None,
        gui: Callable = False,
        **kwargs,
    ):

        # Store the arguments
        self.iterable = iterable
        self.desc = desc or ""
        self.total = total
        self.leave = leave
        self.fp = file
        self.ncols = ncols
        self.mininterval = mininterval
        self.maxinterval = maxinterval
        self.miniters = miniters
        self.ascii = ascii
        self.disable = disable
        self.unit = unit
        self.unit_scale = unit_scale
        self.unit_divisor = unit_divisor
        self.lock_args = lock_args
        self.gui = gui
        self.dynamic_ncols = dynamic_ncols
        self.bar_format = bar_format
        self.postfix = None

        # Init the iterations counters
        self.last_print_n = initial
        self.n = initial

        self.pos = 0

    def __bool__(self):
        if self.total is not None:
            return self.total > 0
        return bool(self.iterable)

    def __nonzero__(self):
        return self.__bool__()

    def __len__(self):
        return 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def clear(self, nolock: bool = False):
        pass

    def refresh(self, nolock: bool = False, lock_args: str = None):
        pass

    def unpause(self):
        pass

    def reset(self, total: int = None):
        pass

    def set_description(self, desc: str = None, refresh: bool = True):
        pass

    def set_description_str(self, desc: str = None, refresh: bool = True):
        pass

    def set_postfix(
        self,
        ordered_dict: Dict[str, str] = None,
        refresh: bool = True,
        **kwargs,
    ):
        pass

    def set_postfix_str(self, s: str = "", refresh: bool = True):
        pass

    def moveto(self, n):
        pass

    def update(self):
        pass

    @property
    def format_dict(self):
        pass

    def display(self, msg: str = None, pos: int = None):
        pass

    def __hash__(self):
        return id(self)

    def __iter__(self):
        # Inlining instance variables as locals (speed optimisation)
        iterable = self.iterable
        yield from iterable
