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


def merge_pairs(list, should_merge, merge):
    """
    Merges adjacent elements of list using the function merge
    if they satisfy the predicate should_merge.

    >>> merge_pairs([], None, None)
    []

    >>> merge_pairs([1], None, None)
    [1]

    >>> merge_pairs([1, 2], lambda x, y: False, None)
    [1, 2]

    >>> merge_pairs([1, 2], lambda x, y: y == x + 1, lambda x, y: (x, y))
    [(1, 2)]

    >>> merge_pairs([1, 2, 3], lambda x, y: y == x + 1, lambda x, y: (x, y))
    [(1, 2), 3]

    >>> merge_pairs([1, 2, 3, 4], lambda x, y: y == x + 1, lambda x, y: (x, y))
    [(1, 2), (3, 4)]
    """
    ret = []
    i = 0
    while i < len(list) - 1:
        a = list[i]
        b = list[i + 1]
        if should_merge(a, b):
            ret.append(merge(a, b))
            i += 2
        else:
            ret.append(a)
            i += 1
    if i == len(list) - 1:
        ret.append(list[i])
    return ret
