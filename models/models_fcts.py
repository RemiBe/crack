"""Regroup all the initialization and output functions for the various
structures (Mesh, Graph, Hypergraph, [NE_]Weights, Partition) in a
common dictionary.
"""

__author__ = "Remi Barat"
__version__ = "1.0"


from crack.models.graph      import INIT_GRAPH_FCTS, INIT_GRAPHGEOM_FCTS, OUTPUT_GRAPH_FCTS
from crack.models.hypergraph import INIT_HYPERGRAPH_FCTS
from crack.models.mesh       import INIT_MESH_FCTS
from crack.models.partition  import INIT_PARTITION_FCTS
from crack.models.nweights   import INIT_NWGT_FCTS
from crack.models.eweights   import INIT_EWGT_FCTS

from crack.models.cut       import cut_lambda_minus_one, gain__cut_lambda_minus_one__graph, gain__cut_lambda_minus_one__hypergraph
from crack.models.imbalance import ConstraintsImbalance, imbalance, gain__imbalance

from crack.utils.errors     import crack_error
from crack.utils.structures  import merge_dicts

INIT_FCTS = merge_dicts(
    INIT_GRAPH_FCTS,
    INIT_GRAPHGEOM_FCTS,
    INIT_HYPERGRAPH_FCTS,
    INIT_MESH_FCTS,
    INIT_NWGT_FCTS,
    INIT_EWGT_FCTS,
    INIT_PARTITION_FCTS
)

OUTPUT_FCTS = merge_dicts(
    OUTPUT_GRAPH_FCTS,
)

CONSTRAINTS_OBJ = {
    "imbalance": ConstraintsImbalance,
}


def get_obj_fcts(models, obj_name, obj_args):
    """How to compute the values (e.g. cut, imbalance) that the user
    usually wants to minimize.
    """
    obj_fct = None
    if obj_name == "cut":
        k_topo = obj_args["key_topology" ]
        k_part = obj_args["key_partition"]
        topology  = models[k_topo]
        partition = models[k_part]
        if topology["entity"] == "graph":
            k_ewgts = obj_args["key_eweights"]
            eweights = models[k_ewgts]
            def obj_fct(models, records, stats):
                return cut_lambda_minus_one(
                    models, records,
                    key_topology=k_topo,
                    key_eweights=k_ewgts,
                    key_partition=k_part
                )
            def gain_fct(i, p_src, p_tgt, stats):
                return gain__cut_lambda_minus_one__graph(
                    topology, eweights, partition, i, p_src, p_tgt, stats
                )
        elif topo["entity"] == "hypergraph":
            k_hwgts = obj_args["key_hweights"]
            hwgts = models[k_hwgts]
            def obj_fct(models, records, stats):
                return cut_lambda_minus_one(
                    models, records,
                    key_topology=k_topo,
                    key_eweights=k_hwgts,
                    key_partition=k_part
                )
            def gain_fct(i, p_src, p_tgt, stats):
                return gain__cut_lambda_minus_one__hypergraph(
                    topo, hwgts, parts, i, p_src, p_tgt, stats
                )
    elif obj_name == "imbalance":
        nwgts = models[obj_args["key_nweights"]]
        parts = models[obj_args["key_partition"]]
        def gain_fct(i, p_src, p_tgt):
            return gain__imbalance(nwgts, parts, i, p_tgt, stats)
    if obj_fct is None:
        crack_error(ValueError, "get_gain_fct",
            "Unknown gain function."
        )
    return obj_fct, gain_fct


