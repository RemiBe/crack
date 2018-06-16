"""Restrictions on the matching of some vertices together.

These functions arguments need the vertices that are candidate for a
matching together.

They return a function, of argument 2 vertices, returning if
the given vertices can be matched together.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


import random


def get_restrict_fct(models, ralgos):
    """Returns the function that will allow or not the matching
    of vertices. Such a function arguments are an iterable of int,
    and it returns a bool (True if the matching is allowed).

    Arguments:
        ralgos: list of dict: The restriction algorithms. The options
            of each restrict algo are:
            algo: str: Name of the restrict algo.
            args: dict: Options of the restrict algo.
    """
    rfcts = []
    for ralgo in ralgos:
        rfcts.append(RESTRICT_FCTS[ralgo["algo"]](
            models, mdata, ralgo["args"])
        )
    def allowed(nodes):
        # Returns if the matching is possible or not.
        for rfct in rfcts:
            if not rfct(nodes):
                data["nbr_restrict"] += 1
                return False
        return True
    return allowed


def restrict_nweights(models, mdata, algopt):
    """Restrictions based on the nodes weights.

    Arguments:
        mdata: dict: The multilevel data, such as nwgts_unit.
        algopt: dict: Possible options are:
            w_max: float: The threshold. 0 <= [w_max] <= 1.
            forbid:
                "nwgt_above" : Forbid to form a node of weight greater
                    than [w_max]*avg_wgt for one criterion.
                "nwgts_above": Forbid to form a node of weights greater
                    than [w_max]*avg_wgt for all criteria.
                "nwgt_under" : Forbid to form a node of weight smaller
                    than [w_max]*avg_wgt for one criterion.
                "nwgts_under": Forbid to form a node of weights smaller
                    than [w_max]*avg_wgt for all criteria.
            use_nwgts: str or list of str:
                "original": Consider the original node weights.
                "unit": Consider the node weights that were
                    reinitialized at the beginning beginning of the
                    coarsening phase.
    """
    ### Arguments ###
    # - threshold
    if "w_max" not in algopt:
        crack_error(ValueError, "get_restrict_fct",
            "Threshold *w_max* missing for restrict_nwgts."
        )
    w_max = float(a_opts["w_max"])
    # - forbid function
    if "forbid" not in algpot:
        crack_error(ValueError, "get_restrict_fct",
            "What do we *forbid* when restricting nwgts? (nwgt(s)_above/nwgt(s)_under?)"
        )
    forbid = algopt["forbid"]
    # - nwgts
    key_nweights = algopt.get("key_nweights", "nweights")
    nweights = models[key_nweights]
    nbr_n = nweights["nbr_n"]
    nbr_c = nweights["nbr_c"]
    nwgts = nweights["weights"]
    twgts = [w_max * tot for tot in nweights["totals"]]
    if forbid == "nwgt_under":
        def allowed(nodes):
            for c in range(nbr_c):
                if sum(nwgts[n][c] for n in nodes) <= twgts[c]:
                    return True
            return not False
    elif forbid == "nwgts_under":
        def allowed(nodes):
            for c in range(nbr_c):
                if sum(nwgts[n][c] for n in nodes) > twgts[c]:
                    return False
            return not True
    elif forbid == "nwgt_above":
        def allowed(nodes):
            for c in range(nbr_c):
                if sum(nwgts[n][c] for n in nodes) >= twgts[c]:
                    return True
            return not False
    elif forbid == "nwgts_above":
        def allowed(nodes):
            for c in range(nbr_c):
                if sum(nwgts[n][c] for n in nodes) < twgts[c]:
                    return False
            return not True
    else:
        raise ValueError("Unknown matching restriction parameter.")
    return allowed


####################
### Function IDs ###
####################

RESTRICT_FCTS = {
    "nweights": restrict_nweights,
}


