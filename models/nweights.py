"""Node weights.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import math
import random

from crack.models.weights   import condition_models
from crack.models.geom_fcts import DIST_FCTS


#####################################################
### Format the models for init_NWeights functions ###
#####################################################

def _init_NWeights(init_fct):
    """Decorator that prepares the [models] to the [init_fct].
    """
    def wrapper(models, records, crit=0, key_out="nweights", **kwargs):
        condition_models(init_fct, models, records, crit, key_out, "nweights", **kwargs)
    return wrapper


######################
### Initialization ###
######################

def init_NWeights_from_args(models, records, wgts, key_in=None, key_out="nweights"):
    if isinstance(key_in, str):
        key_in = [key_in]
    nbr_n = len(wgts)
    nbr_c = len(wgts[0])
    models[key_out] = {
        "entity" : "nweights",
        "nbr_n"  : nbr_n,
        "nbr_c"  : nbr_c,
        "weights": wgts,
        "totals" : [sum(w[c] for w in wgts) for c in range(nbr_c)],
        "keys"   : key_in,
    }


@_init_NWeights
def init_NWeights_geometric_lines(models, records, key_in="graph", inf=1, sup=100, npeaks=None, peaks_pos=None, radiuses=None, g=None):
    """Create weights whose heaviest are along geometric lines randomly
    generated.

    The distance is geometric.

    Arguments (all are optional):
        key_in: 'graph'|'mesh'|'hypergraph': Which geometrical data will
            be considered (Default: graph).
        inf: int: Minimum weight (Default: 1).
        sup: sup: Maximum weight (Default: 100).
        npeaks: int: Number of peaks per criterion (Needed if
            [peaks_pos] is not provided).
        peaks_pos: list of list of float: Positions of the peaks.
        radiuses: list of float: Radiuses of the mountains.
    """
    # TODO
    pass


@_init_NWeights
def init_NWeights_geometric_mountains(models, records, key_in="graph", inf=1, sup=100, npeaks=None, peaks_pos=None, radiuses=None, f=None):
    """Create weights whose heaviest are concentrated around some
    random peaks, and decreasing with the distance to the peaks.

    The distance is geometric.

    Arguments (all are optional):
        key_in: str: Key of the geometric entity whose data will
            be considered (Default: 'graph').
        inf: int: Minimum weight (Default: 1).
        sup: sup: Maximum weight (Default: 100).
        npeaks: int: Number of peaks per criterion (Needed if
            [peaks_pos] is not provided).
        peaks_pos: list of list of float: Positions of the peaks.
        radiuses: list of float: Radiuses of the mountains.
        f: function: (Default: x --> x**2)
    """
    dimns = models[key_in]["dimns"]
    nbr_n = models[key_in]["nbr_n"]
    coord = models[key_in]["coord"]
    nwgts = [0] * nbr_n

    dist  = DIST_FCTS[dimns]
    if f is None:
        def f(x): return x**2
    if peaks_pos is None:
        peaks_pos = []
        radiuses  = []
    if npeaks is None:
        npeaks = len(peaks_pos)
    if npeaks > len(peaks_pos):
        limits = []
        mesh_rad = 0
        for d in range(dimns):
            min_c = min(coord[i][d] for i in range(nbr_n))
            max_c = max(coord[i][d] for i in range(nbr_n))
            mesh_rad = max(mesh_rad, max_c - min_c)
            limits.append((min_c, max_c))
        max_rad = mesh_rad / 4.0
        min_rad = mesh_rad / 8.0

    # Find and give new weights to the circles
    for j in range(npeaks):
        # Get next peak
        if j >= len(peaks_pos):
            t = 0
            while t < 10:
                peak   = tuple(random.uniform(limits[d][0], limits[d][1]) for d in range(dimns))
                radius = random.uniform(min_rad, max_rad)
                if not [pt for pt, r in zip(peaks_pos, radiuses) if dist(pt, peak) < r]:
                    break # Peak is not in another circle
                t += 1
            if t == 10:
                continue
            peaks_pos.append(peak)
            radiuses.append(radius)
        else:
            peak   = peaks_pos[-1]
            radius = peaks_pos[-1]
        # Assign weights
        for i, pt in enumerate(coord):
            # Test if the point is in the mountain
            x = dist(pt, peak)
            if x <= radius:
                nwgts[i] += int(sup - (sup - inf) * f(float(x) / radius)) # so that f(0) = sup and f(radius) = inf.
    # Give weights to the rest of the Nodes
    if inf > 0:
        for i in range(nbr_n):
            if nwgts[i] == 0:
                nwgts[i] = inf
    return nwgts


#########################
### Topologic methods ###
#########################

@_init_NWeights
def init_NWeights_random(models, records, key_in=None, nbr_n=None, inf=1, sup=100, **kwargs):
    """Give random weights to every node.

    Keyword Arguments:
        key_in: str: Key of the entity the weights are associated with.
        nbr_n: int: If [key_in] is not provided, must specify the
            number of weights to generate.
        inf: int: Minimum weight of a vertex
        sup: int: Maximum weight of a vertex
    """
    if nbr_n is None:
        nbr_n = models[key_in]["nbr_n"]
    return [random.randint(inf, sup) for _ in range(nbr_n)]


@_init_NWeights
def init_NWeights_topologic_mountains(structs, inf=1, sup=100, npeaks=2):
    """Returns a dict where the weights are concentrated around some
    random peaks, and decreasing from the peak to its neighbors.

    The distance is topologic.

    Arguments:
        structs: dict: The geometry and topology.
        inf: (Optional) int: Minimum weight.
        sup: (Optional) sup: Maximum weight.
        npeaks: (Optional) int: Number of peaks per criteria.
    """
    # TODO
    pass


@_init_NWeights
def init_NWeights_unit(models, records, key_in=None, nbr_n=None):
    """Give a unit weight to every element.

    Options:
        key_in: str: Key of the entity the weights will correspond to.
    """
    if nbr_n is None:
        nbr_n = models[key_in]["nbr_n"]
    return [1] * nbr_n


###############
### Coarsen ###
###############

def coarsen_NWeights(models, records, c_models, key_nweights, aggregation):
    """Returns a tuple of tuple corresponding to the coarsened
    [nweights] according to [aggregation].
    """
    nbr_n_ = len(set(aggregation))
    nbr_c  = models[key_nweights]["nbr_c"]
    nwgts  = models[key_nweights]["weights"]
    nwgts_ = [[0] * nbr_c for _ in range(nbr_n_)]
    for i, i_ in enumerate(aggregation):
        for c in range(nbr_c):
            nwgts_[i_][c] += nwgts[i][c]
    c_models[key_nweights] = {
        "entity" : "nweights",
        "nbr_n"  : nbr_n_,
        "nbr_c"  : nbr_c,
        "weights": nwgts_,
        "totals" : models[key_nweights]["totals"],
        "keys"   : models[key_nweights]["keys"],
    }


####################
### Function IDs ###
####################

INIT_NWGT_FCTS = {
    "init_NWeights_geometric_mountains": init_NWeights_geometric_mountains,
    "init_NWeights_geometric_lines"    : init_NWeights_geometric_lines,
    "init_NWeights_random"             : init_NWeights_random,
    "init_NWeights_topologic_mountains": init_NWeights_topologic_mountains,
    "init_NWeights_unit"               : init_NWeights_unit,
}

