# -*- coding: utf-8 -*-

import re

from natsort import ns, numeric_regex_chooser

int_finder = re.compile(rf"(\D+)({numeric_regex_chooser(ns.INT | ns.SIGNED)})")


def get_int(matchobj):
    return matchobj.group(2)


def ignore_alpha(x):
    return int_finder.sub(get_int, str(x))
