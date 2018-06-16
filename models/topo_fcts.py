"""Common functions associated with topological models (Graph,
Hypergraph).
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.models.geom_fcts import DIST_FCTS


def min_dist_nodes(topo):
    """Compute the minimum distance between neighboring nodes.
    """
    nodes = topo["nodes"]
    nbr_n = topo["nbr_n"]
    coord = topo["coord"]
    dimns = topo["dimns"]
    d_min = min(DIST_FCTS[dimns](coord[i], coord[j]) for i in range(nbr_n) for j in nodes[i][0])
    return d_min


