"""
"""

__author__ = "Remi Barat"
__version__ = "1.0"


import math
import random

from crack.models.weights import condition_models, format_crit


#####################################################
### Format the models for init_NWeights functions ###
#####################################################

def _init_EWeights(init_fct):
    """Decorator that prepares the [models] to the [init_fct].
    """
    def wrapper(models, records, crit=0, key_out="eweights", **kwargs):
        condition_models(init_fct, models, records, crit, key_out, "eweights", **kwargs)
    return wrapper


######################
### Initialization ###
######################

def init_EWeights_from_args(models, records, wgts, key_in=None, key_out="eweights"):
    if isinstance(key_in, str):
        key_in = [key_in]
    nbr_n = len(wgts)
    nbr_c = len(wgts[0])
    models[key_out] = {
        "entity" : "eweights",
        "nbr_n"  : nbr_n,
        "nbr_c"  : nbr_c,
        "weights": wgts,
        "totals" : [sum(w[c] for w in wgts) for c in range(nbr_c)],
        "keys"   : key_in,
    }


@_init_EWeights
def init_EWeights_from_HWeights(models, records, key_out="eweights", key_graph="graph", key_hypergraph="hypergraph", key_hweights="hweights", f=None, f_args="sum_centers"):
    # Arguments #
    nbr_e  = models[key_graph]["nbr_e"]
    edges  = models[key_graph]["edges"]
    hwgts  = models[key_hweights]["weights"]
    hedges = models[key_hypergraph]["edges"]
    if f is None:
        def f(*hwgts): return sum(hwgt[0] for hwgt in hwgts)
    #############
    if f_args == "sum_centers":
        wgts = [f(hwgts[i], hwgts[j]) for i, j in edges]
    else:
        crack_error(
            ValueError, "init_EWeights_from_HWeights",
            "Unknown 'f_args'. Possible values are: 'sum_centers'."
        )
    return wgts

@_init_EWeights
def init_EWeights_from_NWeights(
    models, records,
    key_out="eweights", key_in="graph",
    key_nweights="nweights", nweights_crit=0,
    f=None, f_args="all_ends",
):
    """Returns Weights based on the weights of the nodes for a
    given criterion.
    """
    nbr_e = models[key_in]["nbr_e"]
    edges = models[key_in]["edges"]
    nwgts = models[key_nweights]["weights"]
    crit  = format_crit(nweights_crit)
    if f is None:
        def f(*nwgts): return sum(nwgt[c] for c in crit for nwgt in nwgts)

    if f_args == "all_ends":
        wgts = [f(*[nwgts[i] for i in edges[e]]) for e in range(nbr_e)]
    else:
        crack_error(
            ValueError, "init_EWeights_from_NWeights",
            "Unknown 'f_args'. Possible values are: 'all_ends'."
        )
    return wgts


@_init_EWeights
def init_EWeights_random(models, records, key_in=None, nbr_e=None, inf=1, sup=100, **kwargs):
    """Generates (uniformly) random eweights.
    """
    if nbr_e is None:
        nbr_e = models[key_in]["nbr_e"]
    return [random.randint(inf, sup) for e in range(nbr_e)]


@_init_EWeights
def init_EWeights_unit(models, records, key_in=None, nbr_e=None):
    """Give a unit weight to every element.

    Options:
        key_in: str: Key of the entity the weights will correspond to.
    """
    if nbr_e is None:
        nbr_e = models[key_in]["nbr_e"]
    return [1] * nbr_e


@_init_EWeights
def init_EWeights_topologic_mountains(structs, inf=1, sup=100, npeaks=2):
    """Some Edges are picked randomly to serve as peaks. The more an
    Edge is close to a peak, the higher is its weight.
    """
    # TODO
    pass


###############
### Coarsen ###
###############

def coarsen_EWeights(models, records, c_models, key_eweights, aggregation):
    """Add the coarsen edge weights to [c_models], under [key_weights].
    """
    nbr_c    = models[key_eweights]["nbr_c"]
    ewgts    = models[key_eweights]["weights"]
    key_in   = models[key_eweights]["keys"]
    key_topo = key_in[0]
    edges    = models[key_topo]["edges"]
    nbr_e_   = c_models[key_topo]["nbr_e"]
    edges_   = c_models[key_topo]["edges"]
    nodes_   = c_models[key_topo]["nodes"]
    ewgts_   = [[0] * nbr_c for _ in range(nbr_e_)]
    tots_    = [0] * nbr_c
    for e, edge in enumerate(edges):
        i = aggregation[edge[0]]
        j = aggregation[edge[1]]
        if i != j:
            e_ = nodes_[i][1][
                next(f for f, j_ in enumerate(nodes_[i][0]) if j_ == j)
            ]
            for c in range(nbr_c):
                ewgts_[e_][c] += ewgts[e][c]
                tots_[c] += ewgts[e][c]
    c_models[key_eweights] = {
        "entity" : "eweights",
        "nbr_n"  : nbr_e_,
        "nbr_c"  : nbr_c,
        "weights": ewgts_,
        "totals" : models[key_eweights]["totals"],
        "keys"   : models[key_eweights]["keys"],
    }


####################
### Function IDs ###
####################

INIT_EWGT_FCTS = {
    "init_EWeights_from_HWeights"      : init_EWeights_from_HWeights,
    "init_EWeights_from_NWeights"      : init_EWeights_from_NWeights,
    "init_EWeights_topologic_mountains": init_EWeights_topologic_mountains,
    "init_EWeights_random"             : init_EWeights_random,
    "init_EWeights_unit"               : init_EWeights_unit,
}


