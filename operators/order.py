"""Change the order of the vertices/elements based on some criteria.

These functions must return a tuple; thus they can be used in a
chain, acting on the previous order (the last order is the most
essential one, the other being like breaking-ties...).
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import random as rd


def get_order(models, records, algos, key_in="graph"):
    """Apply the different ordering strategies. This function doesn't
    renumber the graph, but returns a new order on the nodes in a dict:

    Returns:
        ordering = {
            "order": tuple of int: In case i: the index of the ith
                vertex that should be called.
            "ordered_nodes_g": tuple of tuple of int:
                               nodes    ngbrs    index
                                        edges    index
            "ordered_nodes_h": tuple of tuple of int:
                               nodes    ngbrs    index
                                        edges    index
                The "graph"/"hypergraph" "nodes" like dict (but it is
                a tuple here: the neighbors/edges of each node are also
                reordered.
        }

    Arguments:
        algos: list of dict: The ordering strategies to apply
            successively. Fields of the dicts are:
            "algo": str: The name of the ordering strategy.
            "args": dict: The options of the ordering strategy.
    """
    key_out = key_in + "__order"
    if not algos:
        models[key_out] = models[key_in]
    else:
        order = None
        for algo in algos:
            order = ORDER_FCTS[algo["algo"]](models, records, algo.get("args", {}), order)
        reorder(models, order, key_in, key_out)
    return key_out


def reorder(models, order, key_in, key_out=None):
    """/!\ Only for nodes.

    Example:
        ngbrs = {
            0: ((1, 2), (0, 1)),
            1: ((0, 4), (0, 2)),
            2: ((0, 5), (1, 3)),
            3: ((4, 5), (4, 5)),
            4: ((1, 3), (2, 4)),
            5: ((2, 3), (3, 5))
        }
        ordr = [1, 4, 3, 2, 0, 5]
        ordered_nodes = {
            0: ((1, 2), (0, 1)),
            1: ((4, 0), (2, 0)), # 4 is before 0 in the order
            2: ((0, 5), (1, 3)),
            3: ((4, 5), (4, 5)),
            4: ((1, 3), (2, 4)),
            5: ((3, 2), (5, 3))  # 3 is before 2 in the order
        }
    """
    if key_out is None:
        key_out = key_in
    nbr_n  = models[key_in]["nbr_n"]
#    nbr_e  = models[key_in]["nbr_e"]
    entity = models[key_in]["entity"]
    nodes  = models[key_in]["nodes"]
#    edges  = models[key_in]["edges"]
    onodes = [ [[], []] for _ in range(nbr_n) ]
#    oedges = [ [] for _ in range(nbr_e) ]
    if entity == "graph":
        for i in order:
            # Add i to the ngbrs list of its neighbors.
            for j, e in zip(nodes[i][0], nodes[i][1]):
                onodes[i][0].append(i)
                onodes[j][1].append(e)
    elif entity == "hypergraph":
        for i in order:
            for j, e in zip(nodes_h[i][0], nodes_h[i][1]):
                onodes[j][0].append(i)
                onodes[j][1].append(e)
    elif entity == "nweights":
        pass # do it if you need it
    models[key_out] = {
        "entity" : "ordered_" + entity,
        "indexes": order,
        "nbr_n"  : nbr_n,
        "nbr_e"  : None,
        "nodes"  : onodes,
        "edges"  : None, # do it if you need it
    }


##########################
### Ordering functions ###
##########################

def get_order_random(models, records, algopt, order, key_in=None, nbr_n=None):
    """Random order on the vertices.
    """
    if order is None:
        if nbr_n is None:
            if key_in is None:
                key_in = models["key_lead"]
            nbr_n = models[key_in]["nbr_n"]
        order = list(range(nbr_n))
    rd.shuffle(order)
    return order


ORDER_FCTS = {
    "random"        : get_order_random,
}


