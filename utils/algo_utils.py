"""Common functions for the algorithms.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.utils.structures import merge_dicts


def init_algos_stats():
    records = {
        "time": 0,
        "operations": 0,
        "per_algo": [],
        "keys": {},
        "levels": [0]
    }
    return records


def record_algos_stats(models, records, algo, cut=None, imb=None, t=None, operations=None, **algopt):
    stats = {
        "algo": algo,
        "cut" : cut,
        "imb" : imb,
        "time": t,
        "operations": operations,
    }
    if t is not None:
        records["time"] += t
    if operations is not None:
        records["operations"] += operations

    records["per_algo"].append(merge_dicts(stats, algopt))


