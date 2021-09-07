import sys


"""
IMPORTANT

This code uses a hack and comes with the following warning:
The method trace() is called when a new local scope is entered, i.e. right when the code in 
your with block begins. When an exception is raised here it gets caught by exit(). That's how 
this hack works. I should add that this is very much a hack and should not be relied upon. 
The magical sys.settrace() is not actually a part of the language definition, it just happens 
to be in CPython. Also, debuggers rely on sys.settrace() to do their job, so using it yourself 
interferes with that. There are many reasons why you shouldn't use this code.

The intention of the code is to only execute the code within the with block if running in AutoRun
"""


class NotInAutoRun(Exception):
    pass


class AutoRunOnly:
    def __init__(self):
        from ichor.arguments import Arguments
        self.auto_run = Arguments.auto_run

    def __enter__(self):
        if not self.auto_run:
            sys.settrace(lambda *args, **keys: None)
            frame = sys._getframe(1)
            frame.f_trace = self.trace

    def trace(self, frame, event, arg):
        raise NotInAutoRun()

    def __exit__(self, type, value, traceback):
        if type is None:
            return  # No exception
        if issubclass(type, NotInAutoRun):
            return True  # Suppress special SkipWithBlock exception