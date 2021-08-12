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

import random


def file(n=100, pcommand=0.9, k=15):
    '\n'.join(command_or_comment(pcommand, k) for _ in range(n))


def command_or_comment(pcommand, k):
    # TODO: else comment rather than command?
    return command(k) if random.random() < pcommand else command(k)


def command(k):
    args_part = ''.join(intersperse(args(), ['\n', ' ']))
    return ''.join([identifier(k), '(', args_part, ')'])


def intersperse(ls, seps):
    """
    intersperse(ls, seps) puts a separator between each element of
    ls, randomly chosen from seps.
    """
    return [y for x in ls for y in [x, random.choice(seps)]][:-1]

numbers = map(str, range(10))
low_letters = map(chr, range(ord('a'), ord('z') + 1))
high_letters = [c.upper() for c in low_letters]
identifier_chars = numbers + low_letters + high_letters + ['_']


def identifier(k):
    """
    identifier(k) generates an identifier with up to k letters.
    """
    return ''.join(random.choice(identifier_chars)
                   for _ in range(random.randint(1, k+1)))


def args():
    pass
