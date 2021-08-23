# Copyright 2015 Open Source Robotics Foundation, Inc.
# Copyright 2013 Willow Garage, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from pathlib import Path

from ichor.cmake.parser import list_utils
from ichor.common.types import Version


class QuotedString:
    def __init__(self, contents, comments):
        self.contents = contents
        self.comments = comments


class Arg:
    def __init__(self, contents, comments=None):
        self.contents = contents
        self.comments = comments


class Command:
    def __init__(self, name, body, comment=None):
        self.name = name
        self.body = body
        self.comment = comment


class BlankLine:
    def __init__(self):
        pass


class Comment(str):
    def __repr__(self):
        return "Comment(" + str(self) + ")"


BEGIN_BLOCK_COMMANDS = [
    "function",
    "macro",
    "if",
    "else",
    "elseif",
    "foreach",
    "while",
]
END_BLOCK_COMMANDS = [
    "endfunction",
    "endmacro",
    "endif",
    "else",
    "elseif",
    "endforeach",
    "endwhile",
]


class CMakeParseError(Exception):
    pass


def parse_cmake_lists(path: Path):
    with open(path, "r") as f:
        file_contents = f.read()
    nums_toks = tokenize(file_contents)
    nums_items = list(parse_file(nums_toks))
    return attach_comments_to_commands(nums_items)


# def compose_lines(tree, formatting_opts):
#     """
#     Yields pretty-printed lines of a CMakeLists file.
#     """
#     tab = formatting_opts.indent
#     level = 0
#     for item in tree:
#         if isinstance(item, (Comment, str)):
#             yield level * tab + item
#         elif isinstance(item, BlankLine):
#             yield ''
#         elif isinstance(item, Command):
#             name = item.name.lower()
#             if name in END_BLOCK_COMMANDS:
#                 level -= 1
#
#             for i, line in enumerate(command_to_lines(item, formatting_opts)):
#                 offset = 1 if i > 0 else 0
#                 line2 = (level + offset) * tab + line
#                 yield line2
#
#             if name in BEGIN_BLOCK_COMMANDS:
#                 level += 1


def is_parameter_name_arg(name):
    return re.match("^[A-Z_]+$", name) and name not in ["ON", "OFF"]


def command_to_lines(cmd, formatting_opts, use_multiple_lines=False):
    class output:
        lines = []
        current_line = cmd.name.lower() + "("
        is_first_in_line = True

    def end_current_line():
        output.lines += [output.current_line]
        output.current_line = ""
        output.is_first_in_line = True

    for arg_index, arg in enumerate(cmd.body):
        # when formatting a command to multiple lines, try to start
        # new lines with parameter names
        #
        #   command(FOO arg
        #     OPTION value
        #     OPTION value)
        if (
            arg_index > 0
            and use_multiple_lines
            and is_parameter_name_arg(arg.contents)
        ):
            end_current_line()

        arg_str = arg_to_str(arg).strip()
        if (
            len(output.current_line) + len(arg_str)
            > formatting_opts.max_line_width
        ):
            if not use_multiple_lines:
                # if the command does not fit on a single line, re-enter the function
                # in multi-line formatting mode so that we can choose the best
                # points to break the line
                return command_to_lines(
                    cmd, formatting_opts, use_multiple_lines=True
                )
            else:
                end_current_line()

        if output.is_first_in_line:
            output.is_first_in_line = False
        else:
            output.current_line += " "

        output.current_line += arg_str
        if len(arg.comments) > 0:
            end_current_line()

    output.current_line += ")"

    if cmd.comment:
        output.current_line += " " + cmd.comment

    end_current_line()

    return output.lines


def arg_to_str(arg):
    comment_part = (
        "  " + "\n".join(arg.comments) + "\n" if arg.comments else ""
    )
    return arg.contents + comment_part


def parse_file(toks):
    """
    Yields line number ranges and top-level elements of the syntax tree for
    a CMakeLists file, given a generator of tokens from the file.

    toks must really be a generator, not a list, for this to work.
    """
    prev_type = "newline"
    for line_num, (typ, tok_contents) in toks:
        if typ == "comment":
            yield [line_num], Comment(tok_contents)
        elif typ == "newline" and prev_type == "newline":
            yield [line_num], BlankLine()
        elif typ == "word":
            line_nums, cmd = parse_command(line_num, tok_contents, toks)
            yield line_nums, cmd
        prev_type = typ


def attach_comments_to_commands(nodes):
    return list_utils.merge_pairs(
        nodes, command_then_comment, attach_comment_to_command
    )


def command_then_comment(a, b):
    line_nums_a, thing_a = a
    line_nums_b, thing_b = b
    return (
        isinstance(thing_a, Command)
        and isinstance(thing_b, Comment)
        and set(line_nums_a).intersection(line_nums_b)
    )


def attach_comment_to_command(lnums_command, lnums_comment):
    command_lines, command = lnums_command
    _, comment = lnums_comment
    return command_lines, Command(command.name, command.body[:], comment)


def parse_command(start_line_num, command_name, toks):
    cmd = Command(name=command_name, body=[], comment=None)
    expect("left paren", toks)
    for line_num, (typ, tok_contents) in toks:
        if typ == "right paren":
            line_nums = range(start_line_num, line_num + 1)
            return line_nums, cmd
        elif typ == "left paren":
            pass
            # raise ValueError('Unexpected left paren at line %s' % line_num)
        elif typ in ("word", "string"):
            cmd.body.append(Arg(tok_contents, []))
        elif typ == "comment":
            c = tok_contents
            if cmd.body:
                cmd.body[-1].comments.append(c)
            else:
                cmd.comments.append(c)
    msg = 'File ended while processing command "%s" started at line %s' % (
        command_name,
        start_line_num,
    )
    raise CMakeParseError(msg)


def expect(expected_type, toks):
    line_num, (typ, tok_contents) = next(toks)
    if typ != expected_type:
        msg = 'Expected a %s, but got "%s" at line %s' % (
            expected_type,
            tok_contents,
            line_num,
        )
        raise CMakeParseError(msg)


# http://stackoverflow.com/questions/691148/pythonic-way-to-implement-a-tokenizer
# TODO: Handle multiline strings.
scanner = re.Scanner(
    [
        (r"#.*", lambda scanner, token: ("comment", token)),
        (r'"[^"]*"', lambda scanner, token: ("string", token)),
        (r"\(", lambda scanner, token: ("left paren", token)),
        (r"\)", lambda scanner, token: ("right paren", token)),
        (r'[^ \t\r\n()#"]+', lambda scanner, token: ("word", token)),
        (r"\n", lambda scanner, token: ("newline", token)),
        (r"\s+", None),  # skip other whitespace
    ]
)


def tokenize(s):
    """
    Yields pairs of the form (line_num, (token_type, token_contents))
    given a string containing the contents of a CMakeLists file.
    """
    toks, remainder = scanner.scan(s)
    line_num = 1
    if remainder != "":
        msg = "Unrecognized tokens at line %s: %s" % (line_num, remainder)
        raise ValueError(msg)
    for tok_type, tok_contents in toks:
        yield line_num, (tok_type, tok_contents.strip())
        line_num += tok_contents.count("\n")
