"""A very straightforward partitioning method: attribute a random part
with every node.
"""


__author__ = "Rémi Barat"
__version__ = "1.0"


import random as rd
from   time import time

from crack.models.partition import init_Partition_from_args
from crack.utils.algo_utils import record_algos_stats
from crack.utils.errors     import crack_error


def random_part(models, records, **algopt):
    """Give a random part to every node.

    Arguments:
        nbr_p: Number of parts required.

    Options:
        key_entity_in: str: Key of the entity in [models] that will be 
            partitioned. (Default is 'graph').
        key_entity_out: str: Key to store the Partition in [models].
            (Default is 'partition').
    """
    ### Arguments
    try:
        nbr_p = algopt["nbr_p"]
    except KeyError:
        crack_error(ValueError, "random_part",
            "Missing argument(s): nbr_p")
    ### Options ###
    key_in  = algopt.get("key_entity_in"  , "graph")
    part    = algopt.get("part",       0)
    key_out = algopt.get("key_entity_out" , "partition")
    ### Variables ###
    nbr_n = models[key_in]["nbr_n"]
    ### Partition ###
    start = time()
    parts = [rd.randint(0,nbr_p-1) for _ in range(nbr_n)]
    end   = time()
    init_Partition_from_args(models, {}, key_out, nbr_p, parts)
    ### Record statistics ###
    record_algos_stats(models, records, "random_part", cut=0, imb=None, t=end-start, operations=nbr_n)


