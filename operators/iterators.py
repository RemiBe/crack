"""Various ways to iterate on Nodes/Edges/Parts.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import itertools as itt
import random    as rd


def update_iter_opts(iter_opts, **kwargs):
    """Set the iterator options.
    """
    for k, v in kwargs.items():
        iter_opts[k] = v


#############
### Nodes ###
#############

def iter_nodes_first_cycle(models, algopt):
    key_topology = algopt["key_topology"]
    nbr_n = models[key_topology]["nbr_n"]
    algopt["restart"] = False
    i = 0
    end = nbr_n-1
    while i != end:
        yield i
        if algopt["restart"]:
            algopt["restart"] = False
            end = i
        i += 1
        if i == nbr_n:
            i = 0


#################
### Partition ###
#################

def iter_parts_first_cycle(models, nbr_p, p_src, algopt):
    p = algopt["last_p_tgt"]
    end = (p - 1) % nbr_p
    while p != end:
        yield p
        p += 1
        if p == nbr_p:
            p = 0


def iter_bipart(models, nbr_p, p_src, algopt):
    yield 1-p_src


####################
### Function IDs ###
####################

ITER_NODES_FCTS = {
    "first_cycle": iter_nodes_first_cycle,
}

ITER_PARTS_FCTS = {
    "bipart"     : iter_bipart,
    "first_cycle": iter_parts_first_cycle,
}


