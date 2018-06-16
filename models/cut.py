"""Compute the (λ-1) cut of a partition, which is the sum of the
λ-1 cut for every edge/hyperedge. This counts the number of parts
the ends of an edge/hyperedge belong to, minus 1.

An example will be easier to understand:

    A --+-- B
       e|
    D --+-- C

    A, B, C, D are (hypergraph) vertices linked by the hyperedge e.
    Assuming that A and B are in part 0, C in part 1, and D in part 2,
    then the number of parts the ends of e belong to is 3 (this number
    is called λ). And λ-1 = 2 is the number of communications induced
    by the partition for e.


NB: Depending on whether the cut is applied on a graph or a hypergraph,
it will be the classic cut or the lambda-1 cut.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.models.weights import format_crit
from crack.utils.errors   import crack_error


def cut_lambda_minus_one(
    models, records,
    key_topology="graph",
    key_eweights="eweights",
    key_partition="partition",
    weights_crit=0,
):
    """
    """
    topo  = models[key_topology]
    nbr_e = models[key_topology] ["nbr_e"]
    edges = models[key_topology] ["edges"]
    parts = models[key_partition]["parts"]
    wgts  = models[key_eweights] ["weights"]
    crit  = format_crit(weights_crit)
    if len(crit) > 1:
        crack_error(
            ValueError, "cut",
            "Does not handle multiple criteria yet..."
        )
    c = crit[0]
    if topo["entity"] == "graph":
        return sum(
            wgts[e][c] for e, (i, j) in enumerate(edges)
                       if parts[i] != parts[j]
        )
    else:
        return sum(
            wgts[i][c] * len([j for j in ends if parts[j] != parts[i]])
                for i, ends in enumerate(edges)
        )


def gain__cut_lambda_minus_one__graph(graph, eweights, partition, i, p_tgt):
    """

    Arguments:
        cut: float: The current cut.
        i: int: Index of the node moved.
    """
    ngbrs, edges = graph["nodes"][i]
    parts = partition["parts"]
    ewgts = eweights["weights"]
    p_src = parts[i]
    old = sum(ewgts[e][0] for j, e in zip(ngbrs, edges) if parts[j] != p_src)
    new = sum(ewgts[e][0] for j, e in zip(ngbrs, edges) if parts[j] != p_tgt)
    return old - new


def gain__cut_lambda_minus_one__hypergraph(graph, eweights, partition, i, p_src, p_tgt):
    pass # TODO


