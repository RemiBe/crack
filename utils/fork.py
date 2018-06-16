"""The fork algorithms: return a bool.
"""


__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.utils.evaluate import eval_expr


def number_of_nodes(l_models, records, phase, expr=None, **algopt):
    """Evaluates the given expression that should compare the number
    of nodes. The keywords are:
    - current : number of nodes at this level
    - finer   : number of nodes at the finer level    (level+1)
    - original: number of nodes of the original graph (level 0)

    Examples of expr:
        - "current <= 120": True when the number of nodes becomes less
          than 120.
        - "current >= 0.9 * finer": True when the number of nodes did
          not decrease more than 10%.
    """
    if expr is None:
        return False
    key = algopt.get("key_in", l_models[0]["key_lead"])
    keywords = {
        "current" : l_models[-1][key]["nbr_n"],
        "original": l_models[ 0][key]["nbr_n"],
    }
    if len(l_models) > 1:
        keywords["finer"] = l_models[-2][key]["nbr_n"]
    return eval_expr(expr, keywords)


_NTRIES__VALID_PARTITION = 1
def valid_partition(models, records, valid=True, ntries_reaches=None, ntries_below=None):
    global _NTRIES__VALID_PARTITION
    nc = models[-1]["c"]
    t  = models[-1]["t"]
    g  = [max(l) for l in gaps(c_structs[-1])]
    if valid:
        res   = (next((c for c in range(nc) if g[c] > t[c]), None) is None)
        retry = not res
    else:
        res   = (next((c for c in range(nc) if g[c] > t[c]), None) is not None)
        retry = res
    if retry:
        if ntries_reaches is not None:
            res = (_NTRIES__VALID_PARTITION == ntries_reaches)
            if res:
                _NTRIES__VALID_PARTITION = 1 # reset counter because the number of maximal tries was exceeded
        if ntries_below is not None:
            res = (_NTRIES__VALID_PARTITION < ntries_below)
            if res:
                _NTRIES__VALID_PARTITION += 1 # try another time
    else:
        _NTRIES__VALID_PARTITION = 1 # reset counter because we found a valid solution
    return res


####################
### Function IDs ###
####################

FORK_FCTS = {
    "number_of_nodes": number_of_nodes,
    "valid_partition": valid_partition,
}
