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
