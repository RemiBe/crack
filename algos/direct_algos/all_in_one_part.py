"""The most straightforward partitioning method: put all the nodes in
the same part.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from   time import time

from crack.utils.algo_utils import record_algos_stats
from crack.models.partition import init_Partition_from_args


def all_in_one_part(models, records, **algopt):
    """Put all the nodes in one part.

    Arguments:
        nbr_p: Number of parts required.

    Options:
        key_entity_in: str: Key of the entity in [models] that will be
            partitioned. (Default is 'graph').
        part: int: Index of the part in which the Nodes will be put.
            (Default is 0).
        key_entity_out: str: Key to store the Partition in [models].
            (Default is 'partition').
    """
    ### Arguments
    try:
        nbr_p = algopt["nbr_p"]
    except KeyError:
        crack_error(ValueError, "all_in_one_part",
            "Missing argument(s):")
    ### Options ###
    key_in  = algopt.get("key_entity_in"  , "graph")
    part    = algopt.get("part",       0)
    key_out = algopt.get("key_entity_out" , "partition")
    ### Variables ###
    nbr_n = models[key_in]["nbr_n"]
    ### Partition ###
    start = time()
    parts = [part] * nbr_n
    end   = time()
    init_Partition_from_args(models, {}, key_out, nbr_p, parts)
    ### Record statistics ###
    record_algos_stats(models, records, "all_in_one_part", cut=0, imb=None, t=end-start, operations=nbr_n)


