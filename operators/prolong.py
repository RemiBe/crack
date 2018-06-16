"""The function to prolong a coarsened graph to a finer level.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from crack.models.partition import init_Partition_from_args


def prolong_same_part(
    l_models, l_aggr, records, key=None, key_partition="partition",
    msg=0
):
    """Each vertex of the upper level gets the part of the vertex it was
    matched with in the lower level.

    Example:
        3 --+-- 4       level 0
            | aggragation
            v
            2           level -1
        If vertex 2 was assigned part p at level -1, then vertices 3
        and 4 are assigned part p at level 0.
    """
    ### Arguments ###
    aggr = l_aggr.pop()
    c_models = l_models.pop() # Coarsened graph
    c_partition = c_models[key_partition]
    nbr_p    = c_partition["nbr_p"]
    parts    = c_partition["parts"]
    f_models = l_models[-1]   # Finer graph
    if key is None:
        key = f_models["key_lead"]
    nbr_n    = f_models[key]["nbr_n"]

    ### Prolong ###
    parts = [parts[aggr[i]] for i in range(nbr_n)]
    init_Partition_from_args(
        f_models, records,
        key=key_partition, nbr_p=nbr_p, parts=parts
    )
    level = records["levels"].pop()
    if msg > 0:
        print("  '->  level: {:-3} nbr_n: {}".format(level, nbr_n))


PROLONG_FCTS = {
    "prolong_same_part": prolong_same_part,
}


