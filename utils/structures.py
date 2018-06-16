"""Functions that facilitate the manipulations of basic data structures.
"""


__author__ = "Rémi Barat"
__version__ = "1.0"


def merge_dicts(*dicts):
    """Return a dict whose keys are all the keys in the dict given,
    and the values are the value for the last dict given.

    Example:
    >>> merge_dicts(
    ...     {"a": 0, "b": 1},
    ...     {"a": 2, "c": 2}
    ... )
    {"a": 2, "b": 1, "c": 2}
    """
    res = {}
    for d in dicts:
        res.update(d)
    return res


