"""Functions that compute aggregates, which correspond to fuse some
nodes together.

An aggregate is a list: containing in cell i the new index of the ith
element.

A matching is a particular aggregate, in which we can fuse at most
two nodes together.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import random as rd


def match_first(models, records, algopt, key_order, allowed):
    """Match each node with the first unmatched neighbor.
    """
    nbr_n = models[key_order]["nbr_n"]
    nodes = models[key_order]["nodes"]
    order = models[key_order].get("indexes", range(nbr_n))
    matching = [None] * nbr_n
    n_ = 0
    for i, (ngbrs, edges) in zip(order, nodes):
        if matching[i] is None:
            for j in ngbrs:
                if matching[j] is None and allowed((i, j)):
                    matching[j] = n_
                    break
            matching[i] = n_
            n_ += 1
    del models[key_order]
    return matching


def match_hem(structs, mdata, a_opts, ordering, allow_matching):
    """Match each node along its heaviest edge.

    Arguments:
        a_opts: dict: Possible options:
            use_ewgts: "unit" | "original"
    """
    n = structs["n"]
    order = ordering["order"]
    ordered_nodes = ordering["ordered_nodes_g"]
    ewgts = get_eweights(structs, mdata, a_opts)
    matching = {i: None for i in range(n)}
    n_ = 0
    for node in order:
        if matching[node] is None:
            edges = ordered_nodes[node][1]
            e = len(edges)
            edges_order = sorted(range(e), key=lambda i: ewgts[edges[i]], reverse=True)
            for i in edges_order:
                ngbr = ordered_nodes[node][0][i]
                if matching[ngbr] is None and allow_matching((node, ngbr)):
                    matching[ngbr] = n_
                    break
            matching[node] = n_
            n_ += 1
    matching = tuple(matching[i] for i in range(n))
    return matching


def match_random(structs, mdata, a_opts, ordering, allow_matching):
    """Match each node with a random unmatched neighbor.
    """
    n = structs["n"]
    nodes = structs["graph"]["nodes"]
    matching = {i: None for i in range(n)}
    order = range(n)
    rd.shuffle(order)
    n_ = 0
    for node in order:
        if matching[node] is None:
            ngbrs = list(nodes[node][0])
            rd.shuffle(ngbrs)
            ngbr = next((ngbr for ngbr in nodes[node][0] if matching[ngbr] is None), None)
            if ngbr is not None:
                matching[ngbr] = n_
            matching[node] = n_
            n_ += 1
    matching = tuple(matching[i] for i in range(n))
    return matching


####################
### Function IDs ###
####################

AGGREGATE_FCTS = {
    "match_first" : match_first,
    "match_hem"   : match_hem,
    "match_random": match_random,
}

