import textwrap
from typing import Any, Mapping, Optional, Sequence

from ichor.cli.useful_functions.user_input import user_input_free_flow

# width of the horizontal rules drawn around a summary block
SUMMARY_WIDTH = 78
SUMMARY_RULE = "=" * SUMMARY_WIDTH


def print_summary(
    title: str,
    details: Optional[Mapping[str, Any]] = None,
    notes: Optional[Sequence[str]] = None,
):
    """Prints a block summarising what has just happened, so that the user is told what
    was done, with which settings, and where to look for the results, rather than only
    that something happened.

    :param title: A short headline, e.g. ``"METADYNAMICS JOB SUBMITTED"``.
    :param details: The settings/paths the action used, printed one per line as an
        aligned ``name : value`` table. Insertion order is kept, so the most important
        entries should come first.
    :param notes: Sentences printed underneath the table, e.g. what happens next or
        where the output ends up. Each one is wrapped to the width of the block.
    """

    print()
    print(SUMMARY_RULE)
    print(title)
    print(SUMMARY_RULE)

    if details:
        # pad the names so that the colons line up and the values can be read as a column
        name_width = max(len(name) for name in details)
        for name, value in details.items():
            print(f"  {name.ljust(name_width)} : {value}")

    if notes:
        for i, note in enumerate(notes):
            # a blank line before every note, so that they do not run into each other
            # or into the table above them
            if details or i:
                print()
            for line in textwrap.wrap(note, SUMMARY_WIDTH - 2) or [""]:
                print(f"  {line}")

    print(SUMMARY_RULE)
    # blank line so the "Press enter to continue" prompt is clearly separate from the
    # summary and is not mistaken for part of it
    print()


def print_summary_and_pause(
    title: str,
    details: Optional[Mapping[str, Any]] = None,
    notes: Optional[Sequence[str]] = None,
):
    """Prints a summary (see :func:`print_summary`) and then waits for the user to press
    enter, so that the summary is read before the menu is redrawn over it."""

    print_summary(title, details, notes)
    user_input_free_flow("Press enter to continue: ")
