"""Automatically coarsen the models.
"""

__author__ = "Rémi Barat"
__version__ = "1.0"


from time import time

from crack.models.graph           import coarsen_Graph
from crack.models.hypergraph      import coarsen_Hypergraph
from crack.models.mesh            import coarsen_Mesh
from crack.models.eweights        import coarsen_EWeights
from crack.models.hweights        import coarsen_HWeights
from crack.models.nweights        import coarsen_NWeights
from crack.models.partition       import coarsen_Partition
from crack.operators.aggregate    import AGGREGATE_FCTS
from crack.operators.order        import get_order
from crack.operators.restrictions import get_restrict_fct
from crack.utils.errors           import crack_error


def coarsen_models(models, records, aggregation):
    """Return the new coarsened models according to the given
    aggregation.

    Arguments:
        aggregation: list of int: In case i: the new index of vertex i.
    """
    COARSEN_FCTS = {
        "graph"     : coarsen_Graph,
        "hypergraph": coarsen_Hypergraph,
        "mesh"      : coarsen_Mesh,
#        "partition" : coarsen_Partition,
        "nweights"  : coarsen_NWeights,
        "eweights"  : coarsen_EWeights,
        "hweights"  : coarsen_HWeights,
    }
    entities = [ # need to coarsen the topologies before the weights...
        "mesh", "graph", "hypergraph",
        "nweights", "eweights", "hweights"
    ]
    c_models = {
        "key_lead": models["key_lead"]
    }
    for entity in entities:
        for key, model in models.items():
            if isinstance(model, dict) and model.get("entity") == entity:
                COARSEN_FCTS[model["entity"]](
                    models, records, c_models, key, aggregation
                )
    return c_models


def coarsen_one_level(l_models, l_aggr, records, msg=0, **algopt):
    """Coarsens the structures.

    Options:
        "aggregate": dict to specify the aggregation policy:
            "algo": str: Its name. See crack.functions.aggregate
                for the available functions.
            "args": dict: Its arguments. Idem.
        "order": list of dict (Optional): The order to try to
            aggregate the nodes. See crack.functions.order
            for the available functions.
        "restrictions": list of dict (Optional): The
            restrictions.  All restrict functions are
            considered, and as long as one is not respected,
            the aggregation is forbidden.
    """
    ### Variables ###
    models        = l_models[-1]
    key           = algopt.get("key", models["key_lead"])
    aggr_algo     = algopt["aggregate"]["algo"]
    aggr_args     = algopt["aggregate"].get("args", {})
    order_algos   = algopt.get("order", [])
    order_key_in  = algopt.get("order_key", key)
    restrict_spec = algopt.get("restrictions", [])

    start_coarse = time()
    ### Ordering ###
    key_order   = get_order(models, records, order_algos, order_key_in)
    ### Restrictions ###
    allowed     = get_restrict_fct(models, restrict_spec)
    ### Matching ###
    aggregation = AGGREGATE_FCTS[aggr_algo](
        models, records, aggr_args, key_order, allowed
    )
    l_aggr.append(aggregation)
    ### Coarsening ### (This is the most time consuming part.)
    c_models = coarsen_models(models, records, aggregation)
    ### Record and update ###
    level = records["levels"][-1] - 1
    records["levels"].append(level)
    if msg > 0:
        print("  '-> level: {:-3} nbr_n: {} -> {}".format(level, len(aggregation), len(set(aggregation))))
#    if msg:
#        print "    {:3d} - Coarsening: n = {:9}, nrestrict = {:7} (took {:5.3f}s)".format(mdata["level"], c_models[lead]["nbr_n"], data["n_restrict"], time() - start_coarse)
    l_models.append(c_models)


####################
### Function IDs ###
####################

COARSEN_FCTS = {
    "coarsen": coarsen_one_level,
}


